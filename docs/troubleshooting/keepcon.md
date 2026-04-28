# app_keepcon WebSocket 排查步骤

适用于现象：**WebSocket 握手成功**（如 `Sec-WebSocket-Accept`、`server: uvicorn`），但客户端 **收不到任何下行 JSON**（websocat 出现 `incoming None`、无 `hello_ok` / `hello_fail`）。

按 **从外到内、从易到难** 依次进行。

---

## 1. 确认客户端发出的是「文本 JSON hello」

- 使用 **`websocat -t -v`**，或交互连接后 **整行粘贴** 一条：`{"type":"hello","device_key":"...","secret":"..."}`。
- 也可用 **Python `websockets`**：`ws.send(json.dumps({...}))`，确保为 **text** 帧。
- **原因**：服务端 `KeepconConsumer.receive` 仅处理 `text_data`；若为 **binary** 帧会 **静默忽略**，无回包亦无应用日志。

---

## 2. 确认同机 HTTP 应用可用

- 请求 **`GET /api/keepcon/health`**（按实际协议与端口，如 `http(s)://host:port/api/keepcon/health`），应返回正常业务包络。
- **目的**：确认 ASGI/Django、路由与监听端口一致；HTTP 都不通时先排查进程、防火墙、反代。

---

## 3. 查看 Uvicorn（或等价 ASGI 服务）实时日志

- 与重试 `hello` **同一时刻**，查看 stderr/日志文件是否出现 **traceback**、**Redis**、**MySQL**、**Channels** 相关错误。
- **原因**：`hello` 成功后仍会执行 `channel_layer.group_add` 等步骤；若此处抛错，可能出现 **连接异常结束、客户端无任何 JSON**。

---

## 4. 核对环境与依赖配置

- **`APP_KEEPCON_ENABLED=true`**。
- **MySQL（keepcon_rw）**：可达；`KeepconDevice` 中存在对应 **`device_key` + `secret`**，且 **`status` 为启用**，与 `authenticate_device` 过滤一致。
- **Redis**：与 **`CHANNEL_Layers` / Channels** 配置一致；可 `PING`，且 **库号、KEY 前缀** 与 `settings` 一致。
- **说明**：纯鉴权失败本应返回 **`hello_fail`** JSON；若失败发生在 **鉴权之后又未成功 `send`**（例如 Redis 异常），则可能表现为 **无下行帧**。

---

## 5. 排除反向代理 / 负载均衡

- **Nginx / SLB** 需正确传递 **`Upgrade`、`Connection`**，并合理设置 **`proxy_read_timeout` / `proxy_send_timeout`**；避免健康检查或短超时 **误断长连接**。
- 条件允许时 **绕过反代直连应用端口** 复现一次，区分是 **应用层** 还是 **入口层** 问题。

---

## 6. 界定网络与协议层（可选）

- 客户端 **`websocat -vv`**：除握手外是否曾出现 **入站 WebSocket 数据**。
- 服务端有权限时对应用端口 **抓包**：首条业务数据后是否出现 **FIN/RST**，辅助判断 **对端未发** 与 **链路被重置**。

---

## 7. 仍无头绪时：短时增加观测（发布后应移除或降级）

- 在 `KeepconConsumer` 的 **`connect` / `receive` / `_handle_hello`**（或外层）增加 **短时、结构化日志**（注意脱敏，勿长期打印 `secret`）。
- **目的**：确认 **WebSocket 帧是否进入 Consumer**；仅限排障窗口使用。

---

## 8. 其他

- 多实例前的 **四层/七层负载** 一般不单独要求会话粘滞 WebSocket **单连接**，但若配置了非常规路由，仍可对照厂商文档复核。
- 边缘 **TLS** 与证书、时钟等问题通常表现为握手失败而非「握手成功后无帧」；若以 **wss** 访问仍异常，再结合证书链与 SNI 排查。

---

## 建议顺序

优先 **健康检查（上文第 2 步）+ 实时日志（第 3 步，与重试同一时刻）** 与 **环境与依赖（第 4 步）**；仍不明确再做 **反代与LB（第 5 步）、抓包（第 6 步）**；最后按需 **短时观测（第 7 步）**。
