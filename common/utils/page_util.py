def build_page(data_list: list[dict], next_offset: int, total_num: int):
    return {
        "data": data_list,
        "next_offset": next_offset,
        "total_num": total_num
    }


def slice_window_for_page(total: int, page: int, page_size: int) -> tuple[int, int, int]:
    """
    Pure pagination math: given total row count and 1-based page index, return
    (offset, resolved_page, total_pages). page_size is clamped to at least 1.
    """
    if page_size < 1:
        page_size = 1
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    resolved = max(1, min(page, total_pages))
    offset = (resolved - 1) * page_size
    return offset, resolved, total_pages
