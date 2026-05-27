# Service Foundation

统一的 SaaS 基础服务平台（Django），通过模块开关组合出不同业务场景的后端底座。

## 核心能力

- 用户中心：注册、登录、JWT、用户资料
- 对象存储：S3 兼容 API（上传、下载、复制、元数据、分页列表）
- 发号服务：Snowflake ID（业务位段、时钟回拨保护）
- 分布式事务：TCC 协调器、Saga 协调器
- 内容与配置：Headless CMS、配置中心
- 通知与连接：通知中心、验证码、Keepcon 长连接、邮件服务
- 运维：`/console/` 控制台

## API 前缀

- `/api/user/`
- `/api/oss/`
- `/api/snowflake/`
- `/api/tcc/`
- `/api/saga/`
- `/api/cms/`
- `/api/config/`
- `/api/notice/`
- `/api/keepcon/`

实际可用路由取决于 `.env` 中的 `APP_*_ENABLED` 开关。

## 快速启动

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
./run.sh start
```

常用命令：

```bash
./run.sh start
./run.sh stop
./run.sh restart
./run.sh status
```

## 事务编排说明

- TCC `POST /api/tcc/tx` 通过 `branches[].branch_code` 指定参与方。
- Try 按 `branch_index` 正序执行，Confirm/Cancel 按逆序回放。
- Saga `POST /api/saga/instances` 支持 `step_payloads` 与失败补偿。
