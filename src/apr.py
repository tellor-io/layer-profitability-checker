import unicodedata

import matplotlib.pyplot as plt
import numpy as np


def calculate_apr_by_stake(
    stake_amount, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
):
    """Calculate APR for a given stake amount"""
    proportion_stake = stake_amount / total_tokens_active
    profit_per_block = (proportion_stake * avg_mint_amount) - (avg_fee / 2)

    # Convert to annual profit
    blocks_per_year = (365 * 24 * 3600) / avg_block_time
    annual_profit = profit_per_block * blocks_per_year

    # APR = (annual_profit / stake_amount) * 100
    apr = (annual_profit / stake_amount) * 100
    return apr


def calculate_break_even_stake(
    total_tokens_active, avg_mint_amount, avg_fee, avg_block_time, median_stake
):
    """Calculate the break-even stake amount where APR is approximately 0%"""
    # Search more precisely in the range where we expect break-even
    for test_mult in np.linspace(0.05, 0.25, 2000):  # More points in likely range
        test_stake = median_stake * test_mult
        test_apr = calculate_apr_by_stake(
            test_stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
        )
        if abs(test_apr) < 1.0:  # Within 1% of zero
            return test_stake, test_mult
    return None, None


def generate_apr_chart(
    total_tokens_active,
    avg_mint_amount,
    avg_fee,
    avg_block_time,
    median_stake,
    break_even_stake,
    break_even_mult,
):
    """Generate APR chart for different stake amounts"""
    # Create stake range from 1% to 200% of median stake
    min_stake = median_stake * 0.01
    max_stake = median_stake * 2.0
    stake_amounts = np.linspace(min_stake, max_stake, 100)

    aprs = []
    for stake in stake_amounts:
        apr = calculate_apr_by_stake(
            stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
        )
        aprs.append(apr)

    # get break even apr if break_even_stake is provided
    if break_even_stake:
        break_even_apr = calculate_apr_by_stake(
            break_even_stake,
            total_tokens_active,
            avg_mint_amount,
            avg_fee,
            avg_block_time,
        )

    # Create the plot
    plt.figure(figsize=(12, 8))
    plt.plot(stake_amounts * 1e-6, aprs, linewidth=2, color="blue")
    plt.xlabel("Individual Stake Amount (TRB)", fontsize=12)
    plt.ylabel("Current APR (%)", fontsize=12)
    plt.title("Current APR vs Individual Stake Amount", fontsize=14, fontweight="bold")
    plt.grid(True, alpha=0.3)

    # Set y-axis limits
    plt.ylim(-500, 1000)

    # Add median stake point
    median_apr = calculate_apr_by_stake(
        median_stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
    )
    plt.plot(median_stake, median_apr, "ro", markersize=8, label="Current Median")
    plt.annotate(
        f"({median_stake:.2f} TRB, {median_apr:.1f}% APR)",
        xy=(median_stake, median_apr),
        xytext=(median_stake + 10, median_apr + 50),
        fontsize=10,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": "red", "alpha": 0.7},
    )

    # Add break-even point if found
    if break_even_stake:
        plt.plot(
            break_even_stake, break_even_apr, "go", markersize=8, label="Break-even"
        )
        plt.annotate(
            f"({break_even_stake:.2f} TRB, {break_even_apr:.1f}% APR)",
            xy=(break_even_stake, break_even_apr),
            xytext=(break_even_stake + 5, break_even_apr + 80),
            fontsize=10,
            fontweight="bold",
            arrowprops={"arrowstyle": "->", "color": "green", "alpha": 0.7},
        )

    plt.legend()
    plt.tight_layout()
    plt.savefig("current_apr_chart.png", dpi=300, bbox_inches="tight")

    return stake_amounts, aprs


def print_info_box(title, data_dict):
    """Print a beautifully formatted information box"""
    print("\n" + "┌" + "─" * 78 + "┐")
    print("│" + " " * 78 + "│")
    print("│" + title.center(78) + "│")
    print("│" + " " * 78 + "│")
    print("├" + "─" * 78 + "┤")

    for key, value in data_dict.items():
        line = f"{key}: {value}"
        print("│" + f" {line:<76}" + "│")

    print("│" + " " * 78 + "│")
    print("└" + "─" * 78 + "┘")


