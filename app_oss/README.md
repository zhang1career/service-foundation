# OSS (Object Storage Service)

这是一个对象存储服务，使用本地存储并提供 AWS S3 兼容的 API。

## 功能特性

1. **本地存储**：对象存储在本地文件系统，通过 `.env` 文件配置存储路径
2. **S3 兼容 API**：提供与 AWS S3 一致的 REST API 接口

## 配置

在 `.env` 文件中配置：

```env
# 指定本地存储路径（必需）
OSS_STORAGE_PATH=/path/to/local/storage
# 可选：默认 bucket 名称
OSS_BUCKET_NAME=default-bucket
```

## API 端点

### S3 兼容的 REST API

服务提供与 AWS S3 兼容的 REST API：

#### 上传对象
```
PUT /api/oss/{bucket}/{key}
Content-Type: application/octet-stream

Body: 对象数据
```

#### 下载对象
```
GET /api/oss/{bucket}/{key}
```

#### 删除对象
```
DELETE /api/oss/{bucket}/{key}
```

#### 获取对象元数据
```
HEAD /api/oss/{bucket}/{key}
```

#### 列出对象
```
GET /api/oss/{bucket}?list-type=2&prefix={prefix}&max-keys={max_keys}
```

## 使用示例

### 使用 boto3 客户端

```python
import boto3

# 配置客户端指向本地服务
s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:8000/api/oss',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy',
    region_name='us-east-1'
)

# 上传对象
s3_client.put_object(
    Bucket='my-bucket',
    Key='my-object-key',
    Body=b'Hello, World!'
)

# 下载对象
response = s3_client.get_object(
    Bucket='my-bucket',
    Key='my-object-key'
)
data = response['Body'].read()

# 列出对象
response = s3_client.list_objects_v2(
    Bucket='my-bucket',
    Prefix='my-prefix'
)
```

## 存储结构

对象存储在以下结构中：

```
{OSS_STORAGE_PATH}/
  {bucket_name}/
    {object_key}
    {object_key}.metadata
```

例如：
```
/storage/
  my-bucket/
    files/
      document.pdf
      document.pdf.metadata
```

元数据文件（`.metadata`）包含对象的元信息，如内容类型、大小、ETag 等。

## 注意事项

1. **本地存储路径**：确保 `OSS_STORAGE_PATH` 指定的路径存在且有写权限
2. **Bucket 名称**：bucket 名称对应本地文件系统中的目录名
3. **Presigned URL**：本地存储不支持 presigned URL，会抛出配置错误异常

