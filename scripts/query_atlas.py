#!/usr/bin/env python3
"""
交互式连接并查询 MongoDB Atlas。

从项目根目录的 .env 读取账号信息。

命令:
  dbs                列出所有数据库
  use <db>           切换数据库
  colls              列出当前数据库的集合
  coll <name>        切换集合
  find [query]       查询当前集合，query 为 JSON，默认 {}
  update f u         对当前集合执行 updateMany，f=filter JSON，u=update JSON
  limit <n>          设置 find 返回数量上限（默认 20）
  help               显示帮助
  exit / quit        退出
"""
import json
import os
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


def get_mongo_uri() -> str:
    user = os.environ.get("MONGO_ATLAS_USER", "")
    password = os.environ.get("MONGO_ATLAS_PASS", "")
    host = os.environ.get("MONGO_ATLAS_HOST", "cluster.mongodb.net")
    cluster = os.environ.get("MONGO_ATLAS_CLUSTER", "cluster0")
    if not user or not password:
        raise SystemExit("错误: 请在 .env 中设置 MONGO_ATLAS_USER 和 MONGO_ATLAS_PASS")
    from urllib.parse import quote_plus
    password_encoded = quote_plus(password)
    return f"mongodb+srv://{user}:{password_encoded}@{cluster}.{host}/?retryWrites=true&w=majority&appName=Cluster0"


def _to_json_safe(docs):
    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])
    return docs


def _split_two_json(s: str) -> tuple[str | None, str | None]:
    """将 ' {...} {...} ' 拆成两个 JSON 字符串。"""
    s = s.strip()
    if not s.startswith("{"):
        return None, None
    depth = 0
    i = 0
    for i, c in enumerate(s):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
    first = s[: i + 1]
    second = s[i + 1 :].strip()
    return first if first else None, second if second else None


def _extract_first_json(s: str) -> tuple[str | None, str]:
    """提取第一个 {...} 和剩余部分。用于 find {} limit 10 这类输入。"""
    s = s.strip()
    if not s or not s.startswith("{"):
        return None, s
    depth = 0
    i = 0
    for i, c in enumerate(s):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
    first = s[: i + 1]
    remainder = s[i + 1 :].strip()
    return first, remainder


def repl(client):
    db_name = None
    coll_name = None
    limit = 20

    while True:
        try:
            prompt = "> "
            if db_name:
                prompt = f"{db_name}"
            if coll_name:
                prompt = f"{db_name}.{coll_name}"
            prompt = f"{prompt}> "
            line = input(prompt).strip().rstrip(";").strip()
        except EOFError:
            print()
            break

        if not line:
            continue

        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        rest = (parts[1] if len(parts) > 1 else "").strip()

        if cmd in ("exit", "quit", "q"):
            break

        if cmd == "help":
            print(__doc__)
            continue

        if cmd == "dbs":
            names = client.list_database_names()
            print(json.dumps(names, indent=2, ensure_ascii=False))
            continue

        if cmd == "use":
            if not rest:
                print("用法: use <db>")
                continue
            if rest not in client.list_database_names():
                print(f"数据库不存在: {rest}，请用 dbs 查看可用数据库")
                continue
            db_name = rest
            coll_name = None
            print(f"当前数据库: {db_name}")
            continue

        if cmd == "colls":
            if not db_name:
                print("请先用 use <db> 选择数据库")
                continue
            names = client[db_name].list_collection_names()
            print(json.dumps(names, indent=2, ensure_ascii=False))
            continue

        if cmd == "coll":
            if not db_name:
                print("请先用 use <db> 选择数据库")
                continue
            if not rest:
                print("用法: coll <collection>")
                continue
            if rest not in client[db_name].list_collection_names():
                print(f"集合不存在: {rest}，请用 colls 查看可用集合")
                continue
            coll_name = rest
            print(f"当前集合: {db_name}.{coll_name}")
            continue

        if cmd == "limit":
            if rest and rest.isdigit():
                limit = int(rest)
                print(f"limit = {limit}")
            else:
                print(f"当前 limit = {limit}")
            continue

        if cmd == "find":
            if not db_name or not coll_name:
                print("请先用 use <db> 和 coll <collection> 选择数据库和集合")
                continue
            query_str, remainder = _extract_first_json(rest)
            try:
                q = json.loads(query_str) if query_str else {}
            except json.JSONDecodeError as e:
                print(f"无效的 query JSON: {e}")
                continue
            lim = limit
            if remainder:
                rem_parts = remainder.split()
                if len(rem_parts) >= 2 and rem_parts[0].lower() == "limit" and rem_parts[1].isdigit():
                    lim = int(rem_parts[1])
            coll = client[db_name][coll_name]
            docs = _to_json_safe(list(coll.find(q).limit(lim)))
            print(json.dumps(docs, indent=2, ensure_ascii=False))
            continue

        if cmd in ("update", "updatemany"):
            if not db_name or not coll_name:
                print("请先用 use <db> 和 coll <collection> 选择数据库和集合")
                continue
            if not rest:
                print("用法: update <filter> <update>  例如: update {\"app_id\":\"0\"} {\"$set\":{\"app_id\":0}}")
                continue
            filter_str, update_str = _split_two_json(rest)
            if not filter_str or not update_str:
                print("需要两个 JSON 对象：filter 和 update")
                continue
            try:
                f = json.loads(filter_str)
                u = json.loads(update_str)
            except json.JSONDecodeError as e:
                print(f"无效的 JSON: {e}")
                continue
            coll = client[db_name][coll_name]
            result = coll.update_many(f, u)
            print(f"matched={result.matched_count} modified={result.modified_count}")
            continue

        print(f"未知命令: {cmd}，输入 help 查看帮助")


def main():
    from pymongo import MongoClient

    uri = get_mongo_uri()
    client = MongoClient(uri, tls=True, serverSelectionTimeoutMS=10000)

    try:
        client.admin.command("ping")
        print("已连接 Atlas，输入 help 查看命令")
    except Exception as e:
        raise SystemExit(f"连接 Atlas 失败: {e}")

    repl(client)


if __name__ == "__main__":
    main()
