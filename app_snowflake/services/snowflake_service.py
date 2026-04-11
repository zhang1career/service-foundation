from app_snowflake.config import get_app_config
from app_snowflake.services.snowflake_generator import SnowflakeGenerator

_generator = None


def generate_id(rid: int) -> dict:
    """
    Generate a single Snowflake ID for a caller registration id (rid).

    The generator encodes a 3-bit segment derived from ``rid`` (masked); see
    ``SnowflakeGenerator.generate`` and ``MASK_BUSINESS_ID``.

    Returns:
        Response containing ID, ``rid``, and parsed segment fields.
    """
    generator = _get_generator()
    id_value = generator.generate(rid)
    parsed = generator.parse_id(id_value)
    return {
        "id": str(id_value),
        "rid": rid,
        "datacenter_id": parsed["datacenter_id"],
        "machine_id": parsed["machine_id"],
        "recount": parsed["recount"],
        "business_id": parsed["business_id"],
        "timestamp": parsed["timestamp"],
        "sequence": parsed["sequence"],
    }


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
