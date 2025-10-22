"""Test configuration and fixtures for profitability checker tests."""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_rpc_client():
    """Create a mock RPC client with basic responses."""
    mock_client = Mock()

    # Mock basic RPC responses
    mock_client.get_chain_id.return_value = "tellor-layer-testnet"
    mock_client.rpc_endpoint = "http://localhost:26657"

    return mock_client


@pytest.fixture
def mock_abci_client():
    """Create a mock ABCI client."""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "rpc_endpoint": "http://localhost:26657",
        "account_address": "tellor1test123456789",
        "rest_endpoint": "http://localhost:1317",
    }


@pytest.fixture
def mock_stake_data():
    """Mock stake data for testing."""
    return (
        20224000000000,  # total_tokens_active (loya)
        0,  # total_tokens_jailed
        0,  # total_tokens_unbonding
        0,  # total_tokens_unbonded
        10,  # active_count
        0,  # jailed_count
        0,  # unbonding_count
        0,  # unbonded_count
        2022400000000,  # median_stake (loya)
        [2022400000000] * 10,  # active_validator_stakes
    )


@pytest.fixture
def mock_mint_events_data():
    """Mock mint events data for testing."""
    return {
        "total_tbr_minted": 1000000000,  # 1000 TRB in loya
        "total_extra_rewards": 500000000,  # 500 TRB in loya
        "tbr_event_count": 10,
        "extra_rewards_event_count": 5,
    }


@pytest.fixture
def mock_reporter_data():
    """Mock reporter data for testing."""
    return {
        "reporters": [
            {
                "address": "tellor1reporter1",
                "stake": 2022400000000,  # 2022.4 TRB in loya
                "status": "active",
            },
            {
                "address": "tellor1reporter2",
                "stake": 1011200000000,  # 1011.2 TRB in loya
                "status": "active",
            },
        ],
        "summary": {
            "total_reporters": "2",
            "active_reporters": "2",
            "total_stake": "3,033.6 TRB",
            "avg_stake": "1,516.8 TRB",
        },
    }
