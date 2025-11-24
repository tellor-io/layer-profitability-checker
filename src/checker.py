from termcolor import colored

from .apr import (
    calculate_apr_avgs,
    calculate_reporter_aprs,
    generate_apr_chart,
    print_reporter_apr_table,
)
from .chain_data.abci_queries import TellorABCIClient
from .chain_data.block_data import get_average_block_time
from .chain_data.rpc_client import TellorRPCClient
from .chain_data.tx_data import (
    print_submit_value_analysis,
    query_recent_reports,
)
from .config import get_rest_endpoint, get_rpc_endpoint, load_config
from .csv_export import export_all_data
from .display_helpers import (
    print_box_and_whisker,
    print_distribution_chart,
    print_info_box,
    print_section_header,
    print_table,
)
from .module_data.globalfee import get_min_gas_price
from .module_data.mint import Minter
from .module_data.reporter import get_reporters
from .module_data.selectors import (
    calculate_selector_profitability,
    format_selector_data_for_display,
    format_selector_profitability_for_display,
    get_all_reporter_selectors,
)
from .module_data.staking import get_total_stake
from .module_data.tipping import (
    format_tips_for_display,
    format_user_tip_totals_for_display,
    get_all_current_tips,
    get_all_user_tip_totals,
    get_available_tips,
    get_tipping_summary,
    get_total_tips,
)
from .rewards import (
    calculate_extra_rewards_duration,
    get_extra_rewards_pool_info,
    query_mint_events,
)
from .scenarios import format_targets_for_display_with_apr, run_scenarios_analysis


