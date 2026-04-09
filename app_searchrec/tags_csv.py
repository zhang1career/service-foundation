"""Comma-separated tag strings for sf_searchrec.doc.tags (TEXT)."""


def parse_tags_csv(raw: str) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    return [p.strip() for p in str(raw).split(",") if p.strip()]


def join_tags_csv(parts: list[str]) -> str:
    return ",".join(str(p).strip() for p in parts if str(p).strip())
