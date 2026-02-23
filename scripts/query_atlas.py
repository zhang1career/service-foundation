#!/usr/bin/env python3
"""
mongosh 风格交互式连接并查询 MongoDB Atlas。

从项目根目录的 .env 读取账号信息。

命令（兼容 mongosh）:
  show dbs                    列出所有数据库
  use <db>                    切换数据库
  db                          显示当前数据库
  show collections            列出当前数据库的集合
  db.<coll>.find([query])     查询，query 为 JSON 默认 {}
  db.<coll>.findOne([query])  返回单条
  db.<coll>.updateMany(f, u)  批量更新，f=filter JSON，u=update JSON
  db.<coll>.getIndexes()      列出索引
  db.<coll>.createIndex(k[,o]) 创建索引，k=keys JSON，o=options JSON 可选
  db.<coll>.dropIndex(n)      删除索引
  it                          继续迭代（find 结果下一页）
  help                        显示帮助
  exit / quit                 退出
"""
import json
import os
import re
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

# find 默认每批数量（与 mongosh 一致）
DEFAULT_BATCH_SIZE = 20


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


def _extract_parens_args(s: str) -> tuple[str | None, str]:
    """提取括号内第一个完整 (...) 和剩余部分。"""
    s = s.strip()
    i = s.find("(")
    if i < 0:
        return None, s
    depth = 0
    j = i
    for j, c in enumerate(s[i:], start=i):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
    inner = s[i + 1 : j].strip()
    remainder = s[j + 1 :].strip()
    return inner, remainder


def _parse_find_args(inner: str) -> tuple[dict | None, int | None]:
    """解析 find(...) 的参数：query 和 limit（从 .limit(n) 链式调用）。"""
    # 先取第一个逗号分隔的参数（忽略 projection）
    # 简单情况：单个 {} 或空
    inner = inner.strip()
    if not inner:
        return {}, None
    # 提取第一个 {...}
    if not inner.startswith("{"):
        return {}, None
    depth = 0
    i = 0
    for i, c in enumerate(inner):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
    query_str = inner[: i + 1]
    try:
        q = json.loads(query_str)
    except json.JSONDecodeError:
        return None, None
    return q, None


def _parse_method_chain(remainder: str) -> dict:
    """解析 .limit(n) .skip(n) 等链式调用。"""
    opts = {}
    while remainder:
        m = re.match(r"\.\s*(limit|skip)\s*\(\s*(\d+)\s*\)", remainder, re.IGNORECASE)
        if not m:
            break
        opts[m.group(1).lower()] = int(m.group(2))
        remainder = remainder[m.end() :].strip()
    return opts


def _extract_first_json(s: str) -> tuple[str | None, str]:
    """提取第一个 {...} 和剩余部分。"""
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


def _split_two_json(s: str) -> tuple[str | None, str | None]:
    """将 ' {...} , {...} ' 拆成两个 JSON 字符串。"""
    first, rest = _extract_first_json(s)
    if not first:
        return None, None
    rest = rest.lstrip(",").strip()
    second, _ = _extract_first_json(rest)
    return first, second


def _match_db_coll_method(line: str) -> re.Match | None:
    """匹配 db.<coll>.<method>( 或 db.<coll>.<method> ( """
    return re.match(
        r"db\s*\.\s*(\w+)\s*\.\s*(\w+)\s*\(",
        line,
        re.IGNORECASE,
    )