def main():
    print_welcome_message()

    # load configuration
    config = load_config("config.yaml")

    # Initialize RPC client with both RPC and REST endpoints
    rpc_endpoint = get_rpc_endpoint(config)
    rest_endpoint = get_rest_endpoint(config)
    print(f"Using RPC endpoint: {rpc_endpoint}")
    print(f"Using REST endpoint: {rest_endpoint}")
    rpc_client = TellorRPCClient(rpc_endpoint, rest_endpoint)
    abci_client = TellorABCIClient(rpc_client)

    # get chain id
    try:
        chain_id = rpc_client.get_chain_id()
        print("\n")
        print(colored(f"  Chain ID: {chain_id}", "green", attrs=["bold"]))
    except Exception as e:
        print(f"Error getting chain ID: {e}")
        chain_id = "unknown"

    # get total stake
    print_section_header("STAKING DISTRIBUTION")
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
    avg_stake = total_tokens_active / active_count

    # Display average and median stakes first
    stake_summary = {
        "Num Active Validators": f"{active_count:,}",
        "Total Active Validator Tokens": f"{total_tokens_active:,.1f} TRB",
        "Avg Active Validator Tokens": f"{avg_stake:,.1f} TRB",
        "Median Active Validator Tokens": f"{median_stake:,.1f} TRB",
    }
    print_info_box("stake distribution", stake_summary, separators=[])

    # Display ASCII box chart
    print_box_and_whisker(active_validator_stakes)

    # Display active/jailed/unbonding data in a table
    validator_headers = ["Status", "Count", "Tokens (TRB)"]
    validator_rows = [
        ["Active", f"{active_count:,}", f"{total_tokens_active:,.1f}"],
        ["Unbonding", f"{unbonding_count:,}", f"{total_tokens_unbonding:,.1f}"],
        ["Unbonded", f"{unbonded_count:,}", f"{total_tokens_unbonded:,.1f}"],
        ["Jailed", f"{jailed_count:,}", f"{total_tokens_jailed:,.1f}"],
    ]
    print_table("validator status", validator_headers, validator_rows)

    # Display ASCII distribution chart
    print_distribution_chart(active_validator_stakes)

    # get current block height and timestamp
    print_section_header("CURRENT BLOCK TIMES")
    avg_block_time, time_diff, block_diff = get_average_block_time(rpc_client)

    block_data = {
        "Sample Duration": f"{time_diff:.1f} seconds",
        "Blocks Produced": f"{block_diff:,}",
        "Avg Block Time": f"{avg_block_time:.1f} seconds",
        "Est Blocks per Hour": f"~ {3600 / avg_block_time:,.0f}",
        "Est Blocks per Day": f"~ {86400 / avg_block_time:,.0f}",
    }
    print_info_box("block time stats", block_data, separators=[3])

    print_section_header("REWARDS DISTRIBUTION")

    # Query mint events from recent blocks
    mint_events_data = query_mint_events(rpc_client=rpc_client)

    # Calculate expected TBR as sanity check
    minter = Minter()
    expected_mint_amount = minter.calculate_block_provision(time_diff)
    expected_avg_mint_amount = expected_mint_amount / block_diff

    # Extract TBR and extra rewards data
    tbr_mint_amount = 0
    extra_rewards_amount = 0
    tbr_avg_mint_amount = 0
    extra_rewards_avg_amount = 0

    # Check if any events were found
    has_any_events = mint_events_data and (
        mint_events_data["total_tbr_minted"] > 0
        or mint_events_data["total_extra_rewards"] > 0
    )
    has_tbr_events = mint_events_data and mint_events_data["total_tbr_minted"] > 0
    has_extra_rewards_events = (
        mint_events_data and mint_events_data["total_extra_rewards"] > 0
    )

    if not has_any_events:
        # No events found - just show message
        print(
            colored(
                "  ⚠️  No mint events found in recent blocks",
                "yellow",
                attrs=["bold"],
            )
        )
    else:
        # Events found - process tbr events
        if has_tbr_events:
            tbr_mint_amount = mint_events_data["total_tbr_minted"]
            tbr_avg_mint_amount = (
                tbr_mint_amount / mint_events_data["tbr_event_count"]
                if mint_events_data["tbr_event_count"] > 0
                else 0
            )
        else:
            tbr_mint_amount = 0
            tbr_avg_mint_amount = 0
            print(
                colored(
                    "  ⚠️  No base rewards events found in recent blocks",
                    "yellow",
                    attrs=["bold"],
                )
            )

        # process extra rewards events
        if has_extra_rewards_events:
            extra_rewards_amount = mint_events_data["total_extra_rewards"]
            extra_rewards_avg_amount = (
                extra_rewards_amount / mint_events_data["extra_rewards_event_count"]
                if mint_events_data["extra_rewards_event_count"] > 0
                else 0
            )
        else:
            extra_rewards_amount = 0
            extra_rewards_avg_amount = 0

        # calculate combined rewards
        total_combined_rewards = tbr_mint_amount + extra_rewards_amount
        total_combined_avg = tbr_avg_mint_amount + extra_rewards_avg_amount

        # Display Inflationary Rewards stats (TBR only) - only if we have TBR events
        if tbr_mint_amount > 0:
            inflationary_rewards_data = {
                "Inflationary Rewards": " ",
                "Data Source": "Event-based",
                "Average Inflationary Rewards Per Block": f"{tbr_avg_mint_amount:,.1f} loya",
                "Projected Daily Inflationary Rewards": f"~ {tbr_avg_mint_amount * (86400 / avg_block_time) * 1e-6:,.0f} TRB",
                "Projected Annual Inflationary Rewards": f"~ {tbr_avg_mint_amount * (86400 / avg_block_time) * 365 * 1e-6:,.0f} TRB",
            }
            print_info_box(
                "inflationary rewards", inflationary_rewards_data, separators=[1, 2]
            )

        # Display Extra Rewards stats - only if we have extra rewards events
        if extra_rewards_amount > 0:
            extra_rewards_data = {
                "Extra Rewards": " ",
                "Data Source": "Event-based",
                "Average Extra Rewards Per Block": f"{extra_rewards_avg_amount:,.1f} loya",
            }
            print_info_box("extra rewards", extra_rewards_data, separators=[1, 2])

    # Always query and display extra rewards pool information
    print("\nQuerying extra rewards pool module account...")
    pool_info = get_extra_rewards_pool_info(rpc_client)

    if pool_info:
        # Display combined pool information and duration estimates
        if has_extra_rewards_events:
            extra_rewards_avg_amount = (
                mint_events_data["total_extra_rewards"]
                / mint_events_data["extra_rewards_event_count"]
                if mint_events_data["extra_rewards_event_count"] > 0
                else 0
            )

            blocks_remaining, days, hours, minutes = calculate_extra_rewards_duration(
                extra_rewards_avg_amount, pool_info["balance_loya"], avg_block_time
            )

            # Display combined pool information with duration estimates
            pool_data = {
                "Extra Rewards Pool": " ",
                "Module Account": pool_info["account_name"],
                "Address": pool_info["address"],
                "Current Balance": f"{pool_info['balance_loya']:,.0f} loya",
                "Avg Extra Rewards Per Block": f"{extra_rewards_avg_amount:,.1f} loya",
                "Estimated Blocks Remaining": f"{blocks_remaining:,}",
                "Estimated Time Remaining": f"{days:.1f} days, {hours:.1f} hours, {minutes:.1f} minutes",
            }
            print_info_box("extra rewards pool", pool_data, separators=[1, 2])
        else:
            # Display basic pool information only (no duration estimates without events)
            pool_data = {
                "Extra Rewards Pool": " ",
                "Module Account": pool_info["account_name"],
                "Address": pool_info["address"],
                "Current Balance": f"{pool_info['balance_loya']:,.0f} loya",
            }
            print_info_box("extra rewards pool", pool_data, separators=[1, 2, 4])
    else:
        print(
            colored(
                "  ⚠️  Could not query extra rewards pool module account",
                "yellow",
                attrs=["bold"],
            )
        )

    # Show extra rewards warning after the pool account table if no events were found
    if mint_events_data and not has_extra_rewards_events:
        print(
            colored(
                "  ⚠️  No extra rewards events found in recent blocks",
                "yellow",
                attrs=["bold"],
            )
        )

    # Only show expected inflationary rewards if no events are found
    if not has_any_events:
        print("\n")
        expected_inflationary_data = {
            "Expected Inflationary Rewards": " ",
            "Data Source": "Expected calculation",
            "Expected Average Rewards Per Block": f"{expected_avg_mint_amount:,.1f} loya",
            "Expected Daily Rewards": f"~ {expected_avg_mint_amount * (86400 / avg_block_time) * 1e-6:,.0f} TRB",
            "Expected Annual Rewards": f"~ {expected_avg_mint_amount * (86400 / avg_block_time) * 365 * 1e-6:,.0f} TRB",
        }
        print_info_box(
            "expected inflationary rewards",
            expected_inflationary_data,
            separators=[1, 2],
        )

    # get average fees paid per submit value using current block analysis
    print_section_header("REPORTING COSTS")
    txs = query_recent_reports(rpc_client=rpc_client)
    analysis = print_submit_value_analysis(txs, rpc_client, config)

    avg_fee = analysis["avg_fee_loya"]
    min_gas_price = get_min_gas_price(rpc_client, config)
    if min_gas_price is None:
        min_gas_price = 0

    tx_data = {
        "Avg Gas Wanted": f"{analysis.get('avg_gas_wanted', 0):,.0f}",
        "Avg Gas Used": f"{analysis.get('avg_gas_used', 0):,.0f}",
        "Min Gas Price": f"{min_gas_price:.6f} loya",
        "Avg Gas Cost (min_gas_price * gas_used)": f"{analysis.get('avg_min_cost', 0):.4f} loya",
        "Avg Fee Paid": f"{avg_fee:.1f} LOYA",
    }
    print_info_box("submit value stats", tx_data)

    # Calculate fee projections
    blocks_per_day = 86400 / avg_block_time
    reports_per_day = blocks_per_day / 2  # Every other block
    daily_fee_cost_loya = reports_per_day * avg_fee
    daily_fee_cost_trb = daily_fee_cost_loya * 1e-6
    monthly_fee_cost_trb = daily_fee_cost_trb * 30
    yearly_fee_cost_trb = daily_fee_cost_trb * 365

    projection_data = {
        "Blocks per Day": f"~ {blocks_per_day:,.0f}",
        "Reports per Day (1 every other block)": f"~ {reports_per_day:,.0f}",
        "Daily Fee Cost": f"~ {daily_fee_cost_trb:,.4f} TRB",
        "Monthly Fee Cost": f"~ {monthly_fee_cost_trb:,.1f} TRB",
        "Yearly Fee Cost": f"~ {yearly_fee_cost_trb:,.1f} TRB",
    }
    print_info_box("fee projections", projection_data)

    #  Actual reporter data
    print_section_header("REPORTERS")
    reporters, reporter_summary = get_reporters(rpc_client, config)
    print_info_box("reporter summary", reporter_summary, separators=[1, 4])

    # Tipping information
    print_section_header("CURRENT TIPS")

    # Get current tips for all price feeds
    current_tips = get_all_current_tips(rpc_client, config)

    # Get total tips all time
    total_tips = get_total_tips(rpc_client)

    # Display tipping summary with custom ordering
    tipping_summary = get_tipping_summary(current_tips)

    # Create ordered summary without Total Tips All Time
    ordered_summary = {}
    ordered_summary["Currently Tipped Queries"] = tipping_summary[
        "Currently Tipped Queries"
    ]
    ordered_summary["Total Tip Amount"] = tipping_summary["Total Tip Amount"]
    ordered_summary["Average Tip"] = tipping_summary["Average Tip"]
    ordered_summary["Highest Tip"] = tipping_summary["Highest Tip"]
    ordered_summary["Lowest Tip"] = tipping_summary["Lowest Tip"]

    print_info_box("tipping summary", ordered_summary, separators=[1, 3])

    # Display tips table
    tip_headers, tip_rows = format_tips_for_display(current_tips)
    print_table("current tips by price feed", tip_headers, tip_rows)

    # Check for available tips if account address is configured
    if "account_address" in config and config["account_address"]:
        print(f"\nQuerying available tips for account: {config['account_address']}\n ")
        available_tips = get_available_tips(
            rpc_client, config, config["account_address"]
        )
        if available_tips is not None:
            account_tips_data = {
                "Claimable reporter rewards": f"{available_tips:.5f} TRB"
            }
            print_info_box("account available tips", account_tips_data)
        else:
            print("  Unable to query available tips for this account")
    else:
        print("\n  No account address configured - skipping available tips query")
        print(
            "  Add 'account_address: your_address_here' to config.yaml to enable this feature"
        )

    # Get all user tip totals
    print_section_header("USER TIP TOTALS")

    # Get all user tip totals using RPC client with configured endpoints
    user_tip_totals = get_all_user_tip_totals(rpc_client)

    # Display total tips all time first
    if total_tips is not None:
        total_tips_data = {"Total Tips All Time": f"{total_tips:.5f} TRB"}
        print_info_box("total tips all time", total_tips_data, separators=[1])

    if user_tip_totals:
        # Display user tip totals table
        tip_totals_headers, tip_totals_rows = format_user_tip_totals_for_display(
            user_tip_totals
        )
        print_table("user tip totals", tip_totals_headers, tip_totals_rows)
    else:
        print("  No addresses found with tip totals > 0")

    # calculate profitability metrics
    print_section_header("AVG/MEDIAN VALIDATOR'S PROJECTED PROFITABILITY")

    print_info_box("stake distribution repeat", stake_summary, separators=[])

    # Use combined rewards for profitability calculations
    # If no events found, use expected calculation for profitability
    if has_any_events:
        avg_combined_mint_amount = (
            total_combined_avg  # This includes both TBR and extra rewards
        )
    else:
        avg_combined_mint_amount = expected_avg_mint_amount  # Use expected TBR only

    avg_proportion_stake = avg_stake / total_tokens_active
    median_proportion_stake = median_stake / total_tokens_active
    avg_profit_per_block = (
        (avg_proportion_stake * avg_combined_mint_amount) - (avg_fee / 2)
    ) * 1e-6
    median_profit_per_block = (
        (median_proportion_stake * avg_combined_mint_amount) - (avg_fee / 2)
    ) * 1e-6

    # Time-based projections
    blocks_per_min = 60 / avg_block_time
    blocks_per_hour = 3600 / avg_block_time
    blocks_per_day = 86400 / avg_block_time

    # Profit projections for average stake
    avg_profit_1min = avg_profit_per_block * blocks_per_min
    avg_profit_1hour = avg_profit_per_block * blocks_per_hour
    avg_profit_1day = avg_profit_per_block * blocks_per_day

    # Profit projections for median stake
    median_profit_1min = median_profit_per_block * blocks_per_min
    median_profit_1hour = median_profit_per_block * blocks_per_hour
    median_profit_1day = median_profit_per_block * blocks_per_day

    # Create profitability table
    profit_headers = [
        "Time Period",
        "Avg Stake Max Profit (TRB)",
        "Median Stake Max Profit (TRB)",
    ]
    profit_rows = [
        ["Per Block", f"{avg_profit_per_block:.6f}", f"{median_profit_per_block:.6f}"],
        ["Per Minute", f"{avg_profit_1min:.6f}", f"{median_profit_1min:.6f}"],
        ["Per Hour", f"{avg_profit_1hour:.1f}", f"{median_profit_1hour:.1f}"],
        ["Per Day", f"{avg_profit_1day:.1f}", f"{median_profit_1day:.1f}"],
        ["Per Month", f"{avg_profit_1day * 30:.1f}", f"{median_profit_1day * 30:.1f}"],
        ["Per Year", f"{avg_profit_1day * 365:.0f}", f"{median_profit_1day * 365:.0f}"],
    ]
    print_table("profitability stats", profit_headers, profit_rows)

    # Convert loya to TRB for APR calculations
    avg_combined_mint_amount_trb = avg_combined_mint_amount * 1e-6
    avg_fee_trb = avg_fee * 1e-6

    # Calculate and display individual reporter APRs
    print_section_header("LIVE REPORTER APRs")
    reporter_aprs = calculate_reporter_aprs(
        reporters,
        total_tokens_active,
        avg_combined_mint_amount_trb,
        avg_fee_trb,
        avg_block_time,
    )

    # Display weighted average, median APRs, and break-even stake in info box
    weighted_avg_apr, median_apr = calculate_apr_avgs(reporter_aprs)

    # Calculate break-even stake amount where APR = 0%
    #
    # profit_per_block = (stake / total_stake) * mint_per_block - (fee / 2)
    # At break-even: profit_per_block = 0
    # (stake / total_stake) * mint_per_block = fee / 2
    # stake = (fee / 2) * total_stake / mint_per_block
    #
    # Formula: break_even = ((avg_fee / 2) * total_stake) / avg_rewards_per_block
    calculated_break_even = (
        (avg_fee_trb / 2) * total_tokens_active
    ) / avg_combined_mint_amount_trb

    apr_averages = {
        "Weighted Avg APR": f"{weighted_avg_apr:.2f}%",
        "Median APR": f"{median_apr:.2f}%",
        "Break-Even Stake (0% apr)": f"{calculated_break_even:.2f} TRB",
    }
    print_info_box("current reporter metrics", apr_averages)

    print_reporter_apr_table(reporter_aprs)

    # Generate APR chart with break-even point
    generate_apr_chart(
        total_tokens_active,
        avg_combined_mint_amount_trb,
        avg_fee_trb,
        avg_block_time,
        median_stake,
        calculated_break_even,
        active_validator_stakes,
    )

    print(
        "\n  To see your max apr in the current network state, check current_apr_chart.png"
    )

    # Selector profitability analysis
    print_section_header("SELECTOR PROFITABILITY")

    # Get selector data for all reporters
    selector_data = get_all_reporter_selectors(rest_endpoint, reporters)

    if selector_data:
        selector_headers, selector_rows = format_selector_data_for_display(
            selector_data
        )
        print_table("reporter selectors", selector_headers, selector_rows)
    else:
        print("\n  No selector data available.")

    # Calculate and display individual selector profitability
    print("\n")
    selector_profits = calculate_selector_profitability(
        rest_endpoint, reporters, reporter_aprs
    )

    if selector_profits:
        profit_headers, profit_rows = format_selector_profitability_for_display(
            selector_profits
        )
        print_table("selector expected yearly earnings", profit_headers, profit_rows)
    else:
        print("  No selector profitability data available.")

    # Run scenarios analysis
    print_section_header("APR BY TOTAL STAKE")
    stake_results, targets = run_scenarios_analysis(
        total_tokens_active, avg_combined_mint_amount_trb, avg_fee_trb, avg_block_time
    )

    # Display target APR points in info box with current APR
    target_display = format_targets_for_display_with_apr(
        targets, total_tokens_active, stake_results
    )
    print_info_box("APR target points", target_display, separators=[1])

    # Calculate current APR for CSV export
    import numpy as np

    stake_amounts_trb = stake_results["stake_amounts_trb"]
    aprs = stake_results["weighted_avg_aprs"]
    current_apr = np.interp(total_tokens_active, stake_amounts_trb, aprs)

    # Prepare data for CSV export
    if has_any_events:
        csv_data_source = "Event-based"
        csv_total_sample = total_combined_rewards * 1e-6
        csv_avg_inflationary_per_block = tbr_avg_mint_amount
        csv_avg_extra_per_block = extra_rewards_avg_amount
    else:
        csv_data_source = "Expected calculation"
        csv_total_sample = expected_mint_amount * 1e-6
        csv_avg_inflationary_per_block = 0
        csv_avg_extra_per_block = 0  # No extra rewards in expected calculation

    # Calculate projected values based on combined rewards
    total_avg_per_block = csv_avg_inflationary_per_block + csv_avg_extra_per_block

    tbr_data = {
        "data_source": csv_data_source,
        "total_tbr_sample": csv_total_sample,
        "num_blocks_sampled": block_diff,
        "avg_inflationary_rewards_per_block": csv_avg_inflationary_per_block,
        "avg_extra_rewards_per_block": csv_avg_extra_per_block,
        "projected_daily_tbr": total_avg_per_block * (86400 / avg_block_time) * 1e-6,
        "projected_annual_tbr": total_avg_per_block
        * (86400 / avg_block_time)
        * 365
        * 1e-6,
    }

    reporting_costs_data = {
        "avg_gas_wanted": analysis.get("avg_gas_wanted", 0),
        "avg_gas_used": analysis.get("avg_gas_used", 0),
        "min_gas_price": min_gas_price,
        "avg_gas_cost": analysis.get("avg_min_cost", 0),
        "avg_fee_paid": avg_fee,
        "blocks_per_day": blocks_per_day,
        "reports_per_day": reports_per_day,
        "daily_fee_cost": daily_fee_cost_trb,
        "monthly_fee_cost": monthly_fee_cost_trb,
        "yearly_fee_cost": yearly_fee_cost_trb,
    }

    user_tips_data = {
        "total_tips_all_time": total_tips if total_tips is not None else 0,
        "user_tip_totals": user_tip_totals if user_tip_totals else [],
    }

    profitability_data = {
        "avg_stake_per_block": avg_profit_per_block,
        "avg_stake_per_minute": avg_profit_1min,
        "avg_stake_per_hour": avg_profit_1hour,
        "avg_stake_per_day": avg_profit_1day,
        "avg_stake_per_month": avg_profit_1day * 30,
        "avg_stake_per_year": avg_profit_1day * 365,
        "median_stake_per_block": median_profit_per_block,
        "median_stake_per_minute": median_profit_1min,
        "median_stake_per_hour": median_profit_1hour,
        "median_stake_per_day": median_profit_1day,
        "median_stake_per_month": median_profit_1day * 30,
        "median_stake_per_year": median_profit_1day * 365,
    }

    apr_data = {"weighted_avg_apr": weighted_avg_apr, "median_apr": median_apr}

    stake_scenario_data = {
        "current_network_stake": total_tokens_active,
        "current_apr": current_apr,
        "stake_results": stake_results,
    }

    # Export all data to CSV files
    export_all_data(
        tbr_data,
        reporting_costs_data,
        user_tips_data,
        profitability_data,
        apr_data,
        stake_scenario_data,
    )

    print_section_header("END")


