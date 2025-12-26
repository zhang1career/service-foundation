
def check_version():
    # lazy load
    import ssl
    # query
    return {
        "TLSv1": ssl.HAS_TLSv1,
        "TLSv1_1": ssl.HAS_TLSv1_1,
        "TLSv1_2": ssl.HAS_TLSv1_2,
        "TLSv1_3": ssl.HAS_TLSv1_3,
    }