def print_apr_table(
    total_tokens_active, avg_mint_amount, avg_fee, avg_block_time, median_stake
):
    """Print a beautifully formatted table of APR values for different stake percentiles"""

    # Find break-even point first
    break_even_stake = None
    break_even_mult = None

    # Search more precisely in the range where we expect break-even
    for test_mult in np.linspace(0.05, 0.25, 2000):  # More points in likely range
        test_stake = median_stake * test_mult
        test_apr = calculate_apr_by_stake(
            test_stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
        )
        if abs(test_apr) < 1.0:  # Within 1% of zero
            break_even_stake = test_stake
            break_even_mult = test_mult
            break

    # Calculate minimum multiplier to get at least 1 TRB
    min_mult_for_1trb = 1e6 / median_stake  # 1 TRB in loya / median_stake in loya

    # More granular multipliers focusing on low values, ensuring minimum is 1 TRB
    base_multipliers = [
        0.02,
        0.05,
        0.08,
        0.1,
        0.15,
        0.2,
        0.25,
        0.3,
        0.4,
        0.5,
        0.75,
        1.0,
        1.25,
        1.5,
        2.0,
        3.0,
        5.0,
        10.0,
        20.0,
    ]

    # Filter multipliers to ensure minimum stake is 1 TRB and add the exact 1 TRB multiplier
    multipliers = [min_mult_for_1trb] + [
        mult for mult in base_multipliers if mult * median_stake >= 1e6
    ]
    multipliers = sorted(set(multipliers))  # Remove duplicates and sort

    # Add median and break-even multipliers to ensure they appear in the table
    multipliers.append(1.0)  # Median multiplier
    if break_even_mult:
        multipliers.append(break_even_mult)  # Break-even multiplier
    multipliers = sorted(set(multipliers))  # Remove duplicates and sort

    # Prepare table data
    headers = ["Stake Amount (TRB)", "Max APR", "Yearly Earnings (TRB)", "% of Network"]

    rows = []
    for mult in multipliers:
        stake = median_stake * mult
        apr = calculate_apr_by_stake(
            stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
        )
        percent_of_total = (stake / total_tokens_active) * 100

        # Calculate yearly earnings in TRB
        yearly_earnings = (stake * 1e-6) * (apr / 100)

        # Format APR with appropriate precision
        if abs(apr) >= 1000:
            apr_str = f"{apr:,.0f}%"
        else:
            apr_str = f"{apr:,.0f}%"

        # Format yearly earnings
        if abs(yearly_earnings) >= 1000:
            earnings_str = f"{yearly_earnings:,.0f}"
        elif abs(yearly_earnings) >= 10:
            earnings_str = f"{yearly_earnings:,.1f}"
        else:
            earnings_str = f"{yearly_earnings:,.2f}"

        # Format stake amount with emoji indicators
        stake_str = f"{stake * 1e-6:,.1f}"

        # Add emojis for special stakes
        if abs(mult - 1.0) < 0.001:  # Median stake
            stake_str = f"📊 {stake_str}"
        elif (
            break_even_mult and abs(mult - break_even_mult) < 0.001
        ):  # Break-even stake
            stake_str = f"⚖️  {stake_str}"

        # Format percentage with consistent spacing
        percent_str = f"{percent_of_total:.2f}%"

        rows.append([stake_str, apr_str, earnings_str, percent_str])

    # Print the table with custom alignment
    print_apr_table_with_alignment(headers, rows)

    # Print legend
    print("\n📊 Median Validator Stake    ⚖️  Break-even Stake")

    return break_even_stake, break_even_mult


