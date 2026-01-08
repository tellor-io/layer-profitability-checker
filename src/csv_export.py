"""CSV export functions for profitability checker data"""

import csv
import os
from datetime import datetime


def ensure_data_directory():
    """Create data directory if it doesn't exist"""
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


def export_time_based_rewards(
    data_source,
    total_tbr_sample,
    num_blocks_sampled,
    avg_inflationary_rewards_per_block,
    avg_extra_rewards_per_block,
    projected_daily_tbr,
    projected_annual_tbr,
):
    """
    Export time-based rewards data to CSV
    Args:
        data_source: Source of the data (e.g., "Event-based")
        total_tbr_sample: Total TBR from sample period in TRB
        num_blocks_sampled: Number of blocks sampled for the analysis
        avg_inflationary_rewards_per_block: Average inflationary rewards per block in loya
        avg_extra_rewards_per_block: Average extra rewards per block in loya
        projected_daily_tbr: Projected daily TBR in TRB
        projected_annual_tbr: Projected annual TBR in TRB
    """
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, "time_based_rewards.csv")

    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline="") as csvfile:
        fieldnames = [
            "timestamp",
            "data_source",
            "total_tbr_sample_window_(trb)",
            "num_blocks_sampled",
            "inflationary_rewards_per_block_(loya)",
            "extra_rewards_per_block_(loya)",
            "projected_daily_tbr_(trb)",
            "projected_annual_tbr_(trb)",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(),
                "data_source": data_source,
                "total_tbr_sample_window_(trb)": f"{total_tbr_sample:.2f}",
                "num_blocks_sampled": f"{num_blocks_sampled}",
                "inflationary_rewards_per_block_(loya)": f"{avg_inflationary_rewards_per_block:.1f}",
                "extra_rewards_per_block_(loya)": f"{avg_extra_rewards_per_block:.1f}",
                "projected_daily_tbr_(trb)": f"{projected_daily_tbr:.0f}",
                "projected_annual_tbr_(trb)": f"{projected_annual_tbr:.0f}",
            }
        )


def export_reporting_costs(
    avg_gas_wanted,
    avg_gas_used,
    min_gas_price,
    avg_gas_cost,
    avg_fee_paid,
    blocks_per_day,
    reports_per_day,
    daily_fee_cost,
    monthly_fee_cost,
    yearly_fee_cost,
):
    """
    Export reporting costs data to CSV

    Args:
        avg_gas_wanted: Average gas wanted
        avg_gas_used: Average gas used
        min_gas_price: Minimum gas price in loya
        avg_gas_cost: Average gas cost in loya
        avg_fee_paid: Average fee paid in LOYA
        blocks_per_day: Estimated blocks per day
        reports_per_day: Estimated reports per day
        daily_fee_cost: Daily fee cost in TRB
        monthly_fee_cost: Monthly fee cost in TRB
        yearly_fee_cost: Yearly fee cost in TRB
    """
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, "reporting_costs.csv")

    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline="") as csvfile:
        fieldnames = [
            "timestamp",
            "avg_gas_wanted",
            "avg_gas_used",
            "min_gas_price_loya",
            "avg_gas_cost_loya",
            "avg_fee_paid_loya",
            "blocks_per_day",
            "reports_per_day",
            "daily_fee_cost_trb",
            "monthly_fee_cost_trb",
            "yearly_fee_cost_trb",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(),
                "avg_gas_wanted": f"{avg_gas_wanted:.0f}",
                "avg_gas_used": f"{avg_gas_used:.0f}",
                "min_gas_price_loya": f"{min_gas_price:.6f}",
                "avg_gas_cost_loya": f"{avg_gas_cost:.4f}",
                "avg_fee_paid_loya": f"{avg_fee_paid:.1f}",
                "blocks_per_day": f"{blocks_per_day:.0f}",
                "reports_per_day": f"{reports_per_day:.0f}",
                "daily_fee_cost_trb": f"{daily_fee_cost:.4f}",
                "monthly_fee_cost_trb": f"{monthly_fee_cost:.1f}",
                "yearly_fee_cost_trb": f"{yearly_fee_cost:.1f}",
            }
        )


def export_user_tip_totals(total_tips_all_time, user_tip_totals):
    """
    Export user tip totals data to CSV

    Args:
        total_tips_all_time: Total tips all time in TRB
        user_tip_totals: List of tuples (address, total_tips_trb)
    """
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, "user_tip_totals.csv")

    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline="") as csvfile:
        # Create fieldnames dynamically based on number of top users we want to track
        # We'll track the top 10 users
        fieldnames = ["timestamp", "total_tips_all_time"]
        for i in range(1, 11):  # Top 10 users
            fieldnames.extend([f"top_{i}_address", f"top_{i}_tips_trb"])

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        row_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tips_all_time": f"{total_tips_all_time:.5f}",
        }

        # Add top 10 users (or fewer if not available)
        for i in range(1, 11):
            if i <= len(user_tip_totals):
                address, tips = user_tip_totals[i - 1]
                row_data[f"top_{i}_address"] = address
                row_data[f"top_{i}_tips_trb"] = f"{tips:.5f}"
            else:
                row_data[f"top_{i}_address"] = ""
                row_data[f"top_{i}_tips_trb"] = ""

        writer.writerow(row_data)


