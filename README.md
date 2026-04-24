# Service Foundation

## 运行服务

在项目根目录执行 `run.sh`（需 bash；若未标记可执行，可先 `chmod +x run.sh`）。脚本通过 `nohup python manage.py runserver` 后台启动，**HOST / PORT** 等仍由 `.env` 与 `manage.py` 读取。

```bash
./run.sh start    # 启动
./run.sh stop     # 停止
./run.sh restart  # 重启
./run.sh status   # 查看是否在运行（未运行则退出码 1）
```

**说明：**

- 需在项目根目录存在 **`.env`**；可选配置 **`APP_NAME`**（默认 `service-foundation`，用于 PID 目录名）、**`LOG_FILE_PATH`**（默认 `log`，Django 输出写入 `$LOG_FILE_PATH/$APP_NAME/django.log`）。
- PID 文件路径：`/var/run/<APP_NAME>/app.pid`；若目录不存在，启动时会尝试创建（可能需要 **`sudo`** 权限）。

## 运维控制台账号

控制台 `/console/` 使用 Django 自带的 `django.contrib.auth` 用户，且需要 **`is_staff`** 权限。首次部署或新环境请创建超级用户（默认具备 `is_staff`）：

```bash
python manage.py createsuperuser
```

按提示设置用户名与密码后，可用该账号登录 `/console/login/`。若使用已有账号，请在 Django Admin 或数据库中将其 **`is_staff`** 设为启用。

部署前请完成依赖安装与迁移，例如：

```bash
pip install -r requirements.txt
python manage.py migrate
```

## TCC：开启事务 API（`POST /api/tcc/tx`）

请求体需包含 **`biz_id`**（对应 `biz_meta.id`），`branches[]` 中每一项用 **`branch_index`**（与控制台为该业务配置的分支序号一致，对应 `branch_meta.branch_index`），不再要求调用方传入 `branch_meta` 表主键。

**一致性说明：** 若在控制台调整分支顺序或修改 `branch_index`，而调用方仍按旧序号组请求，可能命中错误的参与方 URL 或业务语义错位。降低与内部主键耦合的同时，需要与配置变更保持协同（例如发布顺序、约定或版本化），否则存在单方面变更顺序导致的数据不一致风险。