def print_apr_table_with_alignment(headers, rows):
    """Print APR table with right-aligned first column and left-aligned other columns"""

    def get_visual_width(text):
        """Calculate the visual width of text, accounting for emojis"""
        visual_width = 0
        i = 0

        while i < len(text):
            char = text[i]
            char_code = ord(char)

            # Special handling for specific emoji sequences
            if char == "⚖" and i + 1 < len(text) and ord(text[i + 1]) == 0xFE0F:
                # ⚖️ (scales with variation selector) takes 3 terminal spaces
                visual_width += 1
                i += 2  # Skip both the emoji and variation selector
            elif char == "📊":
                # 📊 takes 2 terminal spaces
                visual_width += 2
                i += 1
            elif char_code >= 0x1F000:  # Other emoji range
                visual_width += 2  # Most emojis take 2 character spaces
                i += 1
            elif unicodedata.east_asian_width(char) in ("F", "W"):  # Full-width or Wide
                visual_width += 2
                i += 1
            elif char_code >= 0x2600 and char_code <= 0x26FF:  # Miscellaneous symbols
                visual_width += 2
                i += 1
            elif (
                char_code >= 0xFE00 and char_code <= 0xFE0F
            ):  # Variation selectors (standalone)
                # These don't add visual width when standalone, skip
                i += 1
            else:
                visual_width += 1  # Regular character
                i += 1

        return visual_width

    # Calculate column widths with proper padding, accounting for visual width
    col_widths = []
    for i in range(len(headers)):
        max_width = len(headers[i])
        for row in rows:
            if i < len(row):
                visual_width = get_visual_width(str(row[i]))
                max_width = max(max_width, visual_width)
        col_widths.append(max_width + 2)  # Add 2 for padding (1 space on each side)

    # Calculate total width: sum of column widths + separators between columns + outer borders
    total_width = sum(col_widths) + len(col_widths) - 1

    # Header
    print("\n" + "┌" + "─" * total_width + "┐")

    # Column headers
    header_line = "│"
    for i, header in enumerate(headers):
        header_line += header.center(col_widths[i])
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

    # Data rows with custom alignment
    for i, row in enumerate(rows):
        row_line = "│"
        for j in range(len(headers)):
            cell_value = str(row[j]) if j < len(row) else ""

            # Calculate padding needed based on visual vs actual width
            visual_width = get_visual_width(cell_value)

            # Right-align first column, left-align others
            if j == 0:  # First column (Stake Amount) - right align
                padding_needed = col_widths[j] - 2 - visual_width
                row_line += f" {' ' * padding_needed}{cell_value} "
            else:  # Other columns - left align
                padding_needed = col_widths[j] - 2 - visual_width
                row_line += f" {cell_value}{' ' * padding_needed} "

            if j < len(headers) - 1:
                row_line += "│"
        row_line += "│"
        print(row_line)

        # Add empty line every 5 rows for readability
        if (i + 1) % 5 == 0 and i < len(rows) - 1:
            empty_line = "│"
            for j, width in enumerate(col_widths):
                empty_line += " " * width
                if j < len(col_widths) - 1:
                    empty_line += "│"
            empty_line += "│"
            print(empty_line)

    # Bottom border
    bottom_line = "└"
    for i, width in enumerate(col_widths):
        bottom_line += "─" * width
        if i < len(col_widths) - 1:
            bottom_line += "┴"
    bottom_line += "┘"
    print(bottom_line)


def calculate_reporter_aprs(
    reporters_data, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
):
    """Calculate APR for each active reporter and return sorted list"""
    reporter_aprs = []

    for reporter in reporters_data["active"]:
        # Power is in TRB (same units as total_tokens_active)
        power_trb = int(reporter["power"]) if reporter["power"].isdigit() else 0
        if power_trb > 0:  # Only calculate for reporters with actual power
            apr = calculate_apr_by_stake(
                power_trb, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
            )

            reporter_aprs.append(
                {
                    "moniker": reporter["moniker"] or reporter["address"][:12] + "...",
                    "power_trb": power_trb,
                    "apr": apr,
                    "commission_rate": float(reporter["commission_rate"]) * 100
                    if reporter["commission_rate"]
                    else 0,
                }
            )

    # Sort by power (descending)
    reporter_aprs.sort(key=lambda x: x["power_trb"], reverse=True)
    return reporter_aprs


def print_reporter_apr_table(reporter_aprs):
    """Print a table of reporter APRs with custom alignment"""
    if not reporter_aprs:
        print("No active reporters with power found.")
        return

    headers = ["Reporter", "Power", "Max APR", "Commission Rate"]
    rows = []

    for reporter in reporter_aprs:
        # Format APR
        apr = reporter["apr"]
        if abs(apr) >= 100:
            apr_str = f"{apr:,.0f}%"
        else:
            apr_str = f"{apr:,.1f}%"

        # Format commission rate
        comm_str = f"{reporter['commission_rate']:.0f}%"

        rows.append(
            [
                reporter["moniker"][:20],  # Truncate long monikers
                f"{reporter['power_trb']:,}",
                apr_str,
                comm_str,
            ]
        )

    # Custom table printing with specific alignment
    print_reporter_table_with_alignment(headers, rows)


