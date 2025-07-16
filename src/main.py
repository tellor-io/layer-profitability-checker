from module_data.staking import get_total_stake
from module_data.mint import Minter
from module_data.reporter import get_reporters
from module_data.globalfee import get_min_gas_price
from chain_data.tx_data import query_recent_reports, print_submit_value_analysis
from chain_data.block_data import get_average_block_time
from chain_data.node_data import get_chain_id
from apr import generate_apr_chart, print_apr_table, calculate_reporter_aprs, print_reporter_apr_table, calculate_apr_avgs
from scenarios import run_scenarios_analysis, format_targets_for_display_with_apr
from termcolor import colored
import yaml
import numpy as np

def print_section_header(title):
    """Print a beautifully formatted section header with a distinct style"""
    print("\n" * 2 + colored("═" * 80, 'green', attrs=['bold']))
    print(colored(f"  {title}", 'green', attrs=['bold', 'dark']))
    print("\n")

def print_info_box(title, data_dict, separators=None):
    """Print a beautifully formatted information box with optional separators"""
    print("┌" + "─" * 78 + "┐")
    
    # Calculate dynamic label width based on longest label + 5
    max_label_length = max(len(key) for key in data_dict.keys())
    label_width = max_label_length + 3
    value_width = 78 - label_width - 1 # 78 total - label_width - padding (?)
    
    keys = list(data_dict.keys())
    for i, (key, value) in enumerate(data_dict.items()):
        # Split the line into two columns: label (left) and value (right)
        # Left align label and value in their respective columns
        formatted_line = f" {key:<{label_width-1}}{str(value):<{value_width}} "
        print("│" + formatted_line + "│")
        
        # Add separator line if specified
        if separators and i + 1 in separators and i < len(keys) - 1:
            print("├" + "─" * 78 + "┤")
    
    print("└" + "─" * 78 + "┘")

def print_table(title, headers, rows):
    """Print a beautifully formatted table with proper border alignment"""
    # Calculate column widths with proper padding
    col_widths = []
    for i in range(len(headers)):
        max_width = len(headers[i])
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width + 2)  # Add 2 for padding (1 space on each side)
    
    # Calculate total width: sum of column widths + separators between columns + outer borders
    total_width = sum(col_widths) + len(col_widths) - 1
    
    # Header
    print("┌" + "─" * total_width + "┐")
    
    # Column headers
    header_line = "│"
    for i, header in enumerate(headers):
        header_line += f" {header:<{col_widths[i]-2}} "
        if i < len(headers) - 1:
            header_line += "│"
    header_line += "│"
    print(header_line)
    
    # Separator line between headers and data
    separator_line = "├"
    for i, width in enumerate(col_widths):
        separator_line += "─" * width
        if i < len(col_widths) - 1:
            separator_line += "┼"
    separator_line += "┤"
    print(separator_line)
    
    # Data rows
    for row in rows:
        row_line = "│"
        for i in range(len(headers)):
            cell_value = str(row[i]) if i < len(row) else ""
            # Left align all columns
            row_line += f" {cell_value:<{col_widths[i]-2}} "
            if i < len(headers) - 1:
                row_line += "│"
        row_line += "│"
        print(row_line)
    
    # Bottom border
    bottom_line = "└"
    for i, width in enumerate(col_widths):
        bottom_line += "─" * width
        if i < len(col_widths) - 1:
            bottom_line += "┴"
    bottom_line += "┘"
    print(bottom_line)

