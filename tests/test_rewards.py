"""Tests for reward event sampling."""

from unittest.mock import Mock

from src.rewards import query_mint_events


def test_query_mint_events_reports_sampled_block_count():
    """Reward projections should know the block window, not only event count."""
    rpc_client = Mock()
    rpc_client.get_block_results.side_effect = [
        {
            "result": {
                "finalize_block_events": [
                    {
                        "type": "extra_rewards_distributed",
                        "attributes": [
                            {"key": "total_amount", "value": "300loya"},
                        ],
                    }
                ]
            }
        },
        {"result": {"finalize_block_events": []}},
        {
            "result": {
                "finalize_block_events": [
                    {
                        "type": "extra_rewards_distributed",
                        "attributes": [
                            {"key": "total_amount", "value": "600loya"},
                        ],
                    }
                ]
            }
        },
    ]

    result = query_mint_events(start_height=10, end_height=12, rpc_client=rpc_client)

    assert result["sampled_block_count"] == 3
    assert result["extra_rewards_event_count"] == 2
    assert result["total_extra_rewards"] == 900
