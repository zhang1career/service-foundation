"""Constants for app_know."""

# Default app ID (used when not specified)
APP_ID_DEFAULT = 0


def validate_app_id(app_id, default=None) -> int:
    """Validate and return app_id as integer. 0 is valid."""
    dflt = default if default is not None else APP_ID_DEFAULT
    if app_id is None:
        return dflt
    if isinstance(app_id, int):
        if app_id < 0:
            raise ValueError("app_id must be a non-negative integer")
        return app_id
    if isinstance(app_id, str):
        s = app_id.strip()
        if not s:
            return dflt
        try:
            val = int(s)
            if val < 0:
                raise ValueError("app_id must be a non-negative integer")
            return val
        except ValueError:
            raise ValueError("app_id must be an integer")
    try:
        val = int(app_id)
        if val < 0:
            raise ValueError("app_id must be a non-negative integer")
        return val
    except (TypeError, ValueError):
        raise ValueError("app_id must be an integer")

# Sentence workflow stage
STAGE_CREATED = 0
STAGE_CLEANED = 1
STAGE_PARSED = 2
STAGE_VECTORIZED = 3

# Sentence workflow status
STATUS_INCOMPLETE = 0
STATUS_COMPLETED = 1
STATUS_PENDING_REVIEW = 2

# Sentence classification (Claim / Fact / Event / Concept / Definition / Argument)
CLASS_CLAIM = "claim"
CLASS_FACT = "fact"
CLASS_EVENT = "event"
CLASS_CONCEPT = "concept"
CLASS_DEFINITION = "definition"
CLASS_ARGUMENT = "argument"

CLASS_CHOICES = [
    (CLASS_CLAIM, "Claim"),
    (CLASS_FACT, "Fact"),
    (CLASS_EVENT, "Event"),
    (CLASS_CONCEPT, "Concept"),
    (CLASS_DEFINITION, "Definition"),
    (CLASS_ARGUMENT, "Argument"),
]

# Perspective type (人物/概念/指标) - int
PERSPECTIVE_PERSON = 0
PERSPECTIVE_CONCEPT = 1
PERSPECTIVE_METRIC = 2
PERSPECTIVE_TYPES = [
    (PERSPECTIVE_PERSON, "人物"),
    (PERSPECTIVE_CONCEPT, "概念"),
    (PERSPECTIVE_METRIC, "指标"),
]

# Insight type (矛盾发现/路径推理/跨文本综合) - int
INSIGHT_CONTRADICTION = 0
INSIGHT_PATH_REASONING = 1
INSIGHT_CROSS_TEXT = 2
INSIGHT_TYPES = [
    (INSIGHT_CONTRADICTION, "矛盾发现"),
    (INSIGHT_PATH_REASONING, "路径推理"),
    (INSIGHT_CROSS_TEXT, "跨文本综合"),
]

# Insight status - int
INSIGHT_DRAFT = 0
INSIGHT_APPROVED = 1
INSIGHT_STATUS = [(INSIGHT_DRAFT, "草稿"), (INSIGHT_APPROVED, "已采纳")]