def export_validator_profitability(
    avg_stake_per_block,
    avg_stake_per_minute,
    avg_stake_per_hour,
    avg_stake_per_day,
    avg_stake_per_month,
    avg_stake_per_year,
    median_stake_per_block,
    median_stake_per_minute,
    median_stake_per_hour,
    median_stake_per_day,
    median_stake_per_month,
    median_stake_per_year,
):
    """
    Export validator profitability projections to CSV

    Args:
        All arguments are profit values in TRB for different time periods
    """
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, "validator_profitability.csv")

    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline="") as csvfile:
        fieldnames = [
            "timestamp",
            "avg_stake_per_block",
            "avg_stake_per_minute",
            "avg_stake_per_hour",
            "avg_stake_per_day",
            "avg_stake_per_month",
            "avg_stake_per_year",
            "median_stake_per_block",
            "median_stake_per_minute",
            "median_stake_per_hour",
            "median_stake_per_day",
            "median_stake_per_month",
            "median_stake_per_year",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(),
                "avg_stake_per_block": f"{avg_stake_per_block:.6f}",
                "avg_stake_per_minute": f"{avg_stake_per_minute:.6f}",
                "avg_stake_per_hour": f"{avg_stake_per_hour:.1f}",
                "avg_stake_per_day": f"{avg_stake_per_day:.1f}",
                "avg_stake_per_month": f"{avg_stake_per_month:.1f}",
                "avg_stake_per_year": f"{avg_stake_per_year:.0f}",
                "median_stake_per_block": f"{median_stake_per_block:.6f}",
                "median_stake_per_minute": f"{median_stake_per_minute:.6f}",
                "median_stake_per_hour": f"{median_stake_per_hour:.1f}",
                "median_stake_per_day": f"{median_stake_per_day:.1f}",
                "median_stake_per_month": f"{median_stake_per_month:.1f}",
                "median_stake_per_year": f"{median_stake_per_year:.0f}",
            }
        )


def export_current_reporter_aprs(weighted_avg_apr, median_apr):
    """
    Export current reporter APRs to CSV

    Args:
        weighted_avg_apr: Weighted average APR percentage
        median_apr: Median APR percentage
    """
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, "current_reporter_aprs.csv")

    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline="") as csvfile:
        fieldnames = ["timestamp", "weighted_avg_apr", "median_apr"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(),
                "weighted_avg_apr": f"{weighted_avg_apr:.2f}",
                "median_apr": f"{median_apr:.2f}",
            }
        )


def export_apr_by_total_stake(current_network_stake, current_apr, stake_results):
    """
    Export APR by total stake scenarios to CSV

    Args:
        current_network_stake: Current network stake in TRB
        current_apr: Current APR percentage
        stake_results: Dictionary containing stake scenario results
    """
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, "apr_by_total_stake.csv")

    file_exists = os.path.isfile(filepath)

    # Define the specific stake levels we want to track
    target_stakes = [50000, 100000, 200000, 500000, 1000000, 2000000, 5000000, 10000000]

    with open(filepath, "a", newline="") as csvfile:
        fieldnames = ["timestamp", "current_network_stake", "current_apr"]

        # Add fieldnames for each target stake level
        for stake in target_stakes:
            if stake >= 1000000:
                stake_label = f"{stake / 1000000:.1f}M"
            else:
                stake_label = f"{stake / 1000:.0f}k"
            fieldnames.append(f"apr_at_{stake_label}_trb")

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        row_data = {
            "timestamp": datetime.now().isoformat(),
            "current_network_stake": f"{current_network_stake:.0f}",
            "current_apr": f"{current_apr:.1f}",
        }

        # Calculate APR for each target stake level
        import numpy as np

        stake_amounts_trb = stake_results["stake_amounts_trb"]
        aprs = stake_results["weighted_avg_aprs"]

        for stake in target_stakes:
            if stake >= 1000000:
                stake_label = f"{stake / 1000000:.1f}M"
            else:
                stake_label = f"{stake / 1000:.0f}k"

            # Interpolate APR at this stake level
            apr_at_stake = np.interp(stake, stake_amounts_trb, aprs)
            row_data[f"apr_at_{stake_label}_trb"] = f"{apr_at_stake:.1f}"

        writer.writerow(row_data)


