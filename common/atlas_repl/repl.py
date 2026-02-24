"""
mongosh-style Atlas REPL core logic. Used by CLI (scripts/query_atlas.py) and API.
"""
import json
import os
import re
from pathlib import Path

# find default batch size (same as mongosh)
DEFAULT_BATCH_SIZE = 20

_HELP_DOC = """
mongosh 风格交互式连接并查询 MongoDB Atlas。

命令（兼容 mongosh）:
  show dbs                    列出所有数据库
  use <db>                    切换数据库
  db                          显示当前数据库
  show collections            列出当前数据库的集合
  <db>.<coll>.<method>(...)   便捷语法
  db.<coll>.find([query])     查询
  db.<coll>.findOne([query])  返回单条
  db.<coll>.updateMany(f, u)  批量更新
  db.<coll>.getIndexes()      列出索引
  db.<coll>.createIndex(k[,o]) 创建索引
  db.<coll>.dropIndex(n)      删除索引
  it                          继续迭代（find 结果下一页）
  help                        显示帮助
  exit / quit                 退出
""".strip()


def get_mongo_uri() -> str:
    """Build MongoDB URI from env. Raises ValueError if credentials missing."""
    user = os.environ.get("MONGO_ATLAS_USER", "")
    password = os.environ.get("MONGO_ATLAS_PASS", "")
    host = os.environ.get("MONGO_ATLAS_HOST", "cluster.mongodb.net")
    cluster = os.environ.get("MONGO_ATLAS_CLUSTER", "cluster0")
    if not user or not password:
        raise ValueError("请在 .env 中设置 MONGO_ATLAS_USER 和 MONGO_ATLAS_PASS")
    from urllib.parse import quote_plus

    password_encoded = quote_plus(password)
    return f"mongodb+srv://{user}:{password_encoded}@{cluster}.{host}/?retryWrites=true&w=majority&appName=Cluster0"


def _to_json_safe(docs):
    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])
    return docs


def _extract_parens_args(s: str) -> tuple:
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


def _parse_find_args(inner: str) -> tuple:
    inner = inner.strip()
    if not inner:
        return {}, None
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
    opts = {}
    while remainder:
        m = re.match(r"\.\s*(limit|skip)\s*\(\s*(\d+)\s*\)", remainder, re.IGNORECASE)
        if not m:
            break
        opts[m.group(1).lower()] = int(m.group(2))
        remainder = remainder[m.end() :].strip()
    return opts


def _extract_first_json(s: str) -> tuple:
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


def _split_two_json(s: str) -> tuple:
    first, rest = _extract_first_json(s)
    if not first:
        return None, None
    rest = rest.lstrip(",").strip()
    second, _ = _extract_first_json(rest)
    return first, second


def _match_db_coll_method(line: str):
    return re.match(r"db\s*\.\s*(\w+)\s*\.\s*(\w+)\s*\(", line, re.IGNORECASE)


_SHORTHAND_RESERVED = frozenset({"show", "use", "db", "help", "it", "exit", "quit", "q"})


def _try_expand_shorthand(line: str, client) -> tuple:
    m = re.match(r"(\w+)\s*\.\s*(\w+)\s*\.\s*(\w+)\s*\(", line, re.IGNORECASE)
    if not m:
        return None
    db_name_cand, coll, method = m.group(1), m.group(2), m.group(3)
    if db_name_cand.lower() in _SHORTHAND_RESERVED:
        return None
    if db_name_cand not in client.list_database_names():
        return None
    rest = "(" + line[m.end() :]
    expanded = f"db.{coll}.{method}{rest}"
    return expanded, db_name_cand


def _default_state():
    return {
        "db_name": None,
        "it_db_name": None,
        "it_coll_name": None,
        "it_query": None,
        "it_skip": 0,
        "it_limit": DEFAULT_BATCH_SIZE,
    }


