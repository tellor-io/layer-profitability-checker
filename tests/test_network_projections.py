"""
Test projected profitabilities for hypothetical extra rewards scenarios on live networks.

This module fetches real network data from palmito (testnet) and mainnet, then calculates
break-even points based on a user-supplied extra_rewards_loya_per_day.

To run:
    pytest tests/test_network_projections.py -v -s
"""

import os

import pytest

from src.apr import calculate_apr_by_stake, calculate_break_even_stake
from src.chain_data.abci_queries import TellorABCIClient
from src.chain_data.block_data import get_average_block_time
from src.chain_data.rpc_client import TellorRPCClient
from src.chain_data.tx_data import query_recent_reports
from src.module_data.staking import get_total_stake

NETWORKS = {
    "palmito": {
        "name": "Palmito (Testnet)",
        "rpc_endpoint": "https://node-palmito.tellorlayer.com/rpc",
        "rest_endpoint": "https://node-palmito.tellorlayer.com",
    },
    "mainnet": {
        "name": "Mainnet",
        "rpc_endpoint": "https://mainnet.tellorlayer.com/rpc",
        "rest_endpoint": "https://mainnet.tellorlayer.com",
    },
}

EXTRA_REWARDS_LOYA_PER_DAY = {
    "palmito": 73470000,  # 1/2 normal mint rate
    "mainnet": 73470000,  # 1/2 normal mint rate
}


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_NETWORK_TESTS") != "1",
    reason="live network projection tests are opt-in; set RUN_NETWORK_TESTS=1",
)


def fetch_network_data(network_key: str) -> dict:
    """
    Fetch real network data from a chain.

    Returns dict with:
    - total_tokens_active (in TRB)
    - avg_fee (in loya)
    - avg_block_time (in seconds)
    - median_stake (in TRB)
    - chain_id
    """
    network = NETWORKS[network_key]
    print(f"\n{'='*60}")
    print(f"FETCHING DATA FROM {network['name'].upper()}")
    print(f"{'='*60}")
    print(f"RPC Endpoint: {network['rpc_endpoint']}")
    print(f"REST Endpoint: {network['rest_endpoint']}")

    # Initialize RPC client
    rpc_client = TellorRPCClient(network["rpc_endpoint"], network["rest_endpoint"])
    abci_client = TellorABCIClient(rpc_client)

    # Get chain ID
    try:
        chain_id = rpc_client.get_chain_id()
        print(f"Chain ID: {chain_id}")
    except Exception as e:
        print(f"Error getting chain ID: {e}")
        chain_id = "unknown"

    # Get total stake data
    print("\n--- Fetching Staking Data ---")
    (
        total_tokens_active,
        total_tokens_jailed,
        total_tokens_unbonding,
        total_tokens_unbonded,
        active_count,
        jailed_count,
        unbonding_count,
        unbonded_count,
        median_stake,
        active_validator_stakes,
    ) = get_total_stake(rpc_client, abci_client)

    print(f"Total Active Stake: {total_tokens_active:,.2f} TRB")
    print(f"Active Validators: {active_count}")
    print(f"Median Stake: {median_stake:,.2f} TRB")

    # Get average block time
    print("\n--- Fetching Block Time Data ---")
    block_time_result = get_average_block_time(rpc_client)

    if block_time_result is None:
        print("WARNING: Could not get block time, using default of 2.0s")
        avg_block_time = 2.0
    else:
        avg_block_time, time_diff, block_diff = block_time_result
        print(f"Average Block Time: {avg_block_time:.2f} seconds")
        print(f"(Sampled {block_diff} blocks over {time_diff:.1f} seconds)")

    # Get average fee from recent transactions
    print("\n--- Fetching Transaction Fee Data ---")
    txs = query_recent_reports(rpc_client=rpc_client, limit=10)

    # Extract fees directly from transaction data (already parsed from block events)
    avg_fee = 0.0
    if txs and txs.get("txs"):
        tx_list = txs["txs"]
        fees = [tx.get("fee_amount", 0) for tx in tx_list if tx.get("fee_amount", 0) > 0]
        if fees:
            avg_fee = sum(fees) / len(fees)
            print(f"Average Fee: {avg_fee:.2f} loya")
            print(f"(Sampled {len(fees)} transactions with fee data)")

    if avg_fee == 0:
        print("WARNING: No fee data found, using default fee of 8 loya")
        avg_fee = 8.0

    return {
        "chain_id": chain_id,
        "total_tokens_active": total_tokens_active,  # in TRB
        "avg_fee": avg_fee,  # in loya
        "avg_block_time": avg_block_time,  # in seconds
        "median_stake": median_stake,  # in TRB
        "active_count": active_count,
    }


