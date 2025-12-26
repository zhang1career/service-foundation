def build_page(data_list: list[dict], next_offset: int, total_num: int):
    return {
        "data": data_list,
        "next_offset": next_offset,
        "total_num": total_num
    }
