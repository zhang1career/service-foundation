import json


def json_encode(result):
    return json.dumps(result, indent=None, default=str)


def json_decode(param):
    return json.loads(param)
