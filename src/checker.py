import yaml
from termcolor import colored

from .apr import (
    calculate_apr_avgs,
    calculate_break_even_stake,
    calculate_reporter_aprs,
    generate_apr_chart,
    print_reporter_apr_table,
)
from .chain_data.abci_queries import TellorABCIClient
from .chain_data.block_data import get_average_block_time
from .chain_data.rpc_client import TellorRPCClient
from .chain_data.tx_data import (
    print_submit_value_analysis,
    query_mint_events,
    query_recent_reports,
)
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
from .scenarios import format_targets_for_display_with_apr, run_scenarios_analysis


def main():
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

    # load configuration
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    # Initialize RPC client (unified approach)
    rpc_endpoint = config.get("rpc_endpoint", "http://localhost:26657")
    print(f"Using RPC endpoint: {rpc_endpoint}")
    rpc_client = TellorRPCClient(rpc_endpoint)
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

    # get mint amount from events and expected calculation
    print_section_header("TIME BASED REWARDS")

    # Query mint events from recent blocks
    mint_events_data = query_mint_events(rpc_client=rpc_client)

    # Calculate expected TBR as sanity check
    minter = Minter()
    expected_mint_amount = minter.calculate_block_provision(time_diff)
    expected_avg_mint_amount = expected_mint_amount / block_diff

    # Use event-based data if available, otherwise fall back to expected
    if mint_events_data and mint_events_data["total_minted"] > 0:
        event_mint_amount = mint_events_data["total_minted"]
        event_avg_mint_amount = (
            event_mint_amount / mint_events_data["event_count"]
            if mint_events_data["event_count"] > 0
            else 0
        )

        # Sanity check: compare event-based vs expected (per block)
        expected_per_block = expected_mint_amount / block_diff
        if (
            abs(event_avg_mint_amount - expected_per_block) > 100
        ):  # Allow 100 loya tolerance
            print(
                colored(
                    "  ⚠️  Current time based rewards amount is different from expected",
                    "yellow",
                    attrs=["bold"],
                )
            )
            print(f"     Event-based: {event_avg_mint_amount:,.1f} loya per block")
            print(f"     Expected:    {expected_per_block:,.1f} loya per block")
            print(
                f"     Difference:  {abs(event_avg_mint_amount - expected_per_block):,.1f} loya per block"
            )

        # Use event-based data for calculations
        mint_amount = event_mint_amount
        avg_mint_amount = event_avg_mint_amount
        data_source = "Event-based"
    else:
        print(
            colored(
                "  ⚠️  No mint events found, using expected calculation",
                "yellow",
                attrs=["bold"],
            )
        )
        mint_amount = expected_mint_amount
        avg_mint_amount = expected_avg_mint_amount
        data_source = "Expected calculation"

    mint_data = {
        "Data Source": data_source,
        "Total TBR from Sample Period": f"{mint_amount * 1e-6:,.2f} TRB",
        "Average TBR Per Block": f"{avg_mint_amount:,.1f} loya",
        "Projected Daily TBR": f"~ {avg_mint_amount * (86400 / avg_block_time) * 1e-6:,.0f} TRB",
        "Projected Annual TBR": f"~ {avg_mint_amount * (86400 / avg_block_time) * 365 * 1e-6:,.0f} TRB",
    }
    print_info_box("minting stats", mint_data, separators=[2])

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

    # Get the REST endpoint from RPC client
    rest_endpoint = rpc_client.rpc_endpoint
    if rest_endpoint.endswith("/rpc"):
        rest_endpoint = rest_endpoint.replace("/rpc", "")

    # Get all user tip totals
    user_tip_totals = get_all_user_tip_totals(rest_endpoint)

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

    avg_proportion_stake = avg_stake / total_tokens_active
    median_proportion_stake = median_stake / total_tokens_active
    avg_profit_per_block = (
        (avg_proportion_stake * avg_mint_amount) - (avg_fee / 2)
    ) * 1e-6
    median_profit_per_block = (
        (median_proportion_stake * avg_mint_amount) - (avg_fee / 2)
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

    # Calculate and display break-even stake
    break_even_stake, break_even_mult = calculate_break_even_stake(
        total_tokens_active, avg_mint_amount, avg_fee, avg_block_time, median_stake
    )
    if break_even_stake:
        break_even_data = {
            "Break-even Stake": f"{break_even_stake:.1f} TRB",
        }
        print_info_box("break-even analysis", break_even_data)

    # Convert loya to TRB for APR calculations
    avg_mint_amount_trb = avg_mint_amount * 1e-6
    avg_fee_trb = avg_fee * 1e-6

    # Generate APR chart
    print("Generated current_apr_chart.png")
    generate_apr_chart(
        total_tokens_active,
        avg_mint_amount_trb,
        avg_fee_trb,
        avg_block_time,
        median_stake,
        break_even_stake,
        break_even_mult,
    )

    # Calculate and display individual reporter APRs
    print_section_header("CURRENT REPORTER APRs")
    reporter_aprs = calculate_reporter_aprs(
        reporters, total_tokens_active, avg_mint_amount_trb, avg_fee_trb, avg_block_time
    )

    # Display both weighted average and median APRs in info box
    weighted_avg_apr, median_apr = calculate_apr_avgs(reporter_aprs)
    apr_averages = {
        "Weighted Avg APR": f"{weighted_avg_apr:.2f}%",
        "Median APR": f"{median_apr:.2f}%",
    }
    print_info_box("apr averages", apr_averages)

    print_reporter_apr_table(reporter_aprs)

    print(
        "\n  To see your max apr in the current network state, check current_apr_chart.png"
    )

    # Run scenarios analysis
    print_section_header("APR BY TOTAL STAKE")
    stake_results, targets = run_scenarios_analysis(
        total_tokens_active, avg_mint_amount_trb, avg_fee_trb, avg_block_time
    )

    # Display target APR points in info box with current APR
    target_display = format_targets_for_display_with_apr(
        targets, total_tokens_active, stake_results
    )
    print_info_box("APR target points", target_display, separators=[2])

    print_section_header("END")


if __name__ == "__main__":
    main()
