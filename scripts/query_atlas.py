#!/usr/bin/env python3
"""
mongosh 风格交互式连接并查询 MongoDB Atlas。

从项目根目录的 .env 读取账号信息。

命令（兼容 mongosh）:
  show dbs                    列出所有数据库
  use <db>                    切换数据库
  db                          显示当前数据库
  show collections            列出当前数据库的集合
  <db>.<coll>.<method>(...)   便捷语法，等价于 use <db> + db.<coll>.<method>(...)
  db.<coll>.<method>(...)     查询等
  it                          继续迭代（find 结果下一页）
  help                        显示帮助
  exit / quit                 退出
"""
import sys
from pathlib import Path

try:
    import readline  # 启用方向键和编辑
except ImportError:
    pass

# 确保项目根在 Python 路径中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env
import environ

env = environ.Env()
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)
else:
    print("警告: 未找到 .env 文件", file=sys.stderr)

from common.atlas_repl import repl_step, get_mongo_uri


def main():
    from pymongo import MongoClient

    try:
        uri = get_mongo_uri()
    except ValueError as e:
        raise SystemExit(f"错误: {e}")

    client = MongoClient(uri, tls=True, serverSelectionTimeoutMS=10000)

    try:
        client.admin.command("ping")
        print("已连接 Atlas，输入 help 查看命令")
    except Exception as e:
        raise SystemExit(f"连接 Atlas 失败: {e}")

    state = None
    while True:
        try:
            prompt = "test> " if not state or not state.get("db_name") else f"{state['db_name']}> "
            line = input(prompt)
        except EOFError:
            print()
            break

        output_lines, state, exited = repl_step(client, line, state)
        for ln in output_lines:
            print(ln)
        if exited:
            break


if __name__ == "__main__":
    main()
