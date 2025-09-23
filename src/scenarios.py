import matplotlib.pyplot as plt
import numpy as np

from .apr import calculate_apr_by_stake

# Set random seed for reproducible results
np.random.seed(42)


def simulate_validator_set(
    total_stake, num_validators=100, stake_distribution="uniform"
):
    """
    Simulate a validator set with uniform stake distribution
    Fixed at 100 validators max for Tellor Layer

    Args:
        total_stake: Total stake in the network (loya)
        num_validators: Number of validators (fixed at 100)
        stake_distribution: 'uniform' (only option)

    Returns:
        List of stake amounts for each validator
    """
    # Ensure we never exceed 100 validators
    num_validators = min(num_validators, 100)

    if stake_distribution == "uniform":
        # Equal stake distribution
        stake_per_validator = total_stake / num_validators
        return [stake_per_validator] * num_validators

    else:
        raise ValueError("Invalid stake_distribution. Use 'uniform'")


def calculate_weighted_avg_apr_scenario(
    validator_stakes, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
):
    """Calculate weighted average APR for a given validator set scenario"""
    total_weighted_apr = 0.0
    total_power = 0

    for stake in validator_stakes:
        if stake > 0:
            apr = calculate_apr_by_stake(
                stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
            )
            total_weighted_apr += apr * stake
            total_power += stake

    if total_power == 0:
        return 0.0

    return total_weighted_apr / total_power


def generate_stake_amount_scenarios(
    base_total_stake, avg_mint_amount, avg_fee, avg_block_time
):
    """Generate scenarios for varying total stake amounts using pure mathematical calculations"""

    # Stake amounts from 0 to 2 million TRB (converted to loya)
    stake_amounts_trb = np.linspace(
        100, 2000000, 1000
    )  # Start at 100 TRB to avoid division by zero
    stake_amounts = stake_amounts_trb * 1e6  # Convert TRB to loya

    # Calculate blocks per year
    blocks_per_year = (365 * 24 * 3600) / avg_block_time

    # Calculate reporting frequency (every other block)
    reports_per_block = 0.5
    reports_per_year = blocks_per_year * reports_per_block

    # Convert TRB inputs to loya for calculations
    avg_mint_amount_loya = avg_mint_amount * 1e6
    avg_fee_loya = avg_fee * 1e6

    # Total mint per year (TBR)
    total_mint_per_year = avg_mint_amount_loya * blocks_per_year

    # Total fees per year (reporting every other block)
    total_fees_per_year = avg_fee_loya * reports_per_year

    # Calculate APR for each total stake level
    weighted_avg_aprs = []

    for total_stake in stake_amounts:
        # APR = (total_mint_per_year - total_fees_per_year) / total_stake * 100
        # This gives the APR that any validator would get at this total stake level
        net_rewards_per_year = total_mint_per_year - total_fees_per_year
        apr = (net_rewards_per_year / total_stake) * 100
        weighted_avg_aprs.append(apr)

    results = {
        "stake_amounts": stake_amounts,
        "stake_amounts_trb": stake_amounts_trb,
        "weighted_avg_aprs": weighted_avg_aprs,
    }

    return results


def find_apr_targets(
    stake_amounts_trb,
    aprs,
    target_aprs,
    total_tokens_active,
    avg_mint_amount,
    avg_fee,
    avg_block_time,
):
    """Calculate APR projections at different total stake levels using pure mathematical calculations"""
    targets = {}

    # Calculate blocks per year
    blocks_per_year = (365 * 24 * 3600) / avg_block_time

    # Calculate reporting frequency (every other block)
    reports_per_block = 0.5
    reports_per_year = blocks_per_year * reports_per_block

    # Convert TRB inputs to loya for calculations
    avg_mint_amount_loya = avg_mint_amount * 1e6
    avg_fee_loya = avg_fee * 1e6

    # Total mint per year (TBR)
    total_mint_per_year = avg_mint_amount_loya * blocks_per_year

    # Total fees per year (reporting every other block)
    total_fees_per_year = avg_fee_loya * reports_per_year

    # Define meaningful total stake levels to show APR projections
    total_stake_levels_trb = [
        50000,
        100000,
        200000,
        500000,
        1000000,
        2000000,
        5000000,
        10000000,
    ]

    for total_stake_trb in total_stake_levels_trb:
        total_stake_loya = total_stake_trb * 1e6  # Convert to loya

        # Calculate APR for a validator at this total stake level
        # APR = (total_mint_per_year - total_fees_per_year) / total_stake * 100
        # This gives the APR that any validator would get at this total stake level

        net_rewards_per_year = total_mint_per_year - total_fees_per_year
        apr = (net_rewards_per_year / total_stake_loya) * 100

        # Show raw APR numbers for each stake level
        if apr > 0 and apr < 1000:  # Cap at 1000% to avoid extreme values
            targets[f"{apr:.1f}% APR"] = {
                "stake_trb": total_stake_trb,
                "actual_apr": apr,
            }

    return targets