def repl_step(client, line: str, state: dict = None) -> tuple[list[str], dict, bool]:
    """
    Execute one REPL step.
    Returns: (output_lines, new_state, exited)
    - output_lines: list of strings to display
    - new_state: serializable dict for next call
    - exited: True if user typed exit/quit/q
    """
    state = state or _default_state()
    out_lines = []
    db_name = state.get("db_name")
    limit = DEFAULT_BATCH_SIZE
    it_db_name = state.get("it_db_name")
    it_coll_name = state.get("it_coll_name")
    it_query = state.get("it_query")
    it_skip = state.get("it_skip") or 0
    it_limit = state.get("it_limit") or limit

    def emit(s):
        out_lines.append(s)

    line = (line or "").strip().rstrip(";").strip()
    if not line:
        return [], state, False

    lower = line.lower()
    if lower in ("exit", "quit", "q"):
        return [], _default_state(), True

    try:
        if lower == "help":
            emit(_HELP_DOC)
            return out_lines, state, False

        if lower == "show dbs":
            for n in client.list_database_names():
                emit(n)
            return out_lines, state, False

        if lower == "db":
            emit(db_name if db_name else "test")
            return out_lines, state, False

        if lower.startswith("use "):
            rest = line[4:].strip()
            if not rest:
                emit("用法: use <db>")
                return out_lines, state, False
            if rest not in client.list_database_names():
                emit(f"数据库不存在: {rest}，请用 show dbs 查看")
                return out_lines, state, False
            new_state = dict(state)
            new_state["db_name"] = rest
            new_state["it_db_name"] = None
            new_state["it_coll_name"] = None
            emit(f"switched to db {rest}")
            return out_lines, new_state, False

        if lower == "show collections":
            if not db_name:
                emit("请先用 use <db> 选择数据库")
                return out_lines, state, False
            for n in client[db_name].list_collection_names():
                emit(n)
            return out_lines, state, False

        if lower == "it":
            if it_coll_name is None or it_db_name is None:
                emit("没有可迭代的 find 结果")
                return out_lines, state, False
            coll = client[it_db_name][it_coll_name]
            cursor = coll.find(it_query).skip(it_skip).limit(it_limit)
            docs = _to_json_safe(list(cursor))
            new_state = dict(state)
            if not docs:
                emit("已到末尾")
                new_state["it_coll_name"] = None
                new_state["it_db_name"] = None
            else:
                for d in docs:
                    emit(json.dumps(d, ensure_ascii=False))
                new_state["it_skip"] = it_skip + len(docs)
                if len(docs) < it_limit:
                    new_state["it_coll_name"] = None
                    new_state["it_db_name"] = None
            return out_lines, new_state, False

        # shorthand: dbname.coll.method(...)
        shorthand = _try_expand_shorthand(line, client)
        if shorthand:
            expanded_line, new_db = shorthand
            db_name = new_db
            line = expanded_line
            new_state = dict(state)
            new_state["db_name"] = new_db
            new_state["it_db_name"] = None
            new_state["it_coll_name"] = None
            emit(f"switched to db {new_db}")
            state = new_state

        m = _match_db_coll_method(line)
        if m:
            coll_name = m.group(1)
            method = m.group(2).lower()
            rest_after_match = line[m.end() :]
            inner, remainder = _extract_parens_args(rest_after_match)
            if inner is None and "(" in rest_after_match:
                emit("无效的括号")
                return out_lines, state, False

            current_db = db_name or "test"
            if current_db not in client.list_database_names():
                emit(f"数据库 {current_db} 不存在")
                return out_lines, state, False
            if coll_name not in client[current_db].list_collection_names():
                emit(f"集合 {current_db}.{coll_name} 不存在")
                return out_lines, state, False

            coll = client[current_db][coll_name]
            new_state = dict(state)
            new_state["it_coll_name"] = None
            new_state["it_db_name"] = None

            if method == "find":
                q, _ = _parse_find_args(inner or "")
                if q is None:
                    emit("无效的 query JSON")
                    return out_lines, state, False
                chain = _parse_method_chain(remainder)
                lim = chain.get("limit", limit)
                sk = chain.get("skip", 0)
                cursor = coll.find(q).skip(sk).limit(lim)
                docs = _to_json_safe(list(cursor))
                for d in docs:
                    emit(json.dumps(d, ensure_ascii=False))
                if len(docs) >= lim:
                    new_state["it_db_name"] = current_db
                    new_state["it_coll_name"] = coll_name
                    new_state["it_query"] = q
                    new_state["it_skip"] = sk + lim
                    new_state["it_limit"] = lim
                return out_lines, new_state, False

            if method == "findone":
                q, _ = _parse_find_args(inner or "")
                if q is None:
                    emit("无效的 query JSON")
                    return out_lines, state, False
                doc = coll.find_one(q)
                if doc:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    emit(json.dumps(doc, indent=2, ensure_ascii=False))
                else:
                    emit("null")
                return out_lines, new_state, False

            if method == "updatemany":
                filter_str, update_str = _split_two_json(inner or "{}")
                if not filter_str or not update_str:
                    emit("用法: db.coll.updateMany(<filter>, <update>)")
                    return out_lines, state, False
                try:
                    f = json.loads(filter_str)
                    u = json.loads(update_str)
                except json.JSONDecodeError as e:
                    emit(f"无效的 JSON: {e}")
                    return out_lines, state, False
                result = coll.update_many(f, u)
                emit(
                    json.dumps(
                        {
                            "acknowledged": True,
                            "matchedCount": result.matched_count,
                            "modifiedCount": result.modified_count,
                        },
                        ensure_ascii=False,
                    )
                )
                return out_lines, new_state, False

            if method == "getindexes":
                idx_list = list(coll.list_indexes())
                idx_safe = [{"name": i["name"], "key": dict(i["key"])} for i in idx_list]
                emit(json.dumps(idx_safe, indent=2, ensure_ascii=False))
                return out_lines, new_state, False

            if method == "createindex":
                if not inner or not inner.strip().startswith("{"):
                    emit("用法: db.coll.createIndex(<keys_json>[, options_json])")
                    return out_lines, state, False
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
                    emit("无效的 keys JSON")
                    return out_lines, state, False
                try:
                    keys = json.loads(keys_str)
                except json.JSONDecodeError as e:
                    emit(f"无效的 keys JSON: {e}")
                    return out_lines, state, False
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
                emit(json.dumps({"numIndexesBefore": 0, "numIndexesAfter": 0, "ok": 1, "name": name}))
                return out_lines, new_state, False

            if method == "dropindex":
                if not inner:
                    emit("用法: db.coll.dropIndex(<name 或 keys_json>)")
                    return out_lines, state, False
                idx_spec = inner.strip().strip('"\'')
                if idx_spec.startswith("{"):
                    try:
                        idx_spec = json.loads(idx_spec)
                    except json.JSONDecodeError as e:
                        emit(f"无效的 keys JSON: {e}")
                        return out_lines, state, False
                try:
                    coll.drop_index(idx_spec)
                    emit(json.dumps({"nIndexesWas": 0, "ok": 1}))
                except Exception as e:
                    emit(f"删除失败: {e}")
                return out_lines, new_state, False

        emit("未知命令，输入 help 查看帮助")
        return out_lines, state, False

    except Exception as e:
        emit(f"错误: {e}")
        return out_lines, state, False
