"""Tests for configuration network selection."""

import pytest

from src.config import (
    get_default_network_config,
    get_network_config,
    get_rest_endpoint,
    get_rpc_endpoint,
    validate_networks,
)


def test_validate_networks_accepts_mainnet_and_testnet(sample_config):
    networks = validate_networks(sample_config)

    assert [network["name"] for network in networks] == ["mainnet", "testnet"]


def test_validate_networks_rejects_missing_networks():
    with pytest.raises(ValueError, match="networks"):
        validate_networks({})


def test_validate_networks_rejects_missing_required_endpoint(sample_config):
    del sample_config["networks"][0]["rest_endpoint"]

    with pytest.raises(ValueError, match="rest_endpoint"):
        validate_networks(sample_config)


def test_get_network_config_resolves_mainnet_and_testnet(sample_config):
    mainnet = get_network_config(sample_config, "mainnet")
    testnet = get_network_config(sample_config, "testnet")

    assert get_rpc_endpoint(mainnet) == "https://mainnet.tellorlayer.com/rpc"
    assert get_rest_endpoint(testnet) == "https://node-palmito.tellorlayer.com"


def test_get_default_network_config_uses_mainnet(sample_config):
    network = get_default_network_config(sample_config)

    assert network["name"] == "mainnet"


def test_get_default_network_config_requires_mainnet(sample_config):
    sample_config["networks"] = [
        network
        for network in sample_config["networks"]
        if network["name"] != "mainnet"
    ]

    with pytest.raises(ValueError, match="mainnet"):
        get_default_network_config(sample_config)
