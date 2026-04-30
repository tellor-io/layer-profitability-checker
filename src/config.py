"""
Configuration loader for Tellor Layer Profitability Checker.
Provides centralized access to configuration values.
"""

from typing import Any, Dict, List

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


REQUIRED_NETWORKS = ("mainnet", "testnet")
REQUIRED_NETWORK_FIELDS = ("name", "rpc_endpoint", "rest_endpoint")


def validate_networks(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate and return configured networks.

    Args:
        config: Configuration dictionary

    Returns:
        List of network configuration dictionaries

    Raises:
        ValueError: If required network configuration is missing or invalid
    """
    networks = config.get("networks")
    if not isinstance(networks, list) or not networks:
        raise ValueError(
            "Config must define a non-empty 'networks' list with mainnet and testnet"
        )

    seen_names = set()
    for index, network in enumerate(networks, start=1):
        if not isinstance(network, dict):
            raise ValueError(f"Network entry #{index} must be a mapping")

        for field in REQUIRED_NETWORK_FIELDS:
            value = network.get(field)
            if not isinstance(value, str) or not value.strip():
                name = network.get("name", f"#{index}")
                raise ValueError(
                    f"Network '{name}' must define a non-empty '{field}'"
                )

        name = network["name"].strip().lower()
        if name in seen_names:
            raise ValueError(f"Duplicate network name '{name}' in config")
        seen_names.add(name)

    missing = [name for name in REQUIRED_NETWORKS if name not in seen_names]
    if missing:
        missing_names = ", ".join(missing)
        raise ValueError(f"Config is missing required network(s): {missing_names}")

    return networks


def get_network_config(config: Dict[str, Any], network_name: str) -> Dict[str, Any]:
    """
    Get a network configuration by name.

    Args:
        config: Configuration dictionary
        network_name: Network name to resolve

    Returns:
        Network configuration dictionary

    Raises:
        ValueError: If the network is not configured
    """
    target_name = network_name.strip().lower()
    for network in validate_networks(config):
        if network["name"].strip().lower() == target_name:
            return network

    raise ValueError(f"Network '{network_name}' is not configured")


def get_default_network_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the default network for non-interactive runs.

    Args:
        config: Configuration dictionary

    Returns:
        Mainnet network configuration dictionary
    """
    return get_network_config(config, "mainnet")


def get_rpc_endpoint(network_config: Dict[str, Any]) -> str:
    """
    Get RPC endpoint from config.

    Args:
        network_config: Selected network configuration dictionary

    Returns:
        RPC endpoint URL
    """
    endpoint = network_config.get("rpc_endpoint")
    if not isinstance(endpoint, str) or not endpoint.strip():
        name = network_config.get("name", "selected network")
        raise ValueError(f"Network '{name}' must define a non-empty 'rpc_endpoint'")
    return endpoint


def get_rest_endpoint(network_config: Dict[str, Any]) -> str:
    """
    Get REST API endpoint from config.

    Args:
        network_config: Selected network configuration dictionary

    Returns:
        REST API endpoint URL
    """
    endpoint = network_config.get("rest_endpoint")
    if not isinstance(endpoint, str) or not endpoint.strip():
        name = network_config.get("name", "selected network")
        raise ValueError(f"Network '{name}' must define a non-empty 'rest_endpoint'")
    return endpoint


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