def plot_stake_scenarios(
    results, base_total_stake, avg_mint_amount, avg_fee, avg_block_time
):
    """Plot average APR vs total stake amount"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    target_aprs = [100, 50, 20, 10, 5, 2, 1]

    # Set x-axis ticks
    x_ticks = np.arange(0, 2500000, 500000)
    x_tick_labels = [
        f"{int(x / 1000)}k" if x < 1000000 else f"{int(x / 1000000)}M" for x in x_ticks
    ]

    # Current stake line
    current_stake_trb = base_total_stake * 1e-6

    # Plot Average APR
    stake_amounts_trb = results["stake_amounts_trb"]
    aprs = results["weighted_avg_aprs"]

    ax.plot(
        stake_amounts_trb, aprs, color="blue", linewidth=2, label="Uniform Distribution"
    )

    # Add target points using mathematical calculation
    targets = find_apr_targets(
        stake_amounts_trb,
        aprs,
        target_aprs,
        base_total_stake,
        avg_mint_amount,
        avg_fee,
        avg_block_time,
    )
    for target_apr, target_data in targets.items():
        ax.plot(target_data["stake_trb"], target_data["actual_apr"], "ko", markersize=6)
        stake_k = target_data["stake_trb"] / 1000
        ax.annotate(
            f"{target_apr}%\n({stake_k:.0f}k)",
            xy=(target_data["stake_trb"], target_data["actual_apr"]),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=8,
            ha="center",
            bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "alpha": 0.8},
        )

    ax.set_xlabel("Total Network Stake (TRB)")
    ax.set_ylabel("Avg APR (%)")
    ax.set_title("Network APR vs Total Stake Amount")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_tick_labels)
    ax.set_ylim(-50, 400)
    if current_stake_trb <= 2000000:
        ax.axvline(
            x=current_stake_trb,
            color="black",
            linestyle="--",
            alpha=0.5,
            label="Current Stake",
        )
        ax.legend()

    plt.tight_layout()
    plt.savefig("apr_by_total_stake.png", dpi=300, bbox_inches="tight")
    print("Generated apr_by_total_stake.png")
    print("\n")
    print("assuming a uniform distribution...")

    return targets


def run_scenarios_analysis(
    total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
):
    """Run stake amount scenarios analysis and generate plots"""

    # Generate stake amount scenarios
    stake_results = generate_stake_amount_scenarios(
        total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
    )
    targets = plot_stake_scenarios(
        stake_results, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
    )

    return stake_results, targets


def format_targets_for_display_with_apr(targets, current_total_stake, stake_results):
    """Format target APR points for display in main.py info box including current APR"""
    # current_total_stake is already in TRB
    current_stake_trb = current_total_stake

    display_dict = {}

    # Add current stake info first
    display_dict["Current Network Stake"] = f"{current_stake_trb:,.0f} TRB"

    # Calculate APR at current stake level by interpolating from results
    try:
        stake_amounts_trb = stake_results["stake_amounts_trb"]
        aprs = stake_results["weighted_avg_aprs"]

        # Ensure we have valid data
        if (
            len(stake_amounts_trb) > 0
            and len(aprs) > 0
            and len(stake_amounts_trb) == len(aprs)
        ):
            # Find the APR at current stake level using interpolation
            current_apr = np.interp(current_stake_trb, stake_amounts_trb, aprs)

            # Add current APR
            display_dict[f"{current_apr:.1f}% APR (Current)"] = (
                f"{current_stake_trb:,.0f} TRB"
            )
        else:
            # Fallback if data is invalid
            display_dict["Current APR"] = "Unable to calculate"
    except Exception:
        # Fallback if interpolation fails
        display_dict["Current APR"] = "Unable to calculate"

    # Add target points in descending order
    sorted_targets = sorted(targets.items(), key=lambda x: x[0], reverse=True)

    for target_apr, data in sorted_targets:
        stake_trb = data["stake_trb"]

        # Format stake amount with appropriate units and commas
        if stake_trb >= 1000000:
            # For millions, show as "1.3M TRB" format
            stake_str = f"{stake_trb / 1000000:.1f}M TRB"
        elif stake_trb >= 1000:
            # For thousands, show as "17k TRB" format
            stake_str = f"{stake_trb / 1000:.0f}k TRB"
        else:
            # For small numbers, show with commas
            stake_str = f"{stake_trb:,.0f} TRB"

        display_dict[target_apr] = stake_str

    return display_dict
