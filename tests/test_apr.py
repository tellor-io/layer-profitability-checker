"""Tests for APR calculation functions."""

import pytest

from src.apr import (
    calculate_apr_avgs,
    calculate_apr_by_stake,
    calculate_break_even_stake,
    calculate_reporter_aprs,
)


class TestAPRCalculations:
    """Test APR calculation functions."""

    def test_calculate_apr_by_stake_basic(self):
        """Test basic APR calculation."""
        stake = 1000000  # 1 TRB in loya
        total_tokens_active = 10000000000  # 10k TRB in loya
        avg_mint_amount = 1000000  # 1 TRB per block in loya
        avg_fee = 5
        avg_block_time = 2.0  # 2 seconds per block

        apr = calculate_apr_by_stake(
            stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
        )

        # Should return a reasonable APR (could be negative if fees are too high)
        print("apr: ", apr)
        assert isinstance(apr, (int, float))
        assert apr > 0

    def test_calculate_apr_by_stake_zero_stake(self):
        """Test APR calculation with zero stake."""
        stake = 0
        total_tokens_active = 10000000000
        avg_mint_amount = 1000000
        avg_fee = 100000
        avg_block_time = 6.0

        # Should handle zero stake gracefully - expect division by zero
        with pytest.raises(ZeroDivisionError):
            calculate_apr_by_stake(
                stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
            )

    def test_calculate_apr_avgs(self):
        """Test APR averages calculation."""
        reporter_aprs = [
            {"address": "addr1", "apr": 10.5, "power_trb": 1000000},
            {"address": "addr2", "apr": 15.2, "power_trb": 2000000},
            {"address": "addr3", "apr": 8.7, "power_trb": 500000},
        ]

        weighted_avg, median = calculate_apr_avgs(reporter_aprs)

        assert weighted_avg > 0
        print("weighted_avg: ", weighted_avg)
        assert median > 0
        print("median: ", median)
        assert weighted_avg != median  # Should be different values

    def test_calculate_break_even_stake(self):
        """Test break-even stake calculation."""
        total_tokens_active = 10000000000  # 10k TRB
        avg_mint_amount = 1000000  # 1 TRB per block
        avg_fee = 100000  # 0.1 TRB fee
        avg_block_time = 2.0
        median_stake = 1000000  # 1 TRB

        break_even_stake, break_even_mult = calculate_break_even_stake(
            total_tokens_active, avg_mint_amount, avg_fee, avg_block_time, median_stake
        )

        print("break_even_stake: ", break_even_stake)
        print("break_even_mult: ", break_even_mult)
        if break_even_stake is not None:
            assert break_even_stake > 0
            assert break_even_mult > 0

    def test_calculate_reporter_aprs(self):
        """Test reporter APR calculations."""
        reporters = {
            "active": [
                {
                    "address": "addr1",
                    "power": "1000000",
                    "moniker": "test1",
                    "commission_rate": "0.1",
                },
                {
                    "address": "addr2",
                    "power": "2000000",
                    "moniker": "test2",
                    "commission_rate": "0.05",
                },
            ]
        }
        total_tokens_active = 10000000000
        avg_mint_amount = 1000000
        avg_fee = 100000
        avg_block_time = 6.0

        reporter_aprs = calculate_reporter_aprs(
            reporters, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
        )

        print("reporter_aprs: ", reporter_aprs)
        assert len(reporter_aprs) == 2
        assert all("apr" in reporter for reporter in reporter_aprs)
        assert all("power_trb" in reporter for reporter in reporter_aprs)