def print_welcome_message():
    # Welcome message with ASCII art night sky - green and bold
    print("\n" + colored("┌" + "═" * 78 + "┐", "green", attrs=["bold"]))
    print(colored("║" + "★" * 78 + "║", "green", attrs=["bold"]))
    print(
        colored(
            "║"
            + "░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░"
            + "║",
            "green",
            attrs=["bold"],
        )
    )
    print(
        colored(
            "║"
            + "█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█"
            + "║",
            "green",
            attrs=["bold"],
        )
    )
    print(colored("║" + " " * 78 + "║", "green", attrs=["bold"]))
    print(colored("║" + " " * 78 + "║", "green", attrs=["bold"]))
    print(
        colored(
            "║" + "TELLOR LAYER PROFITABILITY CHECKER".center(78) + "║",
            "green",
            attrs=["bold"],
        )
    )
    print(colored("║" + " " * 78 + "║", "green", attrs=["bold"]))
    print(colored("║" + " " * 78 + "║", "green", attrs=["bold"]))
    print(
        colored(
            "║"
            + "█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█"
            + "║",
            "green",
            attrs=["bold"],
        )
    )
    print(
        colored(
            "║"
            + "░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░"
            + "║",
            "green",
            attrs=["bold"],
        )
    )
    print(colored("║" + "★" * 78 + "║", "green", attrs=["bold"]))
    print(colored("└" + "═" * 78 + "┘", "green", attrs=["bold"]))


if __name__ == "__main__":
    main()
