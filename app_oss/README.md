# OSS (Object Storage Service)

An object storage service that uses local filesystem storage and provides AWS S3-compatible REST API endpoints.

## Features

1. **Local Storage**: Objects are stored on the local filesystem, with storage path configured via `.env` file
2. **S3-Compatible API**: Provides REST API endpoints that are fully compatible with AWS S3
3. **Unified View**: Uses `S3UnifiedView` to handle all S3 operations, automatically routing based on HTTP method and URL pattern
4. **Object Copying**: Supports S3 CopyObject operation, enabling object duplication via `x-amz-copy-source` header
5. **Metadata Support**: Supports custom metadata through `x-amz-meta-*` headers
6. **Paginated Listing**: Supports ListObjectsV2 API with prefix filtering and pagination

## Configuration

Configure in the `.env` file:

```env
# Specify local storage path (required)
OSS_STORAGE_PATH=/path/to/local/storage
# Optional: default bucket name
OSS_BUCKET_NAME=default-bucket
```

Configuration Notes:
- `OSS_STORAGE_PATH`: Base path for local storage. The directory will be created automatically if it doesn't exist.
- `OSS_BUCKET_NAME`: Optional default bucket name, used when bucket is not specified in certain operations.

## API Endpoints

### S3-Compatible REST API

The service provides AWS S3-compatible REST API endpoints, all accessible through the unified `/api/oss/` path:

#### Upload Object
```
PUT /api/oss/{bucket}/{key}
Content-Type: application/octet-stream
x-amz-meta-{key}: {value}  # Optional: custom metadata

Body: Object data
```

#### Copy Object (S3 CopyObject)
```
PUT /api/oss/{bucket}/{key}
x-amz-copy-source: /{source-bucket}/{source-key}
x-amz-metadata-directive: COPY|REPLACE  # Optional, defaults to COPY
x-amz-meta-{key}: {value}  # Optional: new metadata (only in REPLACE mode)

Body: Empty
```

#### Download Object
```
GET /api/oss/{bucket}/{key}
```

Response Headers:
- `Content-Type`: Object content type
- `Content-Length`: Object size
- `Last-Modified`: Last modification time
- `ETag`: Object ETag (MD5 hash)
- `x-amz-meta-{key}`: Custom metadata

#### Delete Object
```
DELETE /api/oss/{bucket}/{key}
```

Response: 204 No Content

#### Get Object Metadata
```
HEAD /api/oss/{bucket}/{key}
```

Response headers are the same as GET operation, but without response body.

#### List Objects (ListObjectsV2)
```
GET /api/oss/{bucket}?list-type=2&prefix={prefix}&max-keys={max_keys}&continuation-token={token}
```

Query Parameters:
- `list-type`: Must be `2` (only ListObjectsV2 is supported)
- `prefix`: Optional, object key prefix filter
- `max-keys`: Optional, maximum number of objects to return (default: 1000)
- `continuation-token`: Optional, continuation token for pagination

Response: XML-formatted ListBucketResult

## Usage Examples

### Using boto3 Client

```python
import boto3

# Configure client to point to local service
s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:8000/api/oss',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy',
    region_name='us-east-1'
)

# Upload object
s3_client.put_object(
    Bucket='my-bucket',
    Key='my-object-key',
    Body=b'Hello, World!',
    Metadata={'custom-key': 'custom-value'}  # Custom metadata
)

# Copy object
s3_client.copy_object(
    CopySource={'Bucket': 'my-bucket', 'Key': 'my-object-key'},
    Bucket='my-bucket',
    Key='my-object-key-copy',
    MetadataDirective='COPY'  # or 'REPLACE'
)

# Download object
response = s3_client.get_object(
    Bucket='my-bucket',
    Key='my-object-key'
)
data = response['Body'].read()
metadata = response.get('Metadata', {})

# Get object metadata
response = s3_client.head_object(
    Bucket='my-bucket',
    Key='my-object-key'
)
content_type = response['ContentType']
content_length = response['ContentLength']

# List objects
response = s3_client.list_objects_v2(
    Bucket='my-bucket',
    Prefix='my-prefix',
    MaxKeys=100
)
for obj in response.get('Contents', []):
    print(f"Key: {obj['Key']}, Size: {obj['Size']}")

# Delete object
s3_client.delete_object(
    Bucket='my-bucket',
    Key='my-object-key'
)
```

### Using HTTP Requests

```bash
# Upload object
curl -X PUT http://localhost:8000/api/oss/my-bucket/my-key \
  -H "Content-Type: text/plain" \
  -H "x-amz-meta-author: John Doe" \
  --data-binary "Hello, World!"

# Copy object
curl -X PUT http://localhost:8000/api/oss/my-bucket/my-key-copy \
  -H "x-amz-copy-source: /my-bucket/my-key" \
  -H "x-amz-metadata-directive: COPY"

# Download object
curl http://localhost:8000/api/oss/my-bucket/my-key

# Get metadata
curl -I http://localhost:8000/api/oss/my-bucket/my-key

# List objects
curl "http://localhost:8000/api/oss/my-bucket?list-type=2&prefix=my-&max-keys=10"

# Delete object
curl -X DELETE http://localhost:8000/api/oss/my-bucket/my-key
```

## Storage Structure

Objects are stored in the following structure:

```
{OSS_STORAGE_PATH}/
  {bucket_name}/
    {object_key}
    {object_key}.metadata
```

Example:
```
/storage/
  my-bucket/
    files/
      document.pdf
      document.pdf.metadata
    images/
      photo.jpg
      photo.jpg.metadata
```

The metadata file (`.metadata`) contains object metadata information stored in JSON format:
- `ContentType`: Content type
- `ContentLength`: Content length
- `LastModified`: Last modification time (ISO format)
- `ETag`: MD5 hash value
- `Metadata`: User-defined metadata dictionary
- `Size`: File size

## Architecture

### Core Components

1. **OSSClient**: Singleton-pattern client wrapper responsible for initializing the local storage service
2. **LocalStorageService**: Local filesystem storage service implementation providing S3-compatible method interfaces
3. **S3UnifiedView**: Unified view class that routes to appropriate handler views based on HTTP method and URL pattern
4. **S3CompatibleView**: Contains individual S3 operation view classes (PUT/GET/DELETE/HEAD/List)

### Workflow

1. Request arrives at `S3UnifiedView`
2. Routes to appropriate view based on URL pattern (presence of `key` parameter) and method type
3. View obtains `LocalStorageService` instance through `OSSClient`
4. Executes corresponding storage operation (upload/download/delete/list, etc.)
5. Returns S3-compatible response format

## Notes

1. **Local Storage Path**: Ensure the path specified by `OSS_STORAGE_PATH` exists and has write permissions. The system will automatically create the directory if it doesn't exist.
2. **Bucket Names**: Bucket names correspond to directory names in the local filesystem, supporting nested object keys (paths).
3. **Presigned URLs**: Local storage does not support presigned URLs. Related operations will raise configuration error exceptions.
4. **ETag Calculation**: Uses MD5 hash algorithm to calculate object ETag, consistent with AWS S3 behavior.
5. **Metadata Storage**: Custom metadata is stored in separate `.metadata` JSON files and does not affect the object file itself.
6. **Pagination Support**: ListObjectsV2 supports pagination using simple index as continuation token.
7. **Error Handling**: Follows S3 API error response format, returning appropriate HTTP status codes and error messages.
