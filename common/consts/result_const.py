# result id
RESULT_INDEX_ID_STAT_DAILY = 10000001
RESULT_INDEX_ID_REVIEW_DAILY = 10000002

# result map
RESULT_INDEX_MAP = {
    RESULT_INDEX_ID_STAT_DAILY: {
        "module": "app_stock.biz.stat_daily_biz",
        "func": "get_result",
    },
    RESULT_INDEX_ID_REVIEW_DAILY: {
        "module": "app_stock.biz.review_daily_biz",
        "func": "get_result",
    },
}