def export_network_profitability_summary(
    current_network_stake,
    current_apr,
    projected_annual_tbr,
    yearly_fee_cost,
    weighted_avg_apr,
    median_apr,
):
    """
    Export network profitability summary - the key metrics for tracking profitability over time

    Args:
        current_network_stake: Current total network stake in TRB
        current_apr: Current APR percentage at network stake level
        projected_annual_tbr: Projected annual time-based rewards in TRB
        yearly_fee_cost: Yearly fee cost in TRB
        weighted_avg_apr: Weighted average APR of all reporters
        median_apr: Median APR of all reporters
    """
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, "network_profitability_summary.csv")

    file_exists = os.path.isfile(filepath)

    # Calculate net annual profitability
    net_annual_profitability = projected_annual_tbr - yearly_fee_cost

    with open(filepath, "a", newline="") as csvfile:
        fieldnames = [
            "timestamp",
            "current_network_stake_trb",
            "current_apr_percent",
            "weighted_avg_apr_percent",
            "median_apr_percent",
            "projected_annual_tbr",
            "yearly_fee_cost_trb",
            "net_annual_profitability_trb",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(),
                "current_network_stake_trb": f"{current_network_stake:.0f}",
                "current_apr_percent": f"{current_apr:.1f}",
                "weighted_avg_apr_percent": f"{weighted_avg_apr:.2f}",
                "median_apr_percent": f"{median_apr:.2f}",
                "projected_annual_tbr": f"{projected_annual_tbr:.0f}",
                "yearly_fee_cost_trb": f"{yearly_fee_cost:.1f}",
                "net_annual_profitability_trb": f"{net_annual_profitability:.0f}",
            }
        )


def export_all_data(
    tbr_data,
    reporting_costs_data,
    user_tips_data,
    profitability_data,
    apr_data,
    stake_scenario_data,
):
    """
    Export all profitability data to CSV files

    Args:
        tbr_data: Dict with time-based rewards data
        reporting_costs_data: Dict with reporting costs data
        user_tips_data: Dict with user tip totals data
        profitability_data: Dict with validator profitability data
        apr_data: Dict with current reporter APR data
        stake_scenario_data: Dict with APR by total stake data
    """
    print("\nExporting data to CSV files...")

    # Export network profitability summary (the most important metrics)
    export_network_profitability_summary(
        stake_scenario_data["current_network_stake"],
        stake_scenario_data["current_apr"],
        tbr_data["projected_annual_tbr"],
        reporting_costs_data["yearly_fee_cost"],
        apr_data["weighted_avg_apr"],
        apr_data["median_apr"],
    )
    print("  ✓ Exported network profitability summary")

    # Export time-based rewards
    export_time_based_rewards(
        tbr_data["data_source"],
        tbr_data["total_tbr_sample"],
        tbr_data["num_blocks_sampled"],
        tbr_data["avg_inflationary_rewards_per_block"],
        tbr_data["avg_extra_rewards_per_block"],
        tbr_data["projected_daily_tbr"],
        tbr_data["projected_annual_tbr"],
    )
    print("  ✓ Exported time-based rewards")

    # Export reporting costs
    export_reporting_costs(
        reporting_costs_data["avg_gas_wanted"],
        reporting_costs_data["avg_gas_used"],
        reporting_costs_data["min_gas_price"],
        reporting_costs_data["avg_gas_cost"],
        reporting_costs_data["avg_fee_paid"],
        reporting_costs_data["blocks_per_day"],
        reporting_costs_data["reports_per_day"],
        reporting_costs_data["daily_fee_cost"],
        reporting_costs_data["monthly_fee_cost"],
        reporting_costs_data["yearly_fee_cost"],
    )
    print("  ✓ Exported reporting costs")

    # Export user tip totals
    export_user_tip_totals(
        user_tips_data["total_tips_all_time"], user_tips_data["user_tip_totals"]
    )
    print("  ✓ Exported user tip totals")

    # Export validator profitability
    export_validator_profitability(
        profitability_data["avg_stake_per_block"],
        profitability_data["avg_stake_per_minute"],
        profitability_data["avg_stake_per_hour"],
        profitability_data["avg_stake_per_day"],
        profitability_data["avg_stake_per_month"],
        profitability_data["avg_stake_per_year"],
        profitability_data["median_stake_per_block"],
        profitability_data["median_stake_per_minute"],
        profitability_data["median_stake_per_hour"],
        profitability_data["median_stake_per_day"],
        profitability_data["median_stake_per_month"],
        profitability_data["median_stake_per_year"],
    )
    print("  ✓ Exported validator profitability")

    # Export current reporter APRs
    export_current_reporter_aprs(apr_data["weighted_avg_apr"], apr_data["median_apr"])
    print("  ✓ Exported current reporter APRs")

    # Export APR by total stake
    export_apr_by_total_stake(
        stake_scenario_data["current_network_stake"],
        stake_scenario_data["current_apr"],
        stake_scenario_data["stake_results"],
    )
    print("  ✓ Exported APR by total stake scenarios")

    print("\nAll data exported successfully to ./data/ directory")
