# Service Foundation Docker 部署指南

本文档介绍如何使用Docker部署Service Foundation应用（Python 3.12 + Django 4.1），支持test和prod环境，并允许外部配置MySQL连接信息。

## 架构说明

本Docker配置使用Django内置的开发服务器（`runserver`）运行应用。负载均衡、健康检查、限流和熔断等功能由外部网关处理。这种架构适合：
- 已有外部网关/API网关（如Kong、Nginx、Envoy等）
- 网关负责负载均衡、探活、限流和熔断
- 容器内只需运行单个Django实例

## 目录结构

```
.
├── Dockerfile                   # Docker镜像构建文件
├── docker-compose.yml           # 部署配置
├── docker-build.sh              # 构建脚本
├── docker-entrypoint.sh         # 容器启动脚本
├── requirements.txt             # Python依赖
├── manage.py                    # Django管理脚本
└── DOCKER_README.md             # 本文档
```

## 快速开始

### 1. 前置要求

- Docker 和 Docker Compose 已安装
- 确保项目根目录存在 `requirements.txt` 和 `manage.py`

### 2. 构建Docker镜像

```bash
# 构建Docker镜像
./docker-build.sh

# 或指定版本号
./docker-build.sh v1.0.0
```

### 3. 启动服务

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f service_foundation

# 停止服务
docker-compose down
```

### 4. 环境配置

#### 环境变量

可以通过 `docker-compose.yml` 中的 `environment` 部分配置环境变量，或者创建 `.env.prod` 文件：

```bash
# .env.prod 示例
ENVIRONMENT=prod
DEBUG=False
DB_DEFAULT_HOST=mysql
DB_DEFAULT_NAME=service_foundation
DB_DEFAULT_USER=zhang
DB_DEFAULT_PASS=123456
DB_DEFAULT_PORT=3306
```

#### 数据库配置

数据库配置通过 `.env.prod` 文件或环境变量设置。确保在 `docker/.env.prod` 文件中配置正确的数据库连接信息。

#### Django服务器配置

容器内使用Django的开发服务器运行，可通过环境变量配置：
- `HOST`: 监听地址（默认：0.0.0.0）
- `PORT`: 监听端口（默认：8000）

**注意**：Django开发服务器是单线程的，适合配合外部网关使用。外部网关负责：
- 负载均衡：将请求分发到多个容器实例
- 健康检查：定期检查容器健康状态
- 限流：控制请求速率
- 熔断：在服务异常时快速失败

#### 邮件服务器配置（SMTP/IMAP）

容器会在后台自动启动邮件服务器（SMTP 和 IMAP），可通过环境变量配置：

**邮件服务器环境变量**：
- `START_MAIL_SERVER`: 是否启动邮件服务器（默认：`true`，设置为 `false` 可禁用）
- `MAIL_SMTP_PORT`: SMTP 服务器端口（默认：25，用于接收邮件）
- `MAIL_IMAP_PORT`: IMAP 服务器端口（默认：143，用于访问邮件）
- `MAIL_SERVER_HOST`: 邮件服务器绑定地址（默认：0.0.0.0）
- `MAIL_OSS_BUCKET`: OSS 存储桶名称，用于存储邮件附件（默认：mail-attachments）
- `MAIL_OSS_ENDPOINT`: OSS 端点 URL（默认：http://localhost:8000/api/oss）

**端口说明**：
- 端口 25（SMTP）和 143（IMAP）是标准邮件协议端口，在 Linux 系统中属于特权端口（< 1024）
- Docker 配置中已添加 `cap_add: NET_BIND_SERVICE` 权限，允许容器绑定这些端口
- 如果遇到权限问题，可以考虑使用非特权端口（如 1025、1143），并通过端口映射到主机的标准端口

**使用非特权端口的配置示例**：
```yaml
environment:
  MAIL_SMTP_PORT: 1025  # 容器内使用非特权端口
  MAIL_IMAP_PORT: 1143
ports:
  - "25:1025"  # 映射到主机标准端口
  - "143:1143"
