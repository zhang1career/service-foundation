from app_snowflake.config import get_app_config
from app_snowflake.services.snowflake_generator import SnowflakeGenerator

_generator = None


def _get_generator():
    """Lazy initialization of SnowflakeGenerator to avoid DB connection at import time."""
    global _generator
    if _generator is None:
        _app_config_dict = get_app_config()
        _generator = SnowflakeGenerator(
            datacenter_id=_app_config_dict["datacenter_id"],
            machine_id=_app_config_dict["machine_id"],
            start_timestamp=_app_config_dict["start_timestamp"],
        )
    return _generator


def generate_id(business_id: int = 0) -> dict:
    """
    Generate a single Snowflake ID

    Returns:
        Response containing ID and detailed information
    """
    generator = _get_generator()
    id_value = generator.generate(business_id)
    parsed = generator.parse_id(id_value)
    return {
        "id": str(id_value),
        "datacenter_id": parsed["datacenter_id"],
        "machine_id": parsed["machine_id"],
        "recount": parsed["recount"],
        "business_id": parsed["business_id"],
        "timestamp": parsed["timestamp"],
        "sequence": parsed["sequence"],
    }
