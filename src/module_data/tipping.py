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
            print(f"Warning: No 'query_datas' found in {config_path}, using empty config")
            return {}
    except FileNotFoundError:
        print(f"Warning: Config file {config_path} not found, using empty config")
        return {}
    except yaml.YAMLError as e:
        print(f"Warning: Error parsing config file: {e}, using empty config")
        return {}


def get_current_tip(rpc_client=None, config=None, query_data: str = None) -> Optional[float]:
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
            rest_endpoint = rpc_client.rpc_endpoint
            if rest_endpoint.endswith('/rpc'):
                rest_endpoint = rest_endpoint.replace('/rpc', '')

            # Query current tip via REST API
            url = f"{rest_endpoint}/tellor-io/layer/oracle/get_current_tip/{query_data}"
            result = subprocess.run([
                'curl', '-s', '-X', 'GET', url, '-H', 'accept: application/json'
            ], capture_output=True, text=True, check=True, timeout=10)

            # Parse JSON response
            response = json.loads(result.stdout)

            # Extract tip amount from response
            if 'tips' in response:
                tip_amount = float(response['tips'])
            elif 'tip' in response:
                tip_amount = float(response['tip'])
            elif 'amount' in response:
                tip_amount = float(response['amount'])
            elif 'value' in response:
                tip_amount = float(response['value'])
            else:
                # If the response is just a number
                tip_amount = float(response)

            # Convert from loya to TRB (assuming 1 TRB = 1e6 loya)
            return tip_amount * 1e-6

        else:
            # Fallback to layerd binary if RPC client not available
            if config and 'layerd_path' in config and query_data:
                layerd_path = config['layerd_path']
                cmd = [
                    layerd_path,
                    "query",
                    "oracle",
                    "get-current-tip",
                    query_data,
                    "--output", "json"
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    print(f"Warning: Failed to query tip for query_data: {result.stderr}")
                    return None

                # Parse the JSON response
                response = json.loads(result.stdout)

                # Extract tip amount from response
                if 'tips' in response:
                    tip_amount = float(response['tips'])
                elif 'tip' in response:
                    tip_amount = float(response['tip'])
                elif 'amount' in response:
                    tip_amount = float(response['amount'])
                elif 'value' in response:
                    tip_amount = float(response['value'])
                else:
                    # If the response is just a number
                    tip_amount = float(response)

                # Convert from loya to TRB (assuming 1 TRB = 1e6 loya)
                return tip_amount * 1e-6
            else:
                print("Warning: No RPC client, config, or query_data available")
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
    if config and 'query_datas' in config:
        query_data_config = config['query_datas']
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


def format_tips_for_display(tips: Dict[str, Optional[float]]) -> Tuple[List[str], List[List[str]]]:
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
    sorted_tips = sorted(tips.items(), key=lambda x: (x[1] is None, x[1] or 0), reverse=True)

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


def get_available_tips(rpc_client=None, config=None, selector_address: str = None) -> Optional[float]:
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
            rest_endpoint = rpc_client.rpc_endpoint
            if rest_endpoint.endswith('/rpc'):
                rest_endpoint = rest_endpoint.replace('/rpc', '')

            # Query available tips via REST API
            url = f"{rest_endpoint}/tellor-io/layer/reporter/available-tips/{selector_address}"
            result = subprocess.run([
                'curl', '-s', '-X', 'GET', url, '-H', 'accept: application/json'
            ], capture_output=True, text=True, check=True, timeout=10)

            # Parse JSON response
            response = json.loads(result.stdout)

            # Extract available tips amount from response
            if 'available_tips' in response:
                tips_amount_str = response['available_tips']
            elif 'tips' in response:
                tips_amount_str = response['tips']
            elif 'amount' in response:
                tips_amount_str = response['amount']
            elif 'value' in response:
                tips_amount_str = response['value']
            else:
                # If the response is just a number
                tips_amount_str = str(response)

            # Convert from loya to TRB (1 TRB = 1e6 loya)
            tips_amount = float(tips_amount_str) / 1e6

            return tips_amount

        else:
            # Fallback to layerd binary if RPC client not available
            if config and 'layerd_path' in config and selector_address:
                layerd_path = config['layerd_path']
                cmd = [
                    layerd_path,
                    "query",
                    "reporter",
                    "available-tips",
                    selector_address,
                    "--output", "json"
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    print(f"Warning: Failed to query available tips: {result.stderr}")
                    return None

                # Parse the JSON response
                response = json.loads(result.stdout)

                # Extract available tips amount from response
                if 'available_tips' in response:
                    tips_amount_str = response['available_tips']
                elif 'tips' in response:
                    tips_amount_str = response['tips']
                elif 'amount' in response:
                    tips_amount_str = response['amount']
                elif 'value' in response:
                    tips_amount_str = response['value']
                else:
                    # If the response is just a number
                    tips_amount_str = str(response)

                # Convert from loya to TRB (1 TRB = 1e6 loya)
                tips_amount = float(tips_amount_str) / 1e6

                return tips_amount
            else:
                print("Warning: No RPC client, config, or selector_address available")
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
        Dictionary of summary statistics
    """
    valid_tips = [tip for tip in tips.values() if tip is not None and tip > 0]

    if not valid_tips:
        return {
            "Total Tipped Queries": "0",
            "Total Tip Amount": "0.00000 TRB",
            "Average Tip": "0.00000 TRB",
            "Highest Tip": "0.00000 TRB",
            "Lowest Tip": "0.00000 TRB"
        }

    total_tipped = len(valid_tips)
    total_amount = sum(valid_tips)
    avg_tip = total_amount / len(valid_tips)
    max_tip = max(valid_tips)
    min_tip = min(valid_tips)

    return {
        "Total Tipped Queries": f"{total_tipped}",
        "Total Tip Amount": f"{total_amount:.5f} TRB",
        "Average Tip": f"{avg_tip:.5f} TRB",
        "Highest Tip": f"{max_tip:.5f} TRB",
        "Lowest Tip": f"{min_tip:.5f} TRB"
    }
