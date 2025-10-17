"""Tipping module for querying current tips for various price feeds"""

import json
import subprocess
from typing import Dict, List, Optional, Tuple

import yaml


def load_query_datas(config_path: str = "config.yaml") -> Dict[str, str]:
    """
    Load queryDatas from config file.

    Args:
        config_path: Path to the config file

    Returns:
        Dictionary mapping price feed names to query data hex strings
    """
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        if "query_datas" in config:
            return config["query_datas"]
        else:
            print(
                f"Warning: No 'query_datas' found in {config_path}, using empty config"
            )
            return {}
    except FileNotFoundError:
        print(f"Warning: Config file {config_path} not found, using empty config")
        return {}
    except yaml.YAMLError as e:
        print(f"Warning: Error parsing config file: {e}, using empty config")
        return {}


def get_current_tip(
    rpc_client=None, config=None, query_data: str = None
) -> Optional[float]:
    """
    Query the current tip for a specific query data using REST API.

    Args:
        rpc_client: RPC client instance
        config: Configuration dictionary
        query_data: The query data hex string

    Returns:
        Current tip amount in TRB, or None if query fails
    """
    try:
        if rpc_client is not None and query_data:
            # Get the REST endpoint from RPC client
            if rpc_client.is_localhost:
                # For localhost, REST API is typically on port 1317
                rest_endpoint = rpc_client.rpc_endpoint.replace(":26657", ":1317")
            else:
                rest_endpoint = rpc_client.rpc_endpoint
            if rest_endpoint.endswith("/rpc"):
                rest_endpoint = rest_endpoint.replace("/rpc", "")

            # Query current tip via REST API
            url = f"{rest_endpoint}/tellor-io/layer/oracle/get_current_tip/{query_data}"
            result = subprocess.run(
                ["curl", "-s", "-X", "GET", url, "-H", "accept: application/json"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            # Parse JSON response
            response = json.loads(result.stdout)

            # Extract tip amount from response
            if "tips" in response:
                tip_amount = float(response["tips"])
            elif "tip" in response:
                tip_amount = float(response["tip"])
            elif "amount" in response:
                tip_amount = float(response["amount"])
            elif "value" in response:
                tip_amount = float(response["value"])
            else:
                # If the response is just a number
                tip_amount = float(response)

            # Convert from loya to TRB (assuming 1 TRB = 1e6 loya)
            return tip_amount * 1e-6

        else:
            # No fallback available
            print("No RPC client available for tip query")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to query tip for query_data: {e}")
        return None
    except subprocess.TimeoutExpired:
        print("Warning: Query timeout for query_data")
        return None
    except json.JSONDecodeError:
        print("Warning: Invalid JSON response for query_data")
        return None
    except (ValueError, KeyError) as e:
        print(f"Warning: Error parsing tip response: {e}")
        return None
    except Exception as e:
        print(f"Warning: Unexpected error querying tip: {e}")
        return None


def get_all_current_tips(rpc_client=None, config=None) -> Dict[str, Optional[float]]:
    """
    Query current tips for all configured price feeds.

    Args:
        rpc_client: RPC client instance
        config: Configuration dictionary

    Returns:
        Dictionary mapping price feed names to their current tip amounts
    """
    tips = {}

    # Load queryDatas from config
    if config and "query_datas" in config:
        query_data_config = config["query_datas"]
    else:
        query_data_config = load_query_datas()

    if not query_data_config:
        print("No queryDatas configured - skipping tip queries")
        return tips

    print("Querying current tips for all price feeds...")

    for feed_name, query_data in query_data_config.items():
        tip = get_current_tip(rpc_client, config, query_data)
        tips[feed_name] = tip

    return tips


def format_tips_for_display(
    tips: Dict[str, Optional[float]],
) -> Tuple[List[str], List[List[str]]]:
    """
    Format tips data for display in a table.

    Args:
        tips: Dictionary of price feed names to tip amounts

    Returns:
        Tuple of (headers, rows) for table display
    """
    headers = ["Price Feed", "Current Tip (TRB)"]
    rows = []

    # Sort by tip amount (descending), with None values at the end
    sorted_tips = sorted(
        tips.items(), key=lambda x: (x[1] is None, x[1] or 0), reverse=True
    )

    for feed_name, tip in sorted_tips:
        if tip is not None and tip > 0:
            # Tipped query - green and bold, with consistent padding
            tip_str = f"\033[32m\033[1m{tip:.5f}\033[0m"
        elif tip is not None:
            tip_str = f"{tip:.5f}"
        else:
            tip_str = "0.00000"
        rows.append([feed_name, tip_str])

    return headers, rows


def get_total_tips(rpc_client=None) -> Optional[float]:
    """
    Query the total amount of tips made on the chain all time using REST API.

    Args:
        rpc_client: RPC client instance to get the correct REST endpoint

    Returns:
        Total tips amount in TRB, or None if query fails
    """
    try:
        # Use the RPC client's REST endpoint
        if rpc_client is None:
            print("Warning: RPC client not provided for total tips query")
            return None

        if rpc_client.is_localhost:
            # For localhost, REST API is typically on port 1317
            rest_endpoint = rpc_client.rpc_endpoint.replace(":26657", ":1317")
        else:
            rest_endpoint = rpc_client.rpc_endpoint
        if rest_endpoint.endswith("/rpc"):
            rest_endpoint = rest_endpoint.replace("/rpc", "")
        url = f"{rest_endpoint}/tellor-io/layer/oracle/get_tip_total"

        result = subprocess.run(
            ["curl", "-s", "-X", "GET", url, "-H", "accept: application/json"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        # Parse JSON response
        response = json.loads(result.stdout)

        # Extract total tips amount from response
        if "total_tips" in response:
            tips_amount = float(response["total_tips"])
        elif "tips" in response:
            tips_amount = float(response["tips"])
        elif "amount" in response:
            tips_amount = float(response["amount"])
        elif "value" in response:
            tips_amount = float(response["value"])
        else:
            # If the response is just a number
            tips_amount = float(response)

        # Convert from loya to TRB (assuming 1 TRB = 1e6 loya)
        return tips_amount * 1e-6

    except subprocess.TimeoutExpired:
        print("Warning: Query timeout for total tips")
        return None
    except json.JSONDecodeError:
        print("Warning: Invalid JSON response for total tips")
        return None
    except (ValueError, KeyError) as e:
        print(f"Warning: Error parsing total tips response: {e}")
        return None
    except Exception as e:
        print(f"Warning: Unexpected error querying total tips: {e}")
        return None


def get_available_tips(
    rpc_client=None, config=None, selector_address: str = None
) -> Optional[float]:
    """
    Query the available tips for a specific selector address using REST API.

    Args:
        rpc_client: RPC client instance
        config: Configuration dictionary
        selector_address: The selector address

    Returns:
        Available tips amount in TRB, or None if query fails
    """
    try:
        if rpc_client is not None and selector_address:
            # Get the REST endpoint from RPC client
            if rpc_client.is_localhost:
                # For localhost, REST API is typically on port 1317
                rest_endpoint = rpc_client.rpc_endpoint.replace(":26657", ":1317")
            else:
                rest_endpoint = rpc_client.rpc_endpoint
            if rest_endpoint.endswith("/rpc"):
                rest_endpoint = rest_endpoint.replace("/rpc", "")

            # Query available tips via REST API
            url = f"{rest_endpoint}/tellor-io/layer/reporter/available-tips/{selector_address}"
            result = subprocess.run(
                ["curl", "-s", "-X", "GET", url, "-H", "accept: application/json"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            # Parse JSON response
            response = json.loads(result.stdout)

            # Extract available tips amount from response
            if "available_tips" in response:
                tips_amount_str = response["available_tips"]
            elif "tips" in response:
                tips_amount_str = response["tips"]
            elif "amount" in response:
                tips_amount_str = response["amount"]
            elif "value" in response:
                tips_amount_str = response["value"]
            else:
                # If the response is just a number
                tips_amount_str = str(response)

            # Convert from loya to TRB (1 TRB = 1e6 loya)
            tips_amount = float(tips_amount_str) / 1e6

            return tips_amount

        else:
            # No fallback available
            print("No RPC client available for available tips query")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to query available tips: {e}")
        return None
    except subprocess.TimeoutExpired:
        print("Warning: Query timeout for available tips")
        return None
    except json.JSONDecodeError:
        print("Warning: Invalid JSON response for available tips")
        return None
    except (ValueError, KeyError) as e:
        print(f"Warning: Error parsing available tips response: {e}")
        return None
    except Exception as e:
        print(f"Warning: Unexpected error querying available tips: {e}")
        return None


def get_tipping_summary(tips: Dict[str, Optional[float]]) -> Dict[str, str]:
    """
    Generate summary statistics for tipping data.

    Args:
        tips: Dictionary of price feed names to tip amounts

    Returns:
        Dictionary of summary statistics in the requested order
    """
    valid_tips = [tip for tip in tips.values() if tip is not None and tip > 0]

    if not valid_tips:
        return {
            "Currently Tipped Queries": "0",
            "Total Tip Amount": "0.00000 TRB",
            "Average Tip": "0.00000 TRB",
            "Highest Tip": "0.00000 TRB",
            "Lowest Tip": "0.00000 TRB",
        }

    total_tipped = len(valid_tips)
    total_amount = sum(valid_tips)
    avg_tip = total_amount / len(valid_tips)
    max_tip = max(valid_tips)
    min_tip = min(valid_tips)

    return {
        "Currently Tipped Queries": f"{total_tipped}",
        "Total Tip Amount": f"{total_amount:.5f} TRB",
        "Average Tip": f"{avg_tip:.5f} TRB",
        "Highest Tip": f"{max_tip:.5f} TRB",
        "Lowest Tip": f"{min_tip:.5f} TRB",
    }


def get_all_denom_owners(rest_endpoint: str) -> List[str]:
    """
    Get all loya denom owners using pagination.

    Args:
        rest_endpoint: REST API endpoint (without /rpc)

    Returns:
        List of all addresses that own loya tokens
    """
    all_addresses = []
    next_key = None
    page = 1

    print("Fetching all loya denom owners...")

    while True:
        # Build URL with pagination
        url = f"{rest_endpoint}/cosmos/bank/v1beta1/denom_owners/loya"
        if next_key:
            url += f"?pagination.key={next_key}"

        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "GET", url, "-H", "accept: application/json"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )

            response = json.loads(result.stdout)

            # Extract addresses from this page
            denom_owners = response.get("denom_owners", [])
            page_addresses = [owner["address"] for owner in denom_owners]
            all_addresses.extend(page_addresses)

            print(
                f"  Page {page}: {len(page_addresses)} addresses (total: {len(all_addresses)})"
            )

            # Check if there are more pages
            pagination = response.get("pagination", {})
            next_key = pagination.get("next_key")

            if not next_key:
                break

            page += 1

        except subprocess.TimeoutExpired:
            print(f"Warning: Timeout fetching page {page}")
            break
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON response on page {page}")
            break
        except Exception as e:
            print(f"Warning: Error fetching page {page}: {e}")
            break

    print(f"  Retrieved {len(all_addresses)} total addresses")
    return all_addresses


def get_user_tip_total(rest_endpoint: str, address: str) -> Optional[float]:
    """
    Get tip total for a specific user address.

    Args:
        rest_endpoint: REST API endpoint (without /rpc)
        address: User address to query

    Returns:
        Tip total in TRB, or None if query fails
    """
    try:
        url = f"{rest_endpoint}/tellor-io/layer/oracle/get_user_tip_total/{address}"
        result = subprocess.run(
            ["curl", "-s", "-X", "GET", url, "-H", "accept: application/json"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        response = json.loads(result.stdout)

        # Extract tip total from response
        if "total_tips" in response:
            tip_amount = float(response["total_tips"])
        elif "tip_total" in response:
            tip_amount = float(response["tip_total"])
        elif "tips" in response:
            tip_amount = float(response["tips"])
        elif "amount" in response:
            tip_amount = float(response["amount"])
        elif "value" in response:
            tip_amount = float(response["value"])
        else:
            # If the response is just a number
            tip_amount = float(response)

        # Convert from loya to TRB (assuming 1 TRB = 1e6 loya)
        return tip_amount * 1e-6

    except subprocess.TimeoutExpired:
        return None
    except json.JSONDecodeError:
        return None
    except (ValueError, KeyError):
        return None
    except Exception:
        return None


def get_all_user_tip_totals(rest_endpoint: str) -> List[Tuple[str, float]]:
    """
    Get tip totals for all loya denom owners.

    Args:
        rest_endpoint: REST API endpoint (without /rpc)

    Returns:
        List of tuples (address, tip_total) for addresses with tip_total > 0
    """
    # Get all addresses
    addresses = get_all_denom_owners(rest_endpoint)

    tip_totals = []
    print(f"\nQuerying tip totals for {len(addresses)} addresses...")

    for i, address in enumerate(addresses, 1):
        if i % 10 == 0 or i == len(addresses):
            print(f"  Progress: {i}/{len(addresses)} addresses queried")

        tip_total = get_user_tip_total(rest_endpoint, address)

        if tip_total is not None and tip_total > 0:
            tip_totals.append((address, tip_total))

    # Sort by tip total (descending)
    tip_totals.sort(key=lambda x: x[1], reverse=True)

    print(f"  Found {len(tip_totals)} addresses with tip totals > 0")
    return tip_totals


def format_user_tip_totals_for_display(
    tip_totals: List[Tuple[str, float]],
) -> Tuple[List[str], List[List[str]]]:
    """
    Format user tip totals for display in a table.

    Args:
        tip_totals: List of tuples (address, tip_total)

    Returns:
        Tuple of (headers, rows) for table display
    """
    headers = ["Address", "Total Tips (TRB)"]
    rows = []

    for address, tip_total in tip_totals:
        rows.append([address, f"{tip_total:.5f}"])

    return headers, rows
