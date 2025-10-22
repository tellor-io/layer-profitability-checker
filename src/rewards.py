"""
Rewards-related functionality for Tellor Layer profitability checker.
Handles mint events, extra rewards pool, and reward calculations.
"""

import json
import subprocess
from typing import Any, Dict, Optional, Tuple

from .chain_data.rpc_client import TellorRPCClient


def query_mint_events(
    start_height=None, end_height=None, rpc_endpoint=None, rpc_client=None
):
    """
    Query mint events from recent blocks using CometBFT RPC
    Returns dict with total minted amounts and event details for both TBR and extra rewards
    """
    if rpc_client is not None:
        # Use unified RPC client
        if start_height is None or end_height is None:
            current_height, _ = rpc_client.get_block_height_and_timestamp()
            if not current_height:
                print("Could not get current block height")
                return None
            start_height = current_height - 10
            end_height = current_height

        print(f"Querying mint events from blocks {start_height} to {end_height}...")

        total_tbr_minted = 0
        total_extra_rewards = 0
        tbr_events = []
        extra_rewards_events = []

        for height in range(start_height, end_height + 1):
            try:
                # Query block results using RPC client
                response = rpc_client.get_block_results(height)
                block_results = response.get("result", {})
                finalize_block_events = block_results.get("finalize_block_events", [])

                for event in finalize_block_events:
                    event_type = event.get("type")
                    attributes = event.get("attributes", [])

                    # Handle inflationary rewards distributed (normal TBR)
                    if event_type == "inflationary_rewards_distributed":
                        amount_str = None
                        for attr in attributes:
                            if attr.get("key") == "total_amount":
                                amount_str = attr.get("value", "")
                                break

                        if amount_str and amount_str.endswith("loya"):
                            amount = int(amount_str[:-4])  # Remove 'loya' suffix
                            total_tbr_minted += amount
                            tbr_events.append(
                                {
                                    "height": height,
                                    "amount": amount,
                                    "amount_str": amount_str,
                                    "event_type": "inflationary_rewards_distributed",
                                }
                            )

                    # Handle extra rewards distributed
                    elif event_type == "extra_rewards_distributed":
                        amount_str = None
                        for attr in attributes:
                            if attr.get("key") == "total_amount":
                                amount_str = attr.get("value", "")
                                break

                        if amount_str and amount_str.endswith("loya"):
                            amount = int(amount_str[:-4])  # Remove 'loya' suffix
                            total_extra_rewards += amount
                            extra_rewards_events.append(
                                {
                                    "height": height,
                                    "amount": amount,
                                    "amount_str": amount_str,
                                    "event_type": "extra_rewards_distributed",
                                }
                            )

            except Exception as e:
                print(f"Error querying mint events at height {height}: {e}")
                continue

        return {
            "total_tbr_minted": total_tbr_minted,
            "total_extra_rewards": total_extra_rewards,
            "total_combined_rewards": total_tbr_minted + total_extra_rewards,
            "tbr_events": tbr_events,
            "extra_rewards_events": extra_rewards_events,
            "tbr_event_count": len(tbr_events),
            "extra_rewards_event_count": len(extra_rewards_events),
            "total_event_count": len(tbr_events) + len(extra_rewards_events),
        }

    else:
        raise Exception("RPC client is required - layerd binary fallback is disabled")


def get_extra_rewards_pool_account(
    rpc_client: TellorRPCClient,
) -> Optional[Dict[str, Any]]:
    """
    Query the extra rewards pool module account information.
    Returns dict with account details or None if query fails.
    """
    # Convert RPC endpoint to REST API endpoint
    if rpc_client.is_localhost:
        rest_endpoint = rpc_client.rpc_endpoint.replace(":26657", ":1317")
    elif rpc_client.rpc_endpoint.endswith("/rpc"):
        rest_endpoint = rpc_client.rpc_endpoint.replace("/rpc", "")
    else:
        rest_endpoint = rpc_client.rpc_endpoint

    url = f"{rest_endpoint}/cosmos/auth/v1beta1/module_accounts/extra_rewards_pool"

    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-X",
                "GET",
                url,
                "-H",
                "accept: application/json",
                "--silent",
                "--show-error",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        # Clean the output - remove any progress information
        output = result.stdout.strip()
        if output.startswith("{"):
            response = json.loads(output)
            return response.get("account", {})
        else:
            print(
                f"Unexpected response format for module account query: {output[:100]}..."
            )
            return None

    except subprocess.CalledProcessError as e:
        print(f"Failed to query extra rewards pool module account: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response for module account query: {e}")
        return None
    except Exception as e:
        print(f"Error querying extra rewards pool module account: {e}")
        return None


def get_account_balance(
    rpc_client: TellorRPCClient, address: str, denom: str = "loya"
) -> Optional[int]:
    """
    Query the balance of a specific account for a given denomination.
    Returns balance in base units (loya) or None if query fails.
    """
    # Convert RPC endpoint to REST API endpoint
    if rpc_client.is_localhost:
        rest_endpoint = rpc_client.rpc_endpoint.replace(":26657", ":1317")
    elif rpc_client.rpc_endpoint.endswith("/rpc"):
        rest_endpoint = rpc_client.rpc_endpoint.replace("/rpc", "")
    else:
        rest_endpoint = rpc_client.rpc_endpoint

    url = (
        f"{rest_endpoint}/cosmos/bank/v1beta1/balances/{address}/by_denom?denom={denom}"
    )

    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-X",
                "GET",
                url,
                "-H",
                "accept: application/json",
                "--silent",
                "--show-error",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        # Clean the output - remove any progress information
        output = result.stdout.strip()
        if output.startswith("{"):
            response = json.loads(output)
            balance_info = response.get("balance", {})
            amount_str = balance_info.get("amount", "0")
            return int(amount_str) if amount_str.isdigit() else 0
        else:
            print(f"Unexpected response format for balance query: {output[:100]}...")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Failed to query account balance: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response for balance query: {e}")
        return None
    except Exception as e:
        print(f"Error querying account balance: {e}")
        return None


def calculate_extra_rewards_duration(
    avg_extra_rewards_per_block: float, pool_balance_loya: int, avg_block_time: float
) -> Tuple[int, float, float, float]:
    """
    Calculate how long the extra rewards pool should last.
    Returns (blocks_remaining, days, hours, minutes)
    """
    if avg_extra_rewards_per_block <= 0:
        return 0, 0.0, 0.0, 0.0

    blocks_remaining = int(pool_balance_loya / avg_extra_rewards_per_block)

    # Convert to time units
    total_seconds = blocks_remaining * avg_block_time
    days = total_seconds / 86400
    hours = (total_seconds % 86400) / 3600
    minutes = (total_seconds % 3600) / 60

    return blocks_remaining, days, hours, minutes


def get_extra_rewards_pool_info(
    rpc_client: TellorRPCClient,
) -> Optional[Dict[str, Any]]:
    """
    Get complete extra rewards pool information including account details and balance.
    Returns dict with pool info or None if any query fails.
    """
    # Get module account information
    account_info = get_extra_rewards_pool_account(rpc_client)
    if not account_info:
        return None

    # Extract address from account info
    address = account_info.get("base_account", {}).get("address")
    if not address:
        print("No address found in module account info")
        return None

    # Get balance
    balance = get_account_balance(rpc_client, address)
    if balance is None:
        return None

    return {
        "account_name": "extra_rewards_pool",
        "address": address,
        "balance_loya": balance,
        "account_info": account_info,
    }
