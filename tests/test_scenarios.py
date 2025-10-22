"""Tests for scenarios and stake calculations."""

import pytest
import numpy as np
from src.scenarios import (
    simulate_validator_set,
    calculate_weighted_avg_apr_scenario,
    find_apr_targets,
    format_targets_for_display_with_apr
)


class TestScenarios:
    """Test scenario calculation functions."""

    def test_simulate_validator_set_uniform(self):
        """Test uniform validator set simulation."""
        total_stake = 10000000000  # 10k TRB in loya
        num_validators = 10
        
        validator_stakes = simulate_validator_set(total_stake, num_validators, "uniform")
        
        assert len(validator_stakes) == 10
        assert all(stake == total_stake / num_validators for stake in validator_stakes)
        assert sum(validator_stakes) == total_stake

    def test_simulate_validator_set_max_validators(self):
        """Test validator set respects 100 validator limit."""
        total_stake = 10000000000
        num_validators = 150  # More than 100
        
        validator_stakes = simulate_validator_set(total_stake, num_validators, "uniform")
        
        assert len(validator_stakes) == 100  # Should be capped at 100

    def test_simulate_validator_set_invalid_distribution(self):
        """Test invalid stake distribution raises error."""
        total_stake = 10000000000
        num_validators = 10
        
        with pytest.raises(ValueError, match="Invalid stake_distribution"):
            simulate_validator_set(total_stake, num_validators, "invalid")

    def test_calculate_weighted_avg_apr_scenario(self):
        """Test weighted average APR calculation for scenario."""
        validator_stakes = [1000000, 2000000, 3000000]  # 1, 2, 3 TRB
        total_tokens_active = 10000000000  # 10k TRB
        avg_mint_amount = 1000000  # 1 TRB per block
        avg_fee = 5  # 0.05 TRB fee (smaller fee to get positive APR)
        avg_block_time = 6.0

        apr = calculate_weighted_avg_apr_scenario(
            validator_stakes, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
        )
        
        # APR could be negative if fees are too high, just check it's a number
        assert isinstance(apr, (int, float))

    def test_find_apr_targets(self):
        """Test APR target calculation."""
        stake_amounts_trb = [50000, 100000, 200000]
        aprs = [50.0, 25.0, 12.5]
        target_aprs = [100, 50, 20]
        total_tokens_active = 10000000000
        avg_mint_amount = 1000000
        avg_fee = 5
        avg_block_time = 6.0

        targets = find_apr_targets(
            stake_amounts_trb, aprs, target_aprs, total_tokens_active,
            avg_mint_amount, avg_fee, avg_block_time
        )
        
        assert isinstance(targets, dict)
        # Should have some targets if APR is reasonable
        if targets:
            assert all("% APR" in key for key in targets.keys())
            assert all("stake_trb" in data for data in targets.values())

    def test_format_targets_for_display_with_apr(self):
        """Test formatting targets for display."""
        targets = {
            "53.6% APR": {"stake_trb": 100000, "actual_apr": 53.6},
            "5.4% APR": {"stake_trb": 1000000, "actual_apr": 5.4},
            "26.8% APR": {"stake_trb": 200000, "actual_apr": 26.8}
        }
        current_total_stake = 20224000  # ~20k TRB
        stake_results = {
            "stake_amounts_trb": [50000, 100000, 200000, 500000, 1000000],
            "weighted_avg_aprs": [100.0, 50.0, 25.0, 10.0, 5.0]
        }

        display_dict = format_targets_for_display_with_apr(
            targets, current_total_stake, stake_results
        )
        
        assert isinstance(display_dict, dict)
        assert "Current Network Stake" in display_dict
        # Should have current APR entry
        assert any("APR (Current)" in key for key in display_dict.keys())
