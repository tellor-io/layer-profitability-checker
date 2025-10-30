"""
Configuration loader for Tellor Layer Profitability Checker.
Provides centralized access to configuration values.
"""

from typing import Any, Dict

import yaml


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the config file

    Returns:
        Dictionary containing configuration values
    """
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except FileNotFoundError:
        print(f"Warning: Config file {config_path} not found, using defaults")
        return {}
    except yaml.YAMLError as e:
        print(f"Warning: Error parsing config file: {e}, using defaults")
        return {}


def get_rpc_endpoint(config: Dict[str, Any]) -> str:
    """
    Get RPC endpoint from config.

    Args:
        config: Configuration dictionary

    Returns:
        RPC endpoint URL
    """
    return config.get("rpc_endpoint", "http://localhost:26657")


def get_rest_endpoint(config: Dict[str, Any]) -> str:
    """
    Get REST API endpoint from config.

    Args:
        config: Configuration dictionary

    Returns:
        REST API endpoint URL
    """
    return config.get("rest_endpoint", "http://localhost:1317")


def get_min_gas_price(config: Dict[str, Any]) -> float:
    """
    Get minimum gas price from config if specified.

    Args:
        config: Configuration dictionary

    Returns:
        Minimum gas price or None if not specified
    """
    if "min_gas_price" in config:
        try:
            return float(config["min_gas_price"])
        except (ValueError, TypeError):
            print(
                f"Warning: Invalid min_gas_price in config: {config['min_gas_price']}"
            )
            return None
    return None


def get_account_address(config: Dict[str, Any]) -> str:
    """
    Get account address from config if specified.

    Args:
        config: Configuration dictionary

    Returns:
        Account address or None if not specified
    """
    return config.get("account_address")


def get_query_datas(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Get query_datas from config.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary mapping price feed names to query data hex strings
    """
    return config.get("query_datas", {})
