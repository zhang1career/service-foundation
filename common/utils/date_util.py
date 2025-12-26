from datetime import datetime, timedelta


def get_now_timestamp() -> int:
    """
    Get the current timestamp in seconds
    """
    now = datetime.now()
    return int(now.timestamp())


def get_now_timestamp_ms() -> int:
    """
    Get the current timestamp in milliseconds
    """
    now = datetime.now()
    return int(round(now.timestamp() * 1000))


def get_natual_range_of_date(date_str: str, date_format: str) -> object:
    """
    Convert date string to a pair timestamp
    (begin timestamp of the day, begin timestamp of the next day)
    """
    # Convert the input date string to a datetime object
    date_obj = get_datetime_of_date_str(date_str, date_format)

    # Calculate the epoch timestamp of the beginning of the day
    start_of_day = int(date_obj.timestamp())

    # Calculate the epoch timestamp of the beginning of the next day
    next_day = date_obj + timedelta(days=1)
    start_of_next_day = int(next_day.timestamp())

    return start_of_day, start_of_next_day


def get_date_int_of_data_str(date_str: str):
    """
    Convert date string into date integer
    "20240501" -> 20240501

    @param date_str: date in string
    @return: date in integer
    """
    return int(date_str)


def get_timestamp_int_of_data_str(date_str: str, date_format: str):
    """
    Convert date string into timestamp integer
    "20240501" -> 1714521600

    @param date_str: date in string
    @param date_format: date format in string
    @return: timestamp in integer
    """
    date_obj = get_datetime_of_date_str(date_str, date_format)
    return get_timestamp_int_of_datatime(date_obj)


def get_timestamp_int_of_datatime(date_obj: datetime):
    """
    Convert datetime into timestamp integer
    2024-05-01 00:00:00 -> 1714521600

    @param date_obj: datetime
    @return: timestamp in integer
    """
    return int(round(date_obj.timestamp()))


def get_datetime_of_date_str(date_str: str, date_format: str):
    """
    Convert date string to a datetime
    "20240501" -> 2024-05-01 00:00:00
    """
    date_obj = datetime.strptime(date_str, date_format)
    return date_obj


def get_datetime_of_timestamp(timestamp: int):
    """
    Convert timestamp to datetime
    1714521600 -> 2024-05-01 00:00:00

    @param timestamp:
    @return: datetime
    """
    return datetime.fromtimestamp(timestamp)


def get_date_str_of_datetime(date_obj: datetime, date_format: str) -> str:
    """
    Convert datetime to date string
    2024-05-01 00:00:00 -> "20240501"

    @param date_obj:
    @param date_format:
    @return: date string
    """
    return date_obj.strftime(date_format)


def get_human_readable_date_str_of_datetime(date_obj: datetime) -> str:
    """
    Convert datetime to human readable date string
    2024-05-01 00:00:00 -> "2024-05-01"

    @param date_obj:
    @return: date string
    """
    return date_obj.strftime("%Y-%m-%d")


def get_date_int_of_timestamp(timestamp: int):
    """
    Convert timestamp to date integer
    1714521600 -> 20240501
    @param timestamp:
    @return:
    """
    date_obj = datetime.fromtimestamp(timestamp)
    date_str = get_date_str_of_datetime(date_obj, "%Y%m%d")
    return get_date_int_of_data_str(date_str)


def get_days_before(date_obj: datetime, days: int):
    """
    Get some days before given datetime
    @param date_obj: given datetime
    @param days: days before
    @return: before datetime
    """
    return date_obj - timedelta(days=days)


