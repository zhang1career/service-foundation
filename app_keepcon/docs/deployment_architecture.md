# app_keepcon 部署架构（PlantUML）

**分阶段**：**首阶段仅 WebSocket 路径**（终端 → TLS 接入 → Channels Worker → Redis → MySQL）。图中 **MQTT Broker与网关为第二阶段**，与 WS 共用 Redis 信封与 `sf_keepcon`；实现首版时可忽略 MQTT 节点或视为规划态。

下文为 PlantUML 源码。可：

- 复制到独立文件 `deployment_architecture.puml` 后用 [PlantUML](https://plantuml.com/) CLI / IDE 插件渲染；
- 或在本仓库用支持 `plantuml` 代码块的预览插件直接渲染本文件。

---

## 主图：设备、服务、WebSocket与 MQTT 网关

```plantuml
@startuml app_keepcon_deployment
!theme plain
title app_keepcon — 部署架构（设备、服务、WebSocket / MQTT 网关）

skinparam backgroundColor #FEFEFE
skinparam shadowing false
skinparam roundCorner 8
skinparam ArrowColor #333333
skinparam defaultFontName sans-serif

legend right
  |= 图例 |
  | 实线 | 生产流量主路径 |
  | 虚线 | 管理面 / 可选 / 未来演进 |
end legend

package "终端与设备" as clients {
  rectangle "手机 / 平板 App\n(WebSocket + TLS)" as dev_mobile
  rectangle "浏览器 H5\n(WebSocket + TLS)" as dev_web
  rectangle "物联网设备\n(WebSocket + TLS)" as dev_iot_ws
  rectangle "物联网设备\n(MQTT 3.1.1 / 5)" as dev_iot_mqtt
}

cloud "接入层" as edge {
  rectangle "TLS终止 / 七层负载均衡\n(Nginx / Envoy / CLB)" as lb
  rectangle "可选：WAF / 限流" as waf
}

package "长连接与实时平面" as realtime {
  rectangle "ASGI / Django Channels\nWebSocket Worker 池" as ws_pool
  rectangle "Redis\n(Channels layer +\ndevice→node 路由 Pub/Sub)" as redis_rt
  together {
    rectangle "MQTT Broker\n(如 EMQX / Mosquitto 集群)" as mqtt_broker
    rectangle "MQTT 网关 / 桥接\n(app_keepcon)\nTopic ↔ device_id / 内部信封" as mqtt_gw
  }
 rectangle "可选：native 侧车\n(未来 C keepcond)\n仅接管 WS 帧与扇出" as native_sidecar <<optional>>
}

package "业务与控制平面" as control {
  rectangle "Django WSGI / HTTP\nREST API、控制台" as django_http
  rectangle "app_keepcon\n领域服务\n(设备、消息、投递状态)" as keepcon_svc
}

database "MySQL\n**sf_keepcon**\n设备、消息、幂等等" as mysql_sf

package "内部调用方" as internal {
  rectangle "其它微服务 / 任务\n(HTTP 内部 API 投递消息)" as producers
}

' --- 客户端 → 边缘
dev_mobile -down-> lb : WSS
dev_web -down-> lb : WSS
dev_iot_ws -down-> lb : WSS
lb -down-> waf : (可选)

' --- WebSocket 路径
waf -down-> ws_pool : 反向代理\nUpgrade: websocket
ws_pool -down-> redis_rt : 订阅/发布\n跨节点投递
ws_pool -down-> keepcon_svc : 鉴权后注册会话\n(或经 Redis 异步)
keepcon_svc -down-> mysql_sf : 读写字段\n消息状态

' --- MQTT 路径
dev_iot_mqtt -down-> mqtt_broker : MQTT over TLS\n(或设备侧明文+专线)
mqtt_broker -down-> mqtt_gw : 规则引擎 /\n共享订阅 / webhook
mqtt_gw -down-> redis_rt : 与 WS 平面\n统一信封
mqtt_gw -down-> keepcon_svc : 持久化 /\n状态机
mqtt_gw -up-> mqtt_broker : 下行发布\n(按 topic / client)

' --- HTTP / 管理
producers -right-> django_http : HTTPS\n内部网络
django_http -down-> keepcon_svc
django_http -up-> mysql_sf

' --- 未来演进（虚线）
native_sidecar ..> ws_pool : 可替换\n部分 Worker
native_sidecar ..> redis_rt
keepcon_svc ..> native_sidecar : 同一 Redis /\nDB 契约

note bottom of ws_pool
  **WebSocket 应用协议（建议）**
  • 握手后首帧或子协议：鉴权 token / device_id
  • 帧类型：hello、ping/pong、push、ack、sync（since_seq）
  • 载荷：版本化 JSON 或 MessagePack；业务 body 与信令分离
  • 离线消息：仅写 MySQL；上线 sync 或连接建立后补发
end note

note bottom of mqtt_gw
  **MQTT 网关职责**
  • 维护 clientId / 证书与 keepcon **device_id** 映射（表或缓存）
  • 上行：MQTT publish → 规范化 **内部消息信封** → Redis + MySQL
  • 下行：内部待投递 → 映射 topic QoS → Broker publish
  • ACL：按租户/设备限制 pub/sub；禁止与 pickle 等不可移植格式
end note

@enduml
```

---

## 网络分区与信任边界

```plantuml
@startuml app_keepcon_network_zones
!theme plain
title app_keepcon — 网络分区与信任边界（示意）

skinparam rectangle {
  roundCorner 8
}

rectangle "公网 / 设备网" as untrusted #FFE4E1
rectangle "DMZ — 接入" as dmz #FFF8DC
rectangle "应用网 — 服务" as appnet #E8F4E8
rectangle "数据网" as datanet #E8EEF8

untrusted -down-> dmz : **仅 TLS**\n443 / 8883(MQTT)
dmz -down-> appnet : 内网 LB →\nWS / HTTP / MQTT 桥
appnet -down-> datanet : MySQL / Redis\n凭证轮换、最小权限

note right of dmz
  • 边缘完成 TLS、证书、部分限流
  • WebSocket 与 MQTT 监听可拆分不同 VIP
end note

note right of appnet
  • Django / Channels / MQTT 网关同集群或分池部署
  • Redis 仅内网；禁公网暴露
end note

@enduml
```

---

## 水平扩展要点

```plantuml
@startuml app_keepcon_scale_out
!theme plain
title app_keepcon — 水平扩展要点（多副本）

collections "WS Worker\n实例 N个" as wsN
collections "WS Worker\n实例 M个" as wsM
queue "Redis" as r
database "MySQL\nsf_keepcon" as db

wsN -down-> r : 订阅 device:{id} /\n节点心跳
wsM -down-> r
wsN -down-> db
wsM -down-> db

note bottom of r
  **禁止** 仅在单机内存维护「设备→连接」
  全局路由需 Redis（或等价）+ TTL；
  投递：写库后 Pub 到目标 device 或 node 分片
end note

@enduml
```
