from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from django.db import models


def attribute_for_field(model: models.Model, field_name: str, field_type: str) -> Any:
    v = getattr(model, field_name, None)
    if field_type == "date" and isinstance(v, datetime):
        return v.strftime("%Y-%m-%dT%H:%M")
    if field_type == "json":
        if v is None:
            return ""
        if isinstance(v, (dict, list)):
            enc = json.dumps(v, ensure_ascii=False, indent=2)
            return enc
        return str(v)
    return v
