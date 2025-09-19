"""Display helper functions for formatting output"""

from termcolor import colored


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
    value_width = 78 - label_width - 1  # 78 total - label_width - padding (?)

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
    import re

    def strip_ansi(text):
        """Remove ANSI escape codes from text for width calculation"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', str(text))

    # Calculate column widths with proper padding
    col_widths = []
    for i in range(len(headers)):
        max_width = len(headers[i])
        for row in rows:
            if i < len(row):
                # Use stripped length for width calculation
                max_width = max(max_width, len(strip_ansi(row[i])))
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
            # Calculate the visual width (without ANSI codes) for proper padding
            visual_width = len(strip_ansi(cell_value))
            padding_needed = col_widths[i] - 2 - visual_width
            # Left align all columns with proper padding
            row_line += f" {cell_value}{' ' * padding_needed} "
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

    # Stakes are already in TRB units
    stakes_trb = stakes.copy()
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
    chart_width = 70  # Increased from 60 to use more space
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

    # Box plot line (aligned to left border)
    box_prefix = "│" + " " * 1  # Just the left border and one space

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

    # Enhanced scale with more numbers - aligned to left border
    scale_prefix = "│" + " " * 1
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
        "Min: ",
        "Q1: ",
        "Median: ",
        "Q3: ",
        "Max: "
    ]

    right_col = [
        f"{min_val:.1f} TRB",
        f"{q1:.1f} TRB",
        f"{q2:.1f} TRB",
        f"{q3:.1f} TRB",
        f"{max_val:.1f} TRB"
    ]

    for left_text, right_text in zip(left_col, right_col):
        # Build the line with proper padding - left align the values
        left_padded = f"│ {left_text:<{16}}"
        right_padded = f"{right_text:<{61}}" + "│"
        line = left_padded + right_padded
        print(line)

    print("└" + "─" * 78 + "┘")


def print_distribution_chart(stakes, title="VALIDATOR COUNTS BY POWER"):
    """Create an ASCII histogram of validator stakes"""
    if not stakes:
        return

    # Stakes are already in TRB units
    stakes_trb = stakes.copy()
    stakes_trb.sort()

    min_stake = min(stakes_trb)
    max_stake = max(stakes_trb)

    def create_robust_bins(min_val, max_val):
        """Create robust, non-overlapping bins that work for any data range"""
        import math

        # Handle edge case where all values are the same
        if min_val == max_val:
            return [0, min_val * 0.5, min_val, min_val * 1.5, min_val * 2]

        # Calculate the range
        range_size = max_val - min_val

        # Determine appropriate number of bins (4-6) based on data spread
        if range_size < 10:
            num_bins = 4
        elif range_size < 100:
            num_bins = 5
        else:
            num_bins = 6

        # Create bins using quantiles for better distribution
        quantiles = []
        for i in range(num_bins + 1):
            quantile = min_val + (i / num_bins) * range_size
            quantiles.append(quantile)

        # Round to nice numbers for display
        def round_to_nice(x):
            if x <= 0:
                return 0
            magnitude = 10 ** math.floor(math.log10(x))
            normalized = x / magnitude
            if normalized <= 1:
                nice = 1
            elif normalized <= 2:
                nice = 2
            elif normalized <= 5:
                nice = 5
            else:
                nice = 10
            return nice * magnitude

        # Round the quantiles to nice numbers
        nice_bins = [round_to_nice(q) for q in quantiles]

        # Ensure no duplicates and proper ordering
        unique_bins = []
        for bin_val in nice_bins:
            if not unique_bins or bin_val > unique_bins[-1]:
                unique_bins.append(bin_val)

        # Ensure we have at least 2 bins and the last bin captures the maximum
        if len(unique_bins) < 2:
            unique_bins = [0, max_val + 1]
        else:
            # Make sure the last bin captures the maximum value
            unique_bins[-1] = max_val + 0.1

        return unique_bins

    bins = create_robust_bins(min_stake, max_stake)

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

    print("┌" + "─" * 78 + "┐")
    print("│" + title.center(78) + "│")
    print("├" + "─" * 78 + "┤")

    for _i, (label, count) in enumerate(zip(bin_labels, bin_counts)):
        # Create green stars - one star per validator
        stars = colored("★" * count, 'green')

        # Calculate padding manually since colored text messes up string formatting
        stars_padding = " " * (chart_width - count)

        # Create the line with proper spacing
        line = f"│ {label:>{max_label_width}} │{stars}{stars_padding}│ {count:2d} │"
        print(line)

    print("└" + "─" * 78 + "┘")
