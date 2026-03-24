# app_cdn

CloudFront 兼容的 CDN 替换应用，提供 Amazon CloudFront 常用接口的本地实现。

## 架构与分层设计

```
┌─────────────────────────────────────────────────────────────────┐
│  Views (cdn_view.py) - REST API 层                               │
│  - 请求解析、参数校验、HTTP 响应                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  Services (cdn_service.py) - 业务逻辑层                           │
│  - 实现 CdnProviderProtocol，CloudFront 兼容 DTO 转换              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  Repos (distribution_repo, invalidation_repo) - 数据访问层        │
│  - CRUD，无业务逻辑                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  Models (Distribution, Invalidation) - 持久化层                   │
└─────────────────────────────────────────────────────────────────┘
```

- **common/cdn/protocol.py**：CDN 抽象协议，实现可替换（如 boto3 CloudFront 适配器）

## 复用与耦合

- 复用 `common.components.singleton`、`common.utils.http_util`、`common.exceptions`
- 遵循 `config.py` + `get_app_config()` 的配置模式
- 通过 `CdnProviderProtocol` 实现与 CloudFront 的解耦，便于切换实现

## 支持的 API

| 操作 | 方法 | 路径 |
|------|------|------|
| **内容分发（缓存+转发）** | GET | /api/cdn/2020-05-31/d/{distribution_id}/{path} |
| ListDistributions | GET | /api/cdn/2020-05-31/distribution |
| CreateDistribution | POST | /api/cdn/2020-05-31/distribution |
| GetDistribution | GET | /api/cdn/2020-05-31/distribution/{id} |
| DeleteDistribution | DELETE | /api/cdn/2020-05-31/distribution/{id} |
| GetDistributionConfig | GET | /api/cdn/2020-05-31/distribution/{id}/config |
| UpdateDistribution | PUT | /api/cdn/2020-05-31/distribution/{id}/config |
| CreateInvalidation | POST | /api/cdn/2020-05-31/distribution/{id}/invalidation |
| ListInvalidations | GET | /api/cdn/2020-05-31/distribution/{id}/invalidation |
| GetInvalidation | GET | /api/cdn/2020-05-31/distribution/{id}/invalidation/{inv_id} |

## 内容分发（缓存 + 流量转发）

CDN 提供边缘缓存与流量转发：

- **缓存**：内容缓存在 app_oss 的 `CDN_CACHE_BUCKET` 中
- **流量转发**：请求路径 `GET /api/cdn/2020-05-31/d/{distribution_id}/{path}`

流程：优先从缓存读取；未命中则从 Origin 拉取、写入缓存、返回用户。创建 Invalidation 时自动清理对应缓存。

## 配置

环境变量（参见 `.env.example`）：

- `APP_CDN_ENABLED`：是否启用 app_cdn
- `CDN_CACHE_BUCKET`：CDN 缓存桶（存于 app_oss）
- `DB_CDN_*`：CDN 数据库配置

源站 OSS 的 **bucket 名（路径前缀）** 按分发配置：在 `origin_config` 中设置扩展字段 **`OriginBucket`**（与 file-io 的 `AWS_BUCKET` 等对齐），CreateDistribution / UpdateDistribution 可读写。

### URL 结构说明

- **管理 API**（CloudFront 兼容）：`/api/cdn/2020-05-31/` + `distribution` 等（`app_cdn/urls.py` 挂载在 `service_foundation/urls.py` 的 `path('api/cdn/2020-05-31/', ...)`）。
- **内容分发**：`/api/cdn/2020-05-31/d/{distribution_id}/{path}`。
- **CreateDistribution** 须在请求体中传 **`DomainName`**（分发域名，如 `localhost:8000`），不再从环境变量推导。

## 创建 Distribution 示例

```bash
curl -X POST http://localhost:8000/api/cdn/2020-05-31/distribution \
  -H "Content-Type: application/json" \
  -d '{
    "CallerReference": "my-ref-001",
    "DomainName": "localhost:8000",
    "OriginBucket": "default",
    "Origins": {
      "Items": [{
        "Id": "default",
        "DomainName": "localhost:8000",
        "OriginPath": "/api/oss",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only"
        }
      }],
      "Quantity": 1
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "default",
      "ViewerProtocolPolicy": "allow-all"
    },
    "Enabled": true,
    "Comment": "Local CDN"
  }'
```

## 创建 Invalidation 示例

```bash
curl -X POST http://localhost:8000/api/cdn/2020-05-31/distribution/{distribution_id}/invalidation \
  -H "Content-Type: application/json" \
  -d '{
    "InvalidationBatch": {
      "CallerReference": "inv-001",
      "Paths": {
        "Items": ["/path/to/invalidate/*"],
        "Quantity": 1
      }
    }
  }'
```
