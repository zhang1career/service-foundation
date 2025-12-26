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
    2. If ENVIRONMENT=test, load .env.test (overrides .env)
    3. If ENVIRONMENT=prod, load .env.prod (overrides .env)
    
    Args:
        base_dir: Base directory where .env files are located
        
    Returns:
        environ.Env instance with loaded environment variables
    """
    # First, load base .env file
    env_file = base_dir / ".env"
    if env_file.exists():
        environ.Env.read_env(env_file)
    
    # Then, load environment-specific file if ENVIRONMENT is set
    # Check both os.environ (system env) and the .env file we just loaded
    environment = os.environ.get("RUN_ENV", "").lower()
    
    if environment == "test":
        test_env_file = base_dir / ".env.test"
        if test_env_file.exists():
            environ.Env.read_env(test_env_file, overwrite=True)
    elif environment == "prod":
        prod_env_file = base_dir / ".env.prod"
        if prod_env_file.exists():
            environ.Env.read_env(prod_env_file, overwrite=True)
    
    # Create and return env instance after loading all files
    env = environ.Env()
    return env