def print_reporter_table_with_alignment(headers, rows):
    """Print a table with right-aligned first column and left-aligned other columns"""

    def get_visual_width(text):
        """Calculate the visual width of text, accounting for emojis"""
        visual_width = 0
        i = 0

        while i < len(text):
            char = text[i]
            char_code = ord(char)

            # Special handling for specific emoji sequences
            if char == "⚖" and i + 1 < len(text) and ord(text[i + 1]) == 0xFE0F:
                # ⚖️ (scales with variation selector) takes 3 terminal spaces
                visual_width += 3
                i += 2  # Skip both the emoji and variation selector
            elif char == "📊":
                # 📊 takes 2 terminal spaces
                visual_width += 2
                i += 1
            elif char_code >= 0x1F000:  # Other emoji range
                visual_width += 2  # Most emojis take 2 character spaces
                i += 1
            elif unicodedata.east_asian_width(char) in ("F", "W"):  # Full-width or Wide
                visual_width += 2
                i += 1
            elif char_code >= 0x2600 and char_code <= 0x26FF:  # Miscellaneous symbols
                visual_width += 2
                i += 1
            elif (
                char_code >= 0xFE00 and char_code <= 0xFE0F
            ):  # Variation selectors (standalone)
                # These don't add visual width when standalone, skip
                i += 1
            else:
                visual_width += 1  # Regular character
                i += 1

        return visual_width

    # Calculate column widths with proper padding, accounting for visual width
    col_widths = []
    for i in range(len(headers)):
        max_width = len(headers[i])
        for row in rows:
            if i < len(row):
                visual_width = get_visual_width(str(row[i]))
                max_width = max(max_width, visual_width)
        col_widths.append(max_width + 2)  # Add 2 for padding (1 space on each side)

    # Calculate total width: sum of column widths + separators between columns + outer borders
    total_width = sum(col_widths) + len(col_widths) - 1

    # Header
    print("\n" + "┌" + "─" * total_width + "┐")

    # Column headers
    header_line = "│"
    for i, header in enumerate(headers):
        header_line += header.center(col_widths[i])
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

    # Data rows with custom alignment
    for i, row in enumerate(rows):
        row_line = "│"
        for j in range(len(headers)):
            cell_value = str(row[j]) if j < len(row) else ""

            # Calculate padding needed based on visual vs actual width
            visual_width = get_visual_width(cell_value)

            # Right-align first column, left-align others
            if j == 0:  # First column (Reporter) - right align
                padding_needed = col_widths[j] - 2 - visual_width
                row_line += f" {' ' * padding_needed}{cell_value} "
            else:  # Other columns - left align
                padding_needed = col_widths[j] - 2 - visual_width
                row_line += f" {cell_value}{' ' * padding_needed} "

            if j < len(headers) - 1:
                row_line += "│"
        row_line += "│"
        print(row_line)

        # Add empty line every 5 rows for readability
        if (i + 1) % 5 == 0 and i < len(rows) - 1:
            empty_line = "│"
            for j, width in enumerate(col_widths):
                empty_line += " " * width
                if j < len(col_widths) - 1:
                    empty_line += "│"
            empty_line += "│"
            print(empty_line)

    # Bottom border
    bottom_line = "└"
    for i, width in enumerate(col_widths):
        bottom_line += "─" * width
        if i < len(col_widths) - 1:
            bottom_line += "┴"
    bottom_line += "┘"
    print(bottom_line)


def calculate_apr_avgs(reporter_aprs):
    """Calculate both weighted average and median APR of all active reporters"""
    if not reporter_aprs:
        return 0.0, 0.0

    total_weighted_apr = 0.0
    total_power = 0
    apr_values = []

    for reporter in reporter_aprs:
        power = reporter["power_trb"]
        apr = reporter["apr"]
        total_weighted_apr += apr * power
        total_power += power
        apr_values.append(apr)

    if total_power == 0:
        return 0.0, 0.0

    weighted_avg = total_weighted_apr / total_power

    # Calculate median
    apr_values.sort()
    n = len(apr_values)
    if n % 2 == 0:
        median_apr = (apr_values[n // 2 - 1] + apr_values[n // 2]) / 2
    else:
        median_apr = apr_values[n // 2]

    return weighted_avg, median_apr