def calculate_break_even_for_extra_rewards(
    network_data: dict,
    extra_rewards_loya_per_day: float,
) -> dict:
    """
    Calculate break-even stake given network parameters and extra rewards rate.

    Args:
        network_data: Dict with total_tokens_active, avg_fee, avg_block_time, median_stake
        extra_rewards_loya_per_day: Extra rewards in loya per day

    Returns:
        Dict with break-even analysis results
    """
    # Convert network data to loya for calculations
    total_tokens_active_loya = network_data["total_tokens_active"] * 1e6
    median_stake_loya = network_data["median_stake"] * 1e6
    avg_fee = network_data["avg_fee"]  # already in loya
    avg_block_time = network_data["avg_block_time"]

    # Calculate blocks per day
    blocks_per_day = 86400 / avg_block_time

    # Convert extra rewards from per-day to per-block
    avg_mint_per_block = extra_rewards_loya_per_day / blocks_per_day

    # Calculate break-even stake
    break_even_stake_loya, break_even_mult = calculate_break_even_stake(
        total_tokens_active_loya,
        avg_mint_per_block,
        avg_fee,
        avg_block_time,
        median_stake_loya,
    )

    if break_even_stake_loya is None:
        return {
            "break_even_stake_trb": None,
            "break_even_mult": None,
            "error": "Could not calculate break-even (mint rate may be 0)",
        }

    break_even_stake_trb = break_even_stake_loya / 1e6

    # Calculate APR at various stake levels
    stake_levels_trb = [10, 25, 50, 100, 200, 300, 500, 1000]
    apr_results = []

    for stake_trb in stake_levels_trb:
        stake_loya = stake_trb * 1e6
        apr = calculate_apr_by_stake(
            stake_loya,
            total_tokens_active_loya,
            avg_mint_per_block,
            avg_fee,
            avg_block_time,
        )
        apr_results.append({
            "stake_trb": stake_trb,
            "apr": apr,
            "annual_yield_trb": stake_trb * (apr / 100),
        })

    # Verify APR at break-even is ~0
    apr_at_break_even = calculate_apr_by_stake(
        break_even_stake_loya,
        total_tokens_active_loya,
        avg_mint_per_block,
        avg_fee,
        avg_block_time,
    )

    return {
        "break_even_stake_trb": break_even_stake_trb,
        "break_even_mult": break_even_mult,
        "apr_at_break_even": apr_at_break_even,
        "avg_mint_per_block": avg_mint_per_block,
        "blocks_per_day": blocks_per_day,
        "apr_results": apr_results,
    }


