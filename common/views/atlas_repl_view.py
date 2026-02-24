"""
REST API view for Atlas REPL: execute one mongosh-style command and return output.
Used by the knowledge detail page's terminal interaction box.
"""
import logging

from pymongo import MongoClient
from rest_framework import status as http_status
from rest_framework.views import APIView

from common.atlas_repl import repl_step, get_mongo_uri
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


class AtlasReplView(APIView):
    """
    POST: Execute one Atlas REPL command.
    Body: { "line": "show dbs", "session": { ... } }
    Returns: { "output": "line1\\nline2", "session": { ... } }
    """

    def post(self, request, *args, **kwargs):
        try:
            data = getattr(request, "data", None) or request.POST or {}
            if not isinstance(data, dict):
                data = {}
            line = (data.get("line") or "").strip()
            session = data.get("session")
            if session is not None and not isinstance(session, dict):
                session = None

            # First connection: show welcome when no session and empty/init line
            if session is None and (not line or line.lower() == "init"):
                try:
                    uri = get_mongo_uri()
                    client = MongoClient(uri, tls=True, serverSelectionTimeoutMS=10000)
                    client.admin.command("ping")
                except ValueError as e:
                    return resp_err(str(e), status=http_status.HTTP_200_OK)
                except Exception as e:
                    return resp_err("连接 Atlas 失败: " + str(e), status=http_status.HTTP_200_OK)
                return resp_ok({
                    "output": "已连接 Atlas，输入 help 查看命令",
                    "session": {},
                })

            try:
                uri = get_mongo_uri()
            except ValueError as e:
                return resp_err(str(e), status=http_status.HTTP_200_OK)

            client = MongoClient(uri, tls=True, serverSelectionTimeoutMS=10000)
            client.admin.command("ping")

            output_lines, new_state, _exited = repl_step(client, line, session)
            output = "\n".join(output_lines) if output_lines else ""

            # Ensure session is JSON-serializable (it_query may be dict)
            session_out = {}
            for k, v in new_state.items():
                if v is not None:
                    session_out[k] = v

            return resp_ok({"output": output, "session": session_out})
        except Exception as e:
            if "ping" in str(e).lower() or "connection" in str(e).lower():
                return resp_err("连接 Atlas 失败: " + str(e), status=http_status.HTTP_200_OK)
            logger.exception("[AtlasReplView] Error: %s", e)
            return resp_exception(e)
