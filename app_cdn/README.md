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
- `CDN_BASE_URL`：CDN 基础 URL
- `CDN_DEFAULT_ORIGIN_URL`：默认源站（如 http://localhost:8000/api/oss 或含 bucket 的 http://localhost:8000/api/oss/mybucket）
- `CDN_DEFAULT_ORIGIN_ID`：默认 Origin ID
- `CDN_CACHE_BUCKET`：CDN 缓存桶（存于 app_oss）
- `CDN_ORIGIN_DEFAULT_BUCKET`：源站为 OSS 时的默认 bucket（若 CDN_DEFAULT_ORIGIN_URL 不含 bucket 则必填）
- `DB_CDN_*`：CDN 数据库配置

## 创建 Distribution 示例

```bash
curl -X POST http://localhost:8000/api/cdn/2020-05-31/distribution \
  -H "Content-Type: application/json" \
  -d '{
    "CallerReference": "my-ref-001",
    "Origins": {
      "Items": [{
        "Id": "default",
        "DomainName": "localhost:8000",
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