def print_projection_results(
    network_name: str,
    network_data: dict,
    extra_rewards_loya_per_day: float,
    results: dict,
):
    """Print formatted projection results."""
    print(f"\n{'='*60}")
    print(f"BREAK-EVEN PROJECTION: {network_name.upper()}")
    print(f"{'='*60}")

    print("\n--- Network Parameters (LIVE DATA) ---")
    print(f"  Chain ID:                {network_data['chain_id']}")
    print(f"  Total Active Stake:      {network_data['total_tokens_active']:,.2f} TRB")
    print(f"  Active Validators:       {network_data['active_count']}")
    print(f"  Median Stake:            {network_data['median_stake']:,.2f} TRB")
    print(f"  Avg Fee per Report:      {network_data['avg_fee']:.2f} loya")
    print(f"  Avg Block Time:          {network_data['avg_block_time']:.2f} seconds")

    print("\n--- Hypothetical Extra Rewards ---")
    print(f"  Extra Rewards Rate:      {extra_rewards_loya_per_day:,.0f} loya/day")
    print(f"                           ({extra_rewards_loya_per_day / 1e6:,.2f} TRB/day)")
    print(f"  Blocks per Day:          ~{results['blocks_per_day']:,.0f}")
    print(f"  Avg Mint per Block:      {results['avg_mint_per_block']:,.4f} loya")

    if results.get("error"):
        print(f"\n  ERROR: {results['error']}")
        return

    print("\n--- BREAK-EVEN ANALYSIS ---")
    print(f"  Minimum Stake for Profitability: {results['break_even_stake_trb']:,.2f} TRB")
    print(f"  (This is {results['break_even_mult']:.4f}x the median stake)")
    print(f"  APR at Break-Even:               {results['apr_at_break_even']:.6f}%")

    print(f"\n{'='*60}")
    print("PROFITABILITY BY STAKE AMOUNT:")
    print(f"{'='*60}")
    print(f"{'Stake (TRB)':<15} {'APR %':<12} {'Status':<15} {'Annual Yield'}")
    print(f"{'-'*60}")

    for item in results["apr_results"]:
        stake_trb = item["stake_trb"]
        apr = item["apr"]
        annual_yield_trb = item["annual_yield_trb"]

        if apr > 0:
            status = "✓ PROFITABLE"
        elif apr > -10:
            status = "~ MARGINAL"
        else:
            status = "✗ UNPROFITABLE"

        yield_str = f"{annual_yield_trb:+,.2f} TRB/yr"
        print(f"{stake_trb:>10,.0f} TRB   {apr:>+8.1f}%    {status:<15} {yield_str}")

    print(f"{'='*60}")
    print(f"\nNOTE: Validators with stake below {results['break_even_stake_trb']:.2f} TRB")
    print("      would be losing money at these extra rewards conditions.\n")