def repl(client):
    db_name = None
    limit = DEFAULT_BATCH_SIZE
    skip = 0
    # 用于 it 的游标状态（mongosh 风格：键入 it 继续显示下一批）
    it_coll = None
    it_query = None
    it_skip = 0
    it_limit = DEFAULT_BATCH_SIZE

    while True:
        try:
            # mongosh 风格 prompt: dbname>
            prompt = "test> " if not db_name else f"{db_name}> "
            line = input(prompt).strip().rstrip(";").strip()
        except EOFError:
            print()
            break

        if not line:
            continue

        lower = line.lower()

        if lower in ("exit", "quit", "q"):
            break

        try:
            if lower == "help":
                print(__doc__)
                continue

            if lower == "show dbs":
                names = client.list_database_names()
                for n in names:
                    print(n)
                continue

            if lower == "db":
                if db_name:
                    print(db_name)
                else:
                    print("test")  # mongosh 默认
                continue

            if lower.startswith("use "):
                rest = line[4:].strip()
                if not rest:
                    print("用法: use <db>")
                    continue
                if rest not in client.list_database_names():
                    print(f"数据库不存在: {rest}，请用 show dbs 查看")
                    continue
                db_name = rest
                it_coll = None
                print(f"switched to db {rest}")
                continue

            if lower == "show collections":
                if not db_name:
                    print("请先用 use <db> 选择数据库")
                    continue
                names = client[db_name].list_collection_names()
                for n in names:
                    print(n)
                continue

            if lower == "it":
                if it_coll is None:
                    print("没有可迭代的 find 结果")
                    continue
                cursor = it_coll.find(it_query).skip(it_skip).limit(it_limit)
                docs = _to_json_safe(list(cursor))
                if not docs:
                    print("已到末尾")
                    it_coll = None
                else:
                    for d in docs:
                        print(json.dumps(d, ensure_ascii=False))
                    it_skip += len(docs)
                    if len(docs) < it_limit:
                        it_coll = None
                continue

            # 尝试解析 db.<coll>.<method>(...)
            m = _match_db_coll_method(line)
            if m:
                coll_name = m.group(1)
                method = m.group(2).lower()
                rest_after_match = line[m.end() :]
                inner, remainder = _extract_parens_args(rest_after_match)
                if inner is None and "(" in rest_after_match:
                    print("无效的括号")
                    continue

                # 若未 use，默认 test
                current_db = db_name or "test"
                if current_db not in client.list_database_names():
                    print(f"数据库 {current_db} 不存在")
                    continue
                if coll_name not in client[current_db].list_collection_names():
                    print(f"集合 {current_db}.{coll_name} 不存在")
                    continue

                coll = client[current_db][coll_name]

                if method == "find":
                    q, _ = _parse_find_args(inner or "")
                    if q is None:
                        print("无效的 query JSON")
                        continue
                    chain = _parse_method_chain(remainder)
                    lim = chain.get("limit", limit)
                    sk = chain.get("skip", 0)
                    cursor = coll.find(q).skip(sk).limit(lim)
                    docs = _to_json_safe(list(cursor))
                    # mongosh 风格：逐条输出
                    for d in docs:
                        print(json.dumps(d, ensure_ascii=False))
                    # 若返回满 batch，保存状态供 it 继续迭代
                    if len(docs) >= lim:
                        it_coll = coll
                        it_query = q
                        it_skip = sk + lim
                        it_limit = lim
                    else:
                        it_coll = None
                    continue

                if method == "findone":
                    q, _ = _parse_find_args(inner or "")
                    if q is None:
                        print("无效的 query JSON")
                        continue
                    doc = coll.find_one(q)
                    if doc:
                        if "_id" in doc:
                            doc["_id"] = str(doc["_id"])
                        print(json.dumps(doc, indent=2, ensure_ascii=False))
                    else:
                        print("null")
                    it_coll = None
                    continue

                if method == "updatemany":
                    filter_str, update_str = _split_two_json(inner or "{}")
                    if not filter_str or not update_str:
                        print("用法: db.coll.updateMany(<filter>, <update>)")
                        continue
                    try:
                        f = json.loads(filter_str)
                        u = json.loads(update_str)
                    except json.JSONDecodeError as e:
                        print(f"无效的 JSON: {e}")
                        continue
                    result = coll.update_many(f, u)
                    print(
                        json.dumps(
                            {
                                "acknowledged": True,
                                "matchedCount": result.matched_count,
                                "modifiedCount": result.modified_count,
                            },
                            ensure_ascii=False,
                        )
                    )
                    it_coll = None
                    continue

                if method == "getindexes":
                    idx_list = list(coll.list_indexes())
                    idx_safe = [{"name": i["name"], "key": dict(i["key"])} for i in idx_list]
                    print(json.dumps(idx_safe, indent=2, ensure_ascii=False))
                    it_coll = None
                    continue

                if method == "createindex":
                    if not inner or not inner.strip().startswith("{"):
                        print("用法: db.coll.createIndex(<keys_json>[, options_json])")
                        continue
                    keys_str, opts_str = None, ""
                    depth = 0
                    for i, c in enumerate(inner):
                        if c == "{":
                            depth += 1
                        elif c == "}":
                            depth -= 1
                            if depth == 0:
                                keys_str = inner[: i + 1]
                                opts_str = inner[i + 1 :].strip().lstrip(",").strip()
                                break
                    if not keys_str:
                        print("无效的 keys JSON")
                        continue
                    try:
                        keys = json.loads(keys_str)
                    except json.JSONDecodeError as e:
                        print(f"无效的 keys JSON: {e}")
                        continue
                    if isinstance(keys, dict):
                        keys = list(keys.items())
                    options = {}
                    if opts_str and opts_str.strip().startswith("{"):
                        o_depth = 0
                        for i, c in enumerate(opts_str):
                            if c == "{":
                                o_depth += 1
                            elif c == "}":
                                o_depth -= 1
                                if o_depth == 0:
                                    try:
                                        options = json.loads(opts_str[: i + 1])
                                    except json.JSONDecodeError:
                                        pass
                                    break
                    name = coll.create_index(keys, **options)
                    print(json.dumps({"numIndexesBefore": 0, "numIndexesAfter": 0, "ok": 1, "name": name}))
                    it_coll = None
                    continue

                if method == "dropindex":
                    if not inner:
                        print("用法: db.coll.dropIndex(<name 或 keys_json>)")
                        continue
                    idx_spec = inner.strip().strip('"\'')
                    if idx_spec.startswith("{"):
                        try:
                            idx_spec = json.loads(idx_spec)
                        except json.JSONDecodeError as e:
                            print(f"无效的 keys JSON: {e}")
                            continue
                    try:
                        coll.drop_index(idx_spec)
                        print(json.dumps({"nIndexesWas": 0, "ok": 1}))
                    except Exception as e:
                        print(f"删除失败: {e}")
                    it_coll = None
                    continue

            print(f"未知命令，输入 help 查看帮助")
        except Exception as e:
            print(f"错误: {e}")


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
