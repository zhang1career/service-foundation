# Service Foundation Docker 部署指南

本文档介绍如何使用Docker部署Service Foundation应用，支持gray和prod环境，并允许外部配置MySQL连接信息。

## 目录结构

```
.
├── Dockerfile                   # Docker镜像构建文件
├── docker-compose.yml           # 部署配置
├── docker-build.sh              # 构建脚本
└── DOCKER_README.md             # 本文档
```

## 快速开始

### 1. 构建Docker镜像

首先确保项目已构建：

```bash
# 构建应用
mvn clean package -DskipTests

# 构建Docker镜像
./docker-build.sh

# 或指定版本号
./docker-build.sh v1.0.0

# 启动
dcup
```