class TestNetworkProjections:
    """Test break-even projections using live network data."""

    @pytest.mark.network
    def test_palmito_projection(self):
        """
        Fetch live data from palmito and calculate break-even with hypothetical extra rewards.
        """
        network_key = "palmito"
        extra_rewards = EXTRA_REWARDS_LOYA_PER_DAY[network_key]

        # Fetch live network data
        network_data = fetch_network_data(network_key)

        # Calculate break-even
        results = calculate_break_even_for_extra_rewards(network_data, extra_rewards)

        # Print results
        print_projection_results(
            NETWORKS[network_key]["name"],
            network_data,
            extra_rewards,
            results,
        )

        # Basic assertions
        assert network_data["total_tokens_active"] > 0, "Should have active stake"
        assert network_data["avg_block_time"] > 0, "Should have valid block time"

        if results["break_even_stake_trb"] is not None:
            assert results["break_even_stake_trb"] > 0, "Break-even should be positive"
            assert abs(results["apr_at_break_even"]) < 0.01, \
                f"APR at break-even should be ~0, got {results['apr_at_break_even']}"

    @pytest.mark.network
    def test_mainnet_projection(self):
        """
        Fetch live data from mainnet and calculate break-even with hypothetical extra rewards.
        """
        network_key = "mainnet"
        extra_rewards = EXTRA_REWARDS_LOYA_PER_DAY[network_key]

        # Fetch live network data
        network_data = fetch_network_data(network_key)

        # Calculate break-even
        results = calculate_break_even_for_extra_rewards(network_data, extra_rewards)

        # Print results
        print_projection_results(
            NETWORKS[network_key]["name"],
            network_data,
            extra_rewards,
            results,
        )

        # Basic assertions
        assert network_data["total_tokens_active"] > 0, "Should have active stake"
        assert network_data["avg_block_time"] > 0, "Should have valid block time"

        if results["break_even_stake_trb"] is not None:
            assert results["break_even_stake_trb"] > 0, "Break-even should be positive"
            assert abs(results["apr_at_break_even"]) < 0.01, \
                f"APR at break-even should be ~0, got {results['apr_at_break_even']}"

    @pytest.mark.network
    def test_both_networks_comparison(self):
        """
        Compare break-even points between palmito and mainnet with the same extra rewards rate.
        """
        print(f"\n\n{'#'*70}")
        print("# NETWORK COMPARISON: PALMITO vs MAINNET")
        print(f"{'#'*70}")

        results_by_network = {}

        for network_key in ["palmito", "mainnet"]:
            extra_rewards = EXTRA_REWARDS_LOYA_PER_DAY[network_key]

            # Fetch live network data
            network_data = fetch_network_data(network_key)

            # Calculate break-even
            results = calculate_break_even_for_extra_rewards(network_data, extra_rewards)

            # Print results
            print_projection_results(
                NETWORKS[network_key]["name"],
                network_data,
                extra_rewards,
                results,
            )

            results_by_network[network_key] = {
                "network_data": network_data,
                "results": results,
                "extra_rewards": extra_rewards,
            }

        # Print comparison summary
        print(f"\n\n{'='*70}")
        print("COMPARISON SUMMARY")
        print(f"{'='*70}")
        print(f"{'Network':<20} {'Total Stake':<15} {'Break-Even':<15} {'Blocks/Day':<15}")
        print(f"{'-'*70}")

        for network_key, data in results_by_network.items():
            network_name = NETWORKS[network_key]["name"]
            total_stake = data["network_data"]["total_tokens_active"]
            break_even = data["results"].get("break_even_stake_trb", "N/A")
            blocks_per_day = data["results"].get("blocks_per_day", "N/A")

            if isinstance(break_even, float):
                break_even_str = f"{break_even:,.2f} TRB"
            else:
                break_even_str = str(break_even)

            if isinstance(blocks_per_day, float):
                blocks_str = f"{blocks_per_day:,.0f}"
            else:
                blocks_str = str(blocks_per_day)

            print(f"{network_name:<20} {total_stake:>12,.0f} TRB  {break_even_str:<15} {blocks_str:<15}")

        print(f"{'='*70}\n")


# ==========================================
# UTILITY: Run projections with custom parameters
# ==========================================

def run_custom_projection(
    network_key: str,
    extra_rewards_loya_per_day: float,
):
    """
    Convenience function to run a projection with custom extra rewards rate.

    Usage:
        from tests.test_network_projections import run_custom_projection
        run_custom_projection("palmito", 500_000_000)  # 500 TRB/day
    """
    if network_key not in NETWORKS:
        raise ValueError(f"Unknown network: {network_key}. Must be one of: {list(NETWORKS.keys())}")

    network_data = fetch_network_data(network_key)
    results = calculate_break_even_for_extra_rewards(network_data, extra_rewards_loya_per_day)
    print_projection_results(
        NETWORKS[network_key]["name"],
        network_data,
        extra_rewards_loya_per_day,
        results,
    )
    return network_data, results


if __name__ == "__main__":
    # Run both projections when executed directly
    print("\n" + "="*70)
    print("TELLOR LAYER NETWORK PROJECTIONS")
    print("="*70)
    print("\nThis script fetches live data from palmito and mainnet,")
    print("then calculates break-even points based on hypothetical extra rewards.")
    print("\nTo modify extra rewards rates, edit EXTRA_REWARDS_LOYA_PER_DAY at the top of this file.")
    print("="*70)

    for network_key in ["palmito", "mainnet"]:
        extra_rewards = EXTRA_REWARDS_LOYA_PER_DAY[network_key]
        run_custom_projection(network_key, extra_rewards)
