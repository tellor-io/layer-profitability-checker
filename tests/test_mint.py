"""Tests for mint module functionality."""

import pytest
from src.module_data.mint import Minter, DAILY_MINT_RATE, MILLISECONDS_IN_DAY


class TestMinter:
    """Test Minter class functionality."""

    def test_minter_initialization(self):
        """Test Minter initialization."""
        minter = Minter()
        assert minter.bond_denom == "loya"
        assert minter.previous_block_time is None

    def test_minter_custom_denom(self):
        """Test Minter with custom denomination."""
        minter = Minter("custom")
        assert minter.bond_denom == "custom"

    def test_calculate_block_provision_basic(self):
        """Test basic block provision calculation."""
        minter = Minter()
        time_diff = 6  # 6 seconds
        
        mint_amount = minter.calculate_block_provision(time_diff)
        
        # Should calculate based on daily mint rate
        expected = DAILY_MINT_RATE * (time_diff * 1000) // MILLISECONDS_IN_DAY
        assert mint_amount == expected
        assert mint_amount > 0

    def test_calculate_block_provision_zero_time(self):
        """Test block provision with zero time difference."""
        minter = Minter()
        
        with pytest.raises(ValueError, match="time_diff 0 cannot be negative"):
            minter.calculate_block_provision(0)

    def test_calculate_block_provision_negative_time(self):
        """Test block provision with negative time difference."""
        minter = Minter()
        
        with pytest.raises(ValueError, match="time_diff -1 cannot be negative"):
            minter.calculate_block_provision(-1)

    def test_calculate_block_provision_large_time(self):
        """Test block provision with large time difference."""
        minter = Minter()
        time_diff = 86400  # 1 day in seconds
        
        mint_amount = minter.calculate_block_provision(time_diff)
        
        # Should be approximately the daily mint rate
        assert mint_amount == DAILY_MINT_RATE

    def test_validate_success(self):
        """Test validation with proper values."""
        minter = Minter()
        minter.previous_block_time = 1234567890
        
        # Should not raise any exception
        minter.validate()

    def test_validate_no_previous_time(self):
        """Test validation without previous block time."""
        minter = Minter()
        
        with pytest.raises(ValueError, match="previous block time cannot be None"):
            minter.validate()

    def test_validate_empty_denom(self):
        """Test validation with empty denomination."""
        minter = Minter("")
        minter.previous_block_time = 1234567890
        
        with pytest.raises(ValueError, match="bond denom should not be empty string"):
            minter.validate()


class TestMintConstants:
    """Test mint module constants."""

    def test_daily_mint_rate(self):
        """Test daily mint rate constant."""
        assert DAILY_MINT_RATE > 0
        assert isinstance(DAILY_MINT_RATE, int)

    def test_milliseconds_in_day(self):
        """Test milliseconds in day constant."""
        assert MILLISECONDS_IN_DAY == 24 * 60 * 60 * 1000
        assert isinstance(MILLISECONDS_IN_DAY, int)
