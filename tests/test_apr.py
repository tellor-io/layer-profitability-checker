"""Tests for APR calculation functions."""

import pytest

from src.apr import (
    calculate_apr_avgs,
    calculate_apr_by_stake,
    calculate_break_even_stake,
    calculate_reporter_aprs,
    calculate_stake_profit_projection,
    parse_commission_rate_percent,
    reporter_reward_pool,
    validator_reward_pool,
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

    def test_break_even_matches_zero_apr(self):
        """Break-even stake should be the exact point where projected APR is zero."""
        total_tokens_active = 26_411.4
        avg_reporter_rewards_per_block = 0.0013319
        avg_fee = 0.0000062
        avg_block_time = 2.17
        median_stake = 1_780.8

        break_even_stake, _ = calculate_break_even_stake(
            total_tokens_active,
            avg_reporter_rewards_per_block,
            avg_fee,
            avg_block_time,
            median_stake,
        )

        apr = calculate_apr_by_stake(
            break_even_stake,
            total_tokens_active,
            avg_reporter_rewards_per_block,
            avg_fee,
            avg_block_time,
        )

        assert break_even_stake == pytest.approx(61.49, rel=0.001)
        assert apr == pytest.approx(0.0, abs=1e-9)

    def test_specific_stake_projection_above_break_even(self):
        """A 125 TRB stake is profitable under the observed mainnet-style sample."""
        projection = calculate_stake_profit_projection(
            125.0,
            26_411.4,
            0.0013319,
            0.0000062,
            2.17,
        )

        assert projection["profit_per_year"] == pytest.approx(46.7, rel=0.02)
        assert projection["apr"] == pytest.approx(37.4, rel=0.02)
        assert projection["profit_per_year"] > 0

    def test_reporter_and_validator_reward_split(self):
        """Tellor reward events emit total rewards; reporter APR uses the 75% pool."""
        total_reward = 100

        assert reporter_reward_pool(total_reward) == 75
        assert validator_reward_pool(total_reward) == 25

    def test_parse_commission_rate_percent(self):
        """Support both decimal strings and Cosmos LegacyDec integer strings."""
        assert parse_commission_rate_percent("0.05") == pytest.approx(5.0)
        assert parse_commission_rate_percent("50000000000000000") == pytest.approx(5.0)
        assert parse_commission_rate_percent("") == 0.0

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
        assert reporter_aprs[0]["commission_rate"] == pytest.approx(5.0)
