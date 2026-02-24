"""
Environment variable loading utility

Supports layered environment variable loading:
1. Load .env (default/base configuration)
2. Load .env.test or .env.prod based on ENVIRONMENT variable (overrides .env)
"""
import os
from pathlib import Path

import environ


def load_env(base_dir: Path) -> environ.Env:
    """
    Load environment variables with layered support
    
    Loading order:
    1. Load .env (base/default configuration)
    2. Load environment-specific file based on RUN_ENV (overrides .env):
       - RUN_ENV=dev  -> .env.dev
       - RUN_ENV=test -> .env.test
       - RUN_ENV=prod -> .env.prod
    
    Args:
        base_dir: Base directory where .env files are located
        
    Returns:
        environ.Env instance with loaded environment variables
    """
    # First, load base .env file
    env_file = base_dir / ".env"
    if env_file.exists():
        environ.Env.read_env(env_file)
    
    # Then, load environment-specific file if RUN_ENV is set
    environment = os.environ.get("RUN_ENV", "").lower()
    
    env_specific_file = None
    if environment == "dev":
        env_specific_file = base_dir / ".env.dev"
    elif environment == "test":
        env_specific_file = base_dir / ".env.test"
    elif environment == "prod":
        env_specific_file = base_dir / ".env.prod"
    
    if env_specific_file and env_specific_file.exists():
        environ.Env.read_env(env_specific_file, overwrite=True)
    
    # Create and return env instance after loading all files
    env = environ.Env()
    return env