```

**邮件服务器日志**：
- 邮件服务器的日志会输出到 `${LOG_DIR}/mail_server.log`
- 可以通过 `docker-compose logs -f service_foundation` 查看所有服务日志
- 单独查看邮件服务器日志：`docker-compose exec service_foundation tail -f /var/log/service_foundation/mail_server.log`

### 5. 访问应用

应用启动后，可以通过以下地址访问：

**Web API**：
- 应用地址：http://localhost:8000（直接访问容器）
- 或通过外部网关访问（推荐）

**邮件服务器**：
- SMTP 服务器：`localhost:25`（接收邮件）
- IMAP 服务器：`localhost:143`（访问邮件）
- 可以通过邮件客户端（如 Thunderbird、Outlook）连接这些服务

**网关配置建议**：
- 将网关的upstream指向容器的8000端口
- 配置健康检查端点（如 `/` 或自定义健康检查路径）
- 根据实际负载配置限流和熔断策略

**邮件服务器连接示例**：
- SMTP 配置（接收邮件）：服务器 `localhost`，端口 `25`，无需认证（收件）
- IMAP 配置（访问邮件）：服务器 `localhost`，端口 `143`，使用邮箱账户用户名和密码登录

### 6. 常用操作

```bash
# 查看运行状态
docker-compose ps

# 查看应用日志
docker-compose logs -f service_foundation

# 进入容器
docker-compose exec service_foundation bash

# 执行Django管理命令
docker-compose exec service_foundation python manage.py migrate
docker-compose exec service_foundation python manage.py createsuperuser
docker-compose exec service_foundation python manage.py collectstatic

# 邮件服务器管理命令（如果需要在容器内手动启动）
docker-compose exec service_foundation python manage.py start_mail_server
docker-compose exec service_foundation python manage.py start_mail_server --smtp-only  # 仅启动 SMTP
docker-compose exec service_foundation python manage.py start_mail_server --imap-only  # 仅启动 IMAP

# 查看邮件服务器日志
docker-compose exec service_foundation tail -f /var/log/service_foundation/mail_server.log

# 重启服务
docker-compose restart service_foundation

# 停止并删除容器（保留数据卷）
docker-compose down

# 停止并删除容器和数据卷
docker-compose down -v
```

### 7. 生产环境注意事项

1. **安全配置**：
   - 修改默认的 `SECRET_KEY`
   - 设置 `DEBUG=False`
   - 配置 `ALLOWED_HOSTS`

2. **数据库**：
   - 确保数据库配置正确（通过 `.env.prod` 文件）
   - 确保数据库已创建并运行迁移

3. **静态文件**：
   - 静态文件会在容器启动时自动收集
   - 生产环境建议通过外部网关/Nginx提供静态文件服务

4. **网关配置**：
   - 确保外部网关正确配置了upstream指向容器
   - 配置合适的健康检查间隔和超时时间
   - 根据业务需求配置限流和熔断策略

5. **日志**：
   - Django的日志会输出到stdout/stderr，可通过 `docker-compose logs` 查看
   - 日志目录 `./docker/log/` 用于其他日志文件

6. **网络**：
   - 确保容器能够访问外部MySQL数据库
   - 确保外部网关能够访问容器

7. **首次启动**：
   - 首次启动时，容器会自动运行数据库迁移
   - 如果需要创建超级用户，使用：`docker-compose exec service_foundation python manage.py createsuperuser`

8. **性能考虑**：
   - Django开发服务器是单线程的，不适合高并发场景
   - 通过外部网关的负载均衡，可以启动多个容器实例来提升性能
   - 如果需要更高性能，可以考虑使用Gunicorn（需要修改 `docker-entrypoint.sh`）

9. **邮件服务器注意事项**：
   - 邮件服务器（SMTP/IMAP）在容器启动时自动后台运行
   - 邮件服务器的生命周期与主容器绑定，容器停止时邮件服务器也会停止
   - 如果需要单独管理邮件服务器，可以设置 `START_MAIL_SERVER=false`，然后手动启动
   - 生产环境建议配置 TLS/SSL 加密（当前版本未实现，需要额外配置）
   - 端口 25 和 143 可能需要防火墙配置才能从外部访问
   - 邮件附件存储在 OSS（Object Storage Service）中，确保 OSS 配置正确
