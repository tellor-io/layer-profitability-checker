"""Tests for block time sampling helpers."""

from datetime import datetime, timezone
from unittest.mock import Mock

from src.chain_data.block_data import get_average_block_time


def test_get_average_block_time_samples_recent_block_timestamps():
    """Average block time uses historical block timestamps without sleeping."""
    rpc_client = Mock()
    rpc_client.get_block_height_and_timestamp.return_value = (
        1_000,
        datetime(2026, 1, 1, 0, 20, tzinfo=timezone.utc),
    )
    rpc_client.get_block_timestamp.return_value = datetime(
        2026, 1, 1, 0, 0, tzinfo=timezone.utc
    )

    avg_block_time, time_diff, block_diff = get_average_block_time(rpc_client)

    assert avg_block_time == 6.0
    assert time_diff == 1_200.0
    assert block_diff == 200
    rpc_client.get_block_timestamp.assert_called_once_with(800)


def test_get_average_block_time_uses_available_history_for_short_chains():
    """Short chains sample from block 1 instead of requesting height 0."""
    rpc_client = Mock()
    rpc_client.get_block_height_and_timestamp.return_value = (
        50,
        datetime(2026, 1, 1, 0, 1, 38, tzinfo=timezone.utc),
    )
    rpc_client.get_block_timestamp.return_value = datetime(
        2026, 1, 1, 0, 0, tzinfo=timezone.utc
    )

    avg_block_time, time_diff, block_diff = get_average_block_time(rpc_client)

    assert avg_block_time == 2.0
    assert time_diff == 98.0
    assert block_diff == 49
    rpc_client.get_block_timestamp.assert_called_once_with(1)
