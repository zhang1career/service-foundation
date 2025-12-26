from app_snowflake.config import get_app_config
from app_snowflake.exceptions.configuration_error_exception import ConfigurationErrorException
from app_snowflake.services.snowflake_generator import SnowflakeGenerator

try:
    app_config_dict = get_app_config()

    generator = SnowflakeGenerator(
        datacenter_id=app_config_dict["datacenter_id"],
        machine_id=app_config_dict["machine_id"],
        start_timestamp=app_config_dict["start_timestamp"],
    )
except Exception as e:
    raise ConfigurationErrorException(f"Failed to initialize SnowflakeGenerator: {str(e)}")


def generate_id(business_id: int = 0) -> dict:
    """
    Generate a single Snowflake ID
    
    Returns:
        Response containing ID and detailed information
    """
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
