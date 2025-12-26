# Service Foundation Docker 部署指南

本文档介绍如何使用Docker部署Service Foundation应用（Python 3.12 + Django 4.1），支持test和prod环境，并允许外部配置MySQL连接信息。

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
# 启动所有服务（包括MySQL）
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

**使用内置MySQL（默认）**：
- MySQL 5.7（兼容Django 4.1）
- 数据库名：`service_foundation`
- 用户名：`zhang`
- 密码：`123456`
- 端口：`3306`

**使用外部MySQL**：
如果已有MySQL服务，可以：
1. 在 `docker-compose.yml` 中注释掉 `mysql` 服务
2. 修改环境变量中的 `DB_DEFAULT_HOST` 和 `DB_SNOWFLAKE_HOST` 为外部MySQL地址
3. 确保外部MySQL已创建相应的数据库

#### Gunicorn配置

可以通过环境变量调整Gunicorn参数：
- `GUNICORN_WORKERS`: worker进程数（默认：4）
- `GUNICORN_THREADS`: 每个worker的线程数（默认：2）
- `GUNICORN_TIMEOUT`: 超时时间（默认：30秒）

### 5. 访问应用

应用启动后，可以通过以下地址访问：
- 应用地址：http://localhost:10000
- MySQL端口：localhost:3306

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
   - 使用外部MySQL数据库时，修改 `DB_DEFAULT_HOST` 和 `DB_SNOWFLAKE_HOST`
   - 确保数据库已创建并运行迁移

3. **静态文件**：
   - 生产环境建议使用Nginx等反向代理服务器
   - 或配置Django的静态文件服务

4. **日志**：
   - 日志文件位于 `./docker/log/` 目录
   - 可通过 `docker-compose.yml` 中的 `volumes` 配置持久化

5. **网络**：
   - 如果使用内置MySQL，可以移除 `networks` 配置或创建新的网络
   - 如果使用外部MySQL，确保网络配置正确，或移除 `depends_on` 和网络配置

6. **首次启动**：
   - 首次启动时，容器会自动运行数据库迁移
   - 如果需要创建超级用户，使用：`docker-compose exec service_foundation python manage.py createsuperuser`
