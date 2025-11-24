"""Query and analyze selector data for reporters."""
import json
import subprocess
from typing import List, Dict, Optional


def get_reporter_selectors(
    rest_endpoint: str, reporter_address: str
) -> Optional[Dict]:
    """
    Query the selections-to endpoint for a specific reporter.
    
    Args:
        rest_endpoint: The REST API endpoint base URL
        reporter_address: The reporter address to query
        
    Returns:
        Dictionary with reporter address and selections list, or None on error
    """
    url = f"{rest_endpoint}/tellor-io/layer/reporter/selections-to/{reporter_address}"
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "accept: application/json", url],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"  ⚠️  Error querying selectors for {reporter_address}: {e}")
        return None


def get_all_reporter_selectors(
    rest_endpoint: str, reporters: Dict[str, List[Dict]]
) -> List[Dict]:
    """
    Query selector data for all active reporters.
    
    Args:
        rest_endpoint: The REST API endpoint base URL
        reporters: Dict with 'active', 'inactive', 'jailed' keys containing reporter lists
        
    Returns:
        List of dictionaries with 'address' and 'num_selectors' fields
    """
    results = []
    
    # Get only active reporters from the dict
    active_reporters = reporters.get("active", [])
    
    print(f"\nQuerying {len(active_reporters)} active reporters...")
    
    for i, reporter in enumerate(active_reporters, 1):
        reporter_address = reporter.get("address")
        if not reporter_address:
            continue
            
        # Progress indicator every 10 reporters
        if i % 10 == 0 or i == len(active_reporters):
            print(f"  Progress: {i}/{len(active_reporters)} reporters queried")
        
        selector_data = get_reporter_selectors(rest_endpoint, reporter_address)
        
        if selector_data:
            num_selectors = len(selector_data.get("selections", []))
            results.append({
                "address": reporter_address,
                "moniker": reporter.get("moniker", "Unknown"),
                "num_selectors": num_selectors,
            })
        else:
            # If query fails, still add with 0 selectors
            results.append({
                "address": reporter_address,
                "moniker": reporter.get("moniker", "Unknown"),
                "num_selectors": 0,
            })
    
    return results


def calculate_selector_profitability(
    rest_endpoint: str,
    reporters: Dict[str, List[Dict]],
    reporter_aprs: List[Dict],
) -> List[Dict]:
    """
    Calculate expected yearly profitability for each selector.
    
    Args:
        rest_endpoint: The REST API endpoint base URL
        reporters: Dict with 'active', 'inactive', 'jailed' keys containing reporter lists
        reporter_aprs: List of reporter APR data with address, power, apr, commission_rate
        
    Returns:
        List of selector profitability data
    """
    selector_profits = []
    active_reporters = reporters.get("active", [])
    
    # Create a lookup dict for reporter APRs by address
    apr_lookup = {r["address"]: r for r in reporter_aprs}
    
    print(f"\nCalculating selector profitability for {len(active_reporters)} active reporters...")
    
    for i, reporter in enumerate(active_reporters, 1):
        reporter_address = reporter.get("address")
        if not reporter_address:
            continue
        
        # Progress indicator
        if i % 10 == 0 or i == len(active_reporters):
            print(f"  Progress: {i}/{len(active_reporters)} reporters processed")
        
        # Get reporter APR data
        apr_data = apr_lookup.get(reporter_address)
        if not apr_data:
            continue
        
        reporter_power = apr_data["power_trb"]
        reporter_apr = apr_data["apr"]
        commission_rate_pct = apr_data["commission_rate"]  # Already in percentage (0-100)
        commission_rate = commission_rate_pct / 100.0  # Convert to decimal (0-1)
        reporter_moniker = apr_data["moniker"]
        
        # Skip reporters with negative APR (unprofitable)
        if reporter_apr < 0:
            continue
        
        # Calculate reporter's yearly profit
        reporter_yearly_profit = reporter_power * (reporter_apr / 100.0)
        
        # Calculate total selector pool (commission_rate% goes to selectors)
        total_selector_pool = reporter_yearly_profit * commission_rate
        
        # Get selector details
        selector_data = get_reporter_selectors(rest_endpoint, reporter_address)
        if not selector_data or "selections" not in selector_data:
            continue
        
        # Calculate each selector's share
        for selection in selector_data["selections"]:
            selector_address = selection.get("selector")
            delegation_total = int(selection.get("delegations_total", 0)) * 1e-6  # Convert loya to TRB
            
            if delegation_total == 0:
                continue
            
            # Selector's expected yearly earnings
            # = (selector_delegation / reporter_power) * total_selector_pool
            selector_yearly_earnings = (delegation_total / reporter_power) * total_selector_pool
            
            selector_profits.append({
                "selector_address": selector_address,
                "reporter_address": reporter_address,
                "reporter_moniker": reporter_moniker,
                "reporter_power": reporter_power,
                "reporter_apr": reporter_apr,
                "commission_rate": commission_rate_pct,  # Store as percentage for display
                "delegation_amount": delegation_total,
                "yearly_earnings": selector_yearly_earnings,
            })
    
    return selector_profits


def format_selector_data_for_display(selector_data: List[Dict]) -> tuple:
    """
    Format selector data for table display.
    
    Args:
        selector_data: List of dictionaries with reporter selector info
        
    Returns:
        Tuple of (headers, rows) for table display
    """
    headers = ["Reporter", "Address", "Num Selectors"]
    
    # Sort by number of selectors descending
    sorted_data = sorted(
        selector_data, 
        key=lambda x: x["num_selectors"], 
        reverse=True
    )
    
    rows = []
    for data in sorted_data:
        moniker = data["moniker"][:20]  # Truncate long monikers
        address = data["address"]
        num_selectors = str(data["num_selectors"])
        rows.append([moniker, address, num_selectors])
    
    return headers, rows


def format_selector_profitability_for_display(selector_profits: List[Dict]) -> tuple:
    """
    Format selector profitability data for table display.
    
    Args:
        selector_profits: List of selector profitability data
        
    Returns:
        Tuple of (headers, rows) for table display
    """
    headers = [
        "Selector Address",
        "Reporter",
        "Delegation (TRB)",
        "Reporter APR",
        "Commission",
        "Yearly Earnings (TRB)"
    ]
    
    # Sort by yearly earnings descending
    sorted_data = sorted(
        selector_profits,
        key=lambda x: x["yearly_earnings"],
        reverse=True
    )
    
    rows = []
    for data in sorted_data:
        selector_addr = data["selector_address"][:20] + "..."
        reporter = data["reporter_moniker"][:15]
        delegation = f"{data['delegation_amount']:.2f}"
        apr = f"{data['reporter_apr']:.1f}%"
        commission = f"{data['commission_rate']:.0f}%"
        earnings = f"{data['yearly_earnings']:.2f}"
        
        rows.append([selector_addr, reporter, delegation, apr, commission, earnings])
    
    return headers, rows