def print_box_and_whisker(stakes, title="VALIDATOR DISTRIBUTION"):
    """Create an ASCII box plot of validator stakes"""
    if not stakes:
        return
    
    # Convert to TRB for display
    stakes_trb = [stake * 1e-6 for stake in stakes]
    stakes_trb.sort()
    
    n = len(stakes_trb)
    
    # Calculate quartiles
    q1_idx = n // 4
    q2_idx = n // 2  # median
    q3_idx = 3 * n // 4
    
    q1 = stakes_trb[q1_idx]
    q2 = stakes_trb[q2_idx]  # median
    q3 = stakes_trb[q3_idx]
    
    min_val = stakes_trb[0]
    max_val = stakes_trb[-1]
    
    # Create the box chart
    chart_width = 60
    total_range = max_val - min_val
    if total_range == 0:
        total_range = 1  # Avoid division by zero
    
    # Calculate positions on the chart
    def pos(val):
        pos_val = int(((val - min_val) / total_range) * chart_width)
        return max(0, min(pos_val, chart_width - 1))  # Ensure within bounds
    
    min_pos = pos(min_val)
    q1_pos = pos(q1)
    q2_pos = pos(q2)
    q3_pos = pos(q3)
    max_pos = pos(max_val)
    
    print("┌" + "─" * 78 + "┐")
    
    # Box plot line (removed title and header)
    box_prefix = "│ Box Plot: " + " " * 6  # This is 16 characters
    
    # Create the visual
    visual = [" "] * chart_width
    
    # Whiskers (lines from min to Q1 and Q3 to max)
    for i in range(max(0, min_pos), min(chart_width, q1_pos)):
        visual[i] = "─"
    for i in range(max(0, q3_pos + 1), min(chart_width, max_pos + 1)):
        visual[i] = "─"
    
    # Box (Q1 to Q3)
    for i in range(max(0, q1_pos), min(chart_width, q3_pos + 1)):
        visual[i] = "█"
    
    # Median line
    if q2_pos < len(visual):
        visual[q2_pos] = colored("│", 'green', attrs=['bold'])
    
    # Whisker ends
    if min_pos < len(visual):
        visual[min_pos] = "├"
    if max_pos < len(visual):
        visual[max_pos] = "┤"
    
    # Build box line with proper alignment accounting for colored text
    visual_content = "".join(visual)
    
    # Count actual visible characters (not ANSI codes)
    visible_chars = 0
    i = 0
    while i < len(visual_content):
        if visual_content[i:i+2] == '\x1b[':  # ANSI escape sequence start
            # Skip to the end of the ANSI sequence
            while i < len(visual_content) and visual_content[i] != 'm':
                i += 1
            i += 1  # Skip the 'm'
        else:
            visible_chars += 1
            i += 1
    
    total_content_length = len(box_prefix) + visible_chars
    padding_needed = 79 - total_content_length
    
    box_line = box_prefix + visual_content + " " * padding_needed + "│"
    print(box_line)
    
    # Add empty line below the box plot
    print("│" + " " * 78 + "│")
    
    # Enhanced scale with more numbers - fix alignment issues
    scale_prefix = "│ # of Tokens: " + " " * 3 
    scale_visual = [" "] * chart_width
    
    # Add scale numbers at regular intervals
    num_intervals = 7  # Reduced to prevent overcrowding
    for i in range(num_intervals + 1):
        pos_on_scale = int(i * (chart_width - 1) / num_intervals)  # Use chart_width - 1 for proper distribution
        
        value = min_val + (i / num_intervals) * total_range  # Calculate value based on interval, not position
        value_str = f"{value:.0f}" if value >= 10 else f"{value:.1f}"
        
        # Special handling for the last number to prevent cutoff
        if i == num_intervals:
            # For the last number, right-align it to the end of the chart
            start_pos = chart_width - len(value_str)
            end_pos = chart_width
        else:
            # Place the number, avoiding overlaps
            start_pos = max(0, pos_on_scale - len(value_str) // 2)
            end_pos = min(chart_width, start_pos + len(value_str))
            
            # Adjust if we're going beyond the chart width
            if end_pos > chart_width:
                start_pos = chart_width - len(value_str)
                end_pos = chart_width
        
        # Check if we have space without overlap
        can_place = True
        for j in range(start_pos, end_pos):
            if j < len(scale_visual) and scale_visual[j] != " ":
                can_place = False
                break
        
        if can_place:
            for j in range(start_pos, end_pos):
                if j < len(scale_visual) and (j - start_pos) < len(value_str):
                    scale_visual[j] = value_str[j - start_pos]
    
    # Build the complete line with proper padding
    scale_content = "".join(scale_visual)
    total_content_length = len(scale_prefix) + len(scale_content)
    padding_needed = 79 - total_content_length
    
    scale_numbers_line = scale_prefix + scale_content + " " * padding_needed + "│"
    print(scale_numbers_line)
    print("│" + " " * 78 + "│")
    
    # Statistics
    # Left column: Min, Median, Max
    # Right column: Q1, Q3
    left_col = [
        f"Min: ",
        f"Q1: ",
        f"Median: ", 
        f"Q3: ",
        f"Max: "
    ]
    
    right_col = [
        f"{min_val:.1f} TRB",
        f"{q1:.1f} TRB",
        f"{q2:.1f} TRB",
        f"{q3:.1f} TRB",
        f"{max_val:.1f} TRB"
    ]
    
    # Calculate column width (split the 78 character width)
    col_width = 39  # 78 / 2
    
    for left_text, right_text in zip(left_col, right_col):
        # Build the line with proper padding
        left_padded = f"│ {left_text:<{16}}"
        right_padded = f"{right_text:<{61}}" + "│"
        line = left_padded + right_padded
        print(line)
    
    print("└" + "─" * 78 + "┘")

def print_distribution_chart(stakes, title="VALIDATOR COUNTS BY POWER"):
    """Create an ASCII histogram of validator stakes"""
    if not stakes:
        return
    
    # Convert to TRB for display
    stakes_trb = [stake * 1e-6 for stake in stakes]
    stakes_trb.sort()
    
    min_stake = min(stakes_trb)
    max_stake = max(stakes_trb)
    
    # Create exactly 6 intervals with nice round numbers
    def round_to_nice_number(x):
        """Round to a nice number for display"""
        if x <= 0:
            return 0
        
        import math
        # Find the order of magnitude
        magnitude = 10 ** math.floor(math.log10(x))
        
        # Normalize to 1-10 range
        normalized = x / magnitude
        
        # Round to nice numbers
        if normalized <= 1.5:
            nice = 1
        elif normalized <= 3:
            nice = 2
        elif normalized <= 7:
            nice = 5
        else:
            nice = 10
        
        return nice * magnitude
    
    # Calculate a good interval size
    range_size = max_stake - min_stake
    raw_interval = range_size / 5  # 5 intervals to span the range (plus one starting from 0)
    nice_interval = round_to_nice_number(raw_interval)
    
    # Ensure minimum interval size
    if nice_interval == 0:
        nice_interval = 1
    
    # Create bins starting from 0
    bins = [0]
    current = nice_interval
    
    # Add intervals until we exceed max_stake
    while len(bins) < 6 and current <= max_stake * 1.5:  # 1.5 buffer to ensure we capture all
        bins.append(current)
        current += nice_interval
    
    # Ensure we have exactly 6 bins by adding the final boundary
    if len(bins) < 6:
        bins.append(max_stake + 1)
    else:
        bins[-1] = max_stake * 1.1  # Ensure the last bin captures the maximum
    
    # Remove any duplicate consecutive values
    unique_bins = [bins[0]]
    for i in range(1, len(bins)):
        if bins[i] > unique_bins[-1]:
            unique_bins.append(bins[i])
    
    bins = unique_bins
    
    # Count validators in each bin and create labels
    bin_counts = []
    bin_labels = []
    
    for i in range(len(bins) - 1):
        count = sum(1 for stake in stakes_trb if bins[i] <= stake < bins[i + 1])
        # Show ALL bins, even if empty (count == 0)
        bin_counts.append(count)
        
        # Format labels nicely
        start_val = bins[i]
        end_val = bins[i + 1]
        
        # Format based on magnitude
        if end_val >= 1000:
            if start_val >= 1000:
                bin_labels.append(f"{start_val/1000:.0f}k-{end_val/1000:.0f}k TRB")
            else:
                bin_labels.append(f"{start_val:.0f}-{end_val/1000:.1f}k TRB")
        elif end_val >= 100:
            bin_labels.append(f"{start_val:.0f}-{end_val:.0f} TRB")
        elif end_val >= 10:
            bin_labels.append(f"{start_val:.0f}-{end_val:.0f} TRB")
        else:
            bin_labels.append(f"{start_val:.1f}-{end_val:.1f} TRB")
    
    if not bin_counts:
        return
    
    # Calculate the maximum width for the chart (leave space for labels)
    max_label_width = max(len(label) for label in bin_labels)
    chart_width = 78 - max_label_width - 8  # Total width - label width - padding and count
    
    # Scale bars to fit within chart width
    max_count = max(bin_counts) if max(bin_counts) > 0 else 1  # Avoid division by zero
    
    print("┌" + "─" * 78 + "┐")
    print("│" + title.center(78) + "│")
    print("├" + "─" * 78 + "┤")
    
    for i, (label, count) in enumerate(zip(bin_labels, bin_counts)):
        # Create green stars - one star per validator
        stars = colored("★" * count, 'green')
        
        # Calculate padding manually since colored text messes up string formatting
        stars_padding = " " * (chart_width - count)
        
        # Create the line with proper spacing
        line = f"│ {label:>{max_label_width}} │{stars}{stars_padding}│ {count:2d} │"
        print(line)
    
    print("└" + "─" * 78 + "┘")

def main():
    
    # Welcome message with ASCII art night sky - green and bold
    print("\n" + colored("┌" + "═" * 78 + "┐", 'green', attrs=['bold']))
    print(colored("║" + "★" * 78 + "║", 'green', attrs=['bold']))
    print(colored("║" + "░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░" + "║", 'green', attrs=['bold']))
    print(colored("║" + "█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█" + "║", 'green', attrs=['bold']))
    print(colored("║" + " " * 78 + "║", 'green', attrs=['bold']))
    print(colored("║" + " " * 78 + "║", 'green', attrs=['bold']))
    print(colored("║" + "TELLOR LAYER PROFITABILITY CHECKER".center(78) + "║", 'green', attrs=['bold']))
    print(colored("║" + " " * 78 + "║", 'green', attrs=['bold']))
    print(colored("║" + " " * 78 + "║", 'green', attrs=['bold']))
    print(colored("║" + "█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█" + "║", 'green', attrs=['bold']))
    print(colored("║" + "░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░▒▓█ ★ ░" + "║", 'green', attrs=['bold']))
    print(colored("║" + "★" * 78 + "║", 'green', attrs=['bold']))
    print(colored("└" + "═" * 78 + "┘", 'green', attrs=['bold']))
    
    # load node url and layerd path from config
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    layerd_path = config["layerd_path"]

    # get chain id 
    chain_id = get_chain_id(layerd_path)
    print("\n")
    print(colored(f"  Chain ID: {chain_id}", 'green', attrs=['bold']))
    
    # get total stake
    print_section_header("STAKING DISTRIBUTION")
    total_tokens_active, total_tokens_jailed, total_tokens_unbonding, active_count, jailed_count, unbonding_count, median_stake, active_validator_stakes = get_total_stake()
    avg_stake = total_tokens_active / active_count

    print("Getting active validator set...")

    # Display average and median stakes first
    stake_summary = {
        "Total Active Validator Tokens": f"{total_tokens_active * 1e-6:,.1f} TRB",
        "Num Active Validators": f"{active_count:,}",
        "Avg Active Validator Tokens": f"{avg_stake * 1e-6:,.1f} TRB",
        "Median Active Validator Tokens": f"{median_stake * 1e-6:,.1f} TRB",
    }
    print_info_box("stake distribution", stake_summary, separators=[])

    # Display ASCII box chart
    print_box_and_whisker(active_validator_stakes)

    # Display active/jailed/unbonding data in a table
    validator_headers = ["Status", "Count", "Tokens (TRB)"]
    validator_rows = [
        ["Active", f"{active_count:,}", f"{total_tokens_active * 1e-6:,.1f}"],
        ["Unbonding", f"{unbonding_count:,}", f"{total_tokens_unbonding * 1e-6:,.1f}"],
        ["Jailed", f"{jailed_count:,}", f"{total_tokens_jailed * 1e-6:,.1f}"]
    ]
    print_table("validator status", validator_headers, validator_rows)

    # Display ASCII distribution chart
    print_distribution_chart(active_validator_stakes)

    # get current block height and timestamp
    print_section_header("CURRENT BLOCK TIMES")
    avg_block_time, time_diff, block_diff = get_average_block_time(layerd_path)
    
    block_data = {
        "Sample Duration": f"{time_diff:.1f} seconds",
        "Blocks Produced": f"{block_diff:,}",
        "Avg Block Time": f"{avg_block_time:.1f} seconds",
        "Est Blocks per Hour": f"~ {3600/avg_block_time:,.0f}",
        "Est Blocks per Day": f"~ {86400/avg_block_time:,.0f}"
    }
    print_info_box("block time stats", block_data, separators=[3])

    # get mint amount for the last 60s
    print_section_header("TIME BASED REWARDS")
    minter = Minter()
    mint_amount = minter.calculate_block_provision(time_diff)
    avg_mint_amount = mint_amount / block_diff
    
    mint_data = {
        "Total TBR from 60s Sample Period": f"{mint_amount * 1e-6:,.2f} TRB",
        "Average TBR Per Block": f"{avg_mint_amount:,.1f} loya",
        "Projected Daily TBR": f"~ {avg_mint_amount * (86400/avg_block_time) * 1e-6:,.0f} TRB",
        "Projected Annual TBR": f"~ {avg_mint_amount * (86400/avg_block_time) * 365 * 1e-6:,.0f} TRB"
    }
    print_info_box("minting stats", mint_data, separators=[2])

    # get average fees paid per submit value using current block analysis
    print_section_header("REPORTING COSTS")
    txs = query_recent_reports(layerd_path)
    analysis = print_submit_value_analysis(txs, layerd_path)

    avg_fee = analysis['avg_fee_loya']
    min_gas_price = get_min_gas_price(layerd_path)
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
        "Reports per Day (every other block)": f"~ {reports_per_day:,.0f}",
        "Daily Fee Cost": f"~ {daily_fee_cost_trb:,.4f} TRB",
        "Monthly Fee Cost": f"~ {monthly_fee_cost_trb:,.1f} TRB",
        "Yearly Fee Cost": f"~ {yearly_fee_cost_trb:,.1f} TRB"
    }
    print_info_box("fee projections", projection_data)

    #  Actual reporter data
    print_section_header("REPORTERS")
    reporters, reporter_summary = get_reporters(layerd_path)
    print_info_box("reporter summary", reporter_summary, separators=[2, 4])

    # calculate profitability metrics
    print_section_header("AVG/MEDIAN VALIDATOR'S PROJECTED PROFITABILITY")

    print_info_box("stake distribution repeat", stake_summary, separators=[])
    
    avg_proportion_stake = avg_stake / total_tokens_active
    median_proportion_stake = median_stake / total_tokens_active
    avg_profit_per_block = ((avg_proportion_stake * avg_mint_amount) - (avg_fee/2)) * 1e-6
    median_profit_per_block = ((median_proportion_stake * avg_mint_amount) - (avg_fee/2)) * 1e-6
    
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
    profit_headers = ["Time Period", "Avg Projected Profit (TRB)", "Median Projected Profit (TRB)"]
    profit_rows = [
        ["Per Block", f"{avg_profit_per_block:.6f}", f"{median_profit_per_block:.6f}"],
        ["Per Minute", f"{avg_profit_1min:.6f}", f"{median_profit_1min:.6f}"],
        ["Per Hour", f"{avg_profit_1hour:.1f}", f"{median_profit_1hour:.1f}"],
        ["Per Day", f"{avg_profit_1day:.1f}", f"{median_profit_1day:.1f}"],
        ["Per Month", f"{avg_profit_1day * 30:.1f}", f"{median_profit_1day * 30:.1f}"],
        ["Per Year", f"{avg_profit_1day * 365:.0f}", f"{median_profit_1day * 365:.0f}"]
    ]
    print_table("profitability stats", profit_headers, profit_rows)

    # Generate APR analysis
    print_section_header("CURRENT APRs")
    print("Generated current_apr_chart.png")
    break_even_stake, break_even_mult = print_apr_table(total_tokens_active, avg_mint_amount, avg_fee, avg_block_time, median_stake)
    
    generate_apr_chart(total_tokens_active, avg_mint_amount, avg_fee, avg_block_time, median_stake, break_even_stake, break_even_mult)

    
    # Calculate and display individual reporter APRs
    print_section_header("CURRENT REPORTER APRs")
    reporter_aprs = calculate_reporter_aprs(reporters, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time)
    
    # Display both weighted average and median APRs in info box
    weighted_avg_apr, median_apr = calculate_apr_avgs(reporter_aprs)
    apr_averages = {
        "Weighted Avg APR": f"{weighted_avg_apr:.2f}%",
        "Median APR": f"{median_apr:.2f}%"
    }
    print_info_box("apr averages", apr_averages)
    
    print_reporter_apr_table(reporter_aprs)

    # Run scenarios analysis
    print_section_header("APR BY TOTAL STAKE")
    stake_results, targets = run_scenarios_analysis(
        total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
    )
    
    # Display target APR points in info box with current APR
    target_display = format_targets_for_display_with_apr(targets, total_tokens_active, stake_results)
    print_info_box("APR target points", target_display, separators=[2])

    print_section_header("END")

if __name__ == "__main__":
    main()