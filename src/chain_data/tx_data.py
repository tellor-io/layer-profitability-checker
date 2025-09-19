import base64
import json
import subprocess
from typing import Any, Dict, Optional

from ..module_data.globalfee import get_min_gas_price
from .block_data import get_block_height_and_timestamp
from .rpc_client import TellorRPCClient


def extract_fee_from_tx_result(tx_result: Dict[str, Any]) -> int:
    """
    Extract fee amount from transaction result events.
    Returns fee amount in loya.
    """
    try:
        events = tx_result.get('events', [])
        for event in events:
            if event.get('type') == 'tx':
                attributes = event.get('attributes', [])
                for attr in attributes:
                    if attr.get('key') == 'fee':
                        fee_str = attr.get('value', '0')
                        # Remove 'loya' suffix and convert to int
                        if fee_str.endswith('loya'):
                            fee_str = fee_str[:-4]  # Remove 'loya' suffix
                        return int(fee_str) if fee_str.isdigit() else 0
        return 0
    except Exception as e:
        print(f"Error extracting fee from tx result: {e}")
        return 0


def parse_submit_value_transaction(tx_base64: str) -> Optional[Dict[str, Any]]:
    """
    Parse a base64-encoded transaction to extract MsgSubmitValue data.
    Returns a dict with reporter address and other relevant info.
    Note: Fee information should be extracted from block results, not from transaction bytes.
    """
    try:
        # Decode base64
        tx_bytes = base64.b64decode(tx_base64)

        # Convert to string for pattern matching
        tx_str = tx_bytes.decode('latin-1', errors='ignore')

        # Find the reporter address (starts with "tellor1")
        import re
        tellor_pattern = r'tellor1[a-z0-9]{38}'
        reporter_matches = re.findall(tellor_pattern, tx_str)

        if reporter_matches:
            reporter = reporter_matches[0]
            return {
                'reporter': reporter,
                'tx_type': 'MsgSubmitValue',
                'raw_tx': tx_base64
            }
        else:
            return None

    except Exception as e:
        print(f"Error parsing transaction: {e}")
        return None


# queries 10 blocks ago and forward, returns dict with up to 10 submit value tx, max 2 per block
def query_recent_reports(layerd_path=None, rpc_client: Optional[TellorRPCClient] = None, limit=10):
    print("Getting current block height..." + "\n")
    current_height, _ = get_block_height_and_timestamp(layerd_path, rpc_client)
    if not current_height:
        print("Could not get current block height")
        return None

    start_height = current_height - 10

    all_txs = []
    height = start_height

    # Search through blocks until we find enough transactions or reach current height
    while len(all_txs) < limit and height <= current_height:
        try:
            print(f"Searching block {height}...")

            if rpc_client is not None:
                # Query block directly and look for transactions
                block_response = rpc_client.get_block_with_txs(height)
                block_data = block_response.get('result', {}).get('block', {})

                # Get block results for gas and fee information
                block_results_response = rpc_client.get_block_results(height)
                block_results = block_results_response.get('result', {})

                block_txs = []

                # Extract transactions from block
                txs = block_data.get('data', {}).get('txs', [])
                txs_results = block_results.get('txs_results', [])

                for i, tx_encoded in enumerate(txs):
                    try:
                        # Parse the transaction to check if it's a MsgSubmitValue
                        parsed_tx = parse_submit_value_transaction(tx_encoded)
                        if parsed_tx:
                            # Get gas and fee info from block results
                            tx_result = txs_results[i] if i < len(txs_results) else {}
                            gas_wanted = tx_result.get('gas_wanted', '0')
                            gas_used = tx_result.get('gas_used', '0')

                            # Extract fee information from block results
                            fee_amount = extract_fee_from_tx_result(tx_result)

                            block_txs.append({
                                'height': height,
                                'tx': tx_encoded,
                                'reporter': parsed_tx['reporter'],
                                'gas_wanted': int(gas_wanted) if gas_wanted else 0,
                                'gas_used': int(gas_used) if gas_used else 0,
                                'fee_amount': fee_amount,
                                'is_submit_value': True
                            })
                    except Exception as e:
                        print(f"Error decoding transaction: {e}")
                        continue
            else:
                # Fallback to layerd binary (should not happen in current setup)
                result = subprocess.run([
                    layerd_path, 'query', 'txs',
                    '--query', f'message.action=\'/layer.oracle.MsgSubmitValue\' AND tx.height = {height}',
                    '--limit', '100',  # Get all txs from this height
                    '--output', 'json'
                ], capture_output=True, text=True, check=True)

                response = json.loads(result.stdout)
                block_txs = response.get('txs', [])

            if block_txs:
                # Take only 2 transactions per block
                txs_to_add = block_txs[:2]
                print(f"Found {len(block_txs)} reports at height {height}, sampling {len(txs_to_add)}")
                all_txs.extend(txs_to_add)

            height += 1

        except Exception as e:
            print(f"Error querying height {height}: {e}")
            height += 1
            continue

    if all_txs:
        print(f"\nSampling {len(all_txs)} oracle transactions")
        # Return in the same format as the original function
        return {
            'total_count': str(len(all_txs)),
            'count': str(min(limit, len(all_txs))),
            'txs': all_txs[:limit]
        }
    else:
        print("No oracle transactions found in recent blocks")
        return {
            'total_count': '0',
            'count': '0',
            'txs': []
        }

# analyzes the submit value transactions and returns a dict with the num txs, gas usage, and fee info
def analyze_submit_value_transactions(tx_response, layerd_path, rpc_client=None, config=None):
    if not tx_response or not tx_response.get('txs'):
        return {
            'tx_count': 0,
            'total_gas_wanted': 0,
            'total_gas_used': 0,
            'total_fees_loya': 0,
            'avg_gas_wanted': 0,
            'avg_gas_used': 0,
            'avg_fee_loya': 0,
            'avg_min_cost': 0,
            'gas_efficiency_pct': 0,
            'reporters': []
        }

    txs = tx_response.get('txs', [])
    submit_value_txs = []

    # Filter for MsgSubmitValue transactions
    for tx in txs:
        # Handle both old format (parsed tx) and new format (base64 string)
        if isinstance(tx.get('tx'), str):
            # New format: base64 encoded transaction
            # For now, assume all transactions are submit value transactions
            # In a full implementation, we'd decode and parse the transaction
            if tx.get('is_submit_value', False):
                submit_value_txs.append(tx)
        else:
            # Old format: parsed transaction object
            messages = tx.get('tx', {}).get('body', {}).get('messages', [])
            for msg in messages:
                if msg.get('@type') == '/layer.oracle.MsgSubmitValue':
                    submit_value_txs.append(tx)
                    break

    if not submit_value_txs:
        return {
            'tx_count': 0,
            'total_gas_wanted': 0,
            'total_gas_used': 0,
            'total_fees_loya': 0,
            'avg_gas_wanted': 0,
            'avg_gas_used': 0,
            'avg_fee_loya': 0,
            'avg_min_cost': 0,
            'gas_efficiency_pct': 0,
            'reporters': []
        }

    # Analyze each transaction
    total_gas_wanted = 0
    total_gas_used = 0
    total_fees_loya = 0
    total_min_cost = 0
    reporters = []

    # Get minimum gas price once
    min_gas_price = get_min_gas_price(layerd_path, rpc_client, config)
    if min_gas_price is None:
        print("Warning: Could not get minimum gas price")
        return {
            'tx_count': 0,
            'total_gas_wanted': 0,
            'total_gas_used': 0,
            'total_fees_loya': 0,
            'avg_gas_wanted': 0,
            'avg_gas_used': 0,
            'avg_fee_loya': 0,
            'avg_min_cost': 0,
            'gas_efficiency_pct': 0,
            'reporters': []
        }

    for tx in submit_value_txs:
        # Handle both old format (parsed tx) and new format (base64 string)
        if isinstance(tx.get('tx'), str):
            # New format: base64 encoded transaction with parsed data
            gas_wanted = tx.get('gas_wanted', 0)
            gas_used = tx.get('gas_used', 0)
            fee_amount = tx.get('fee_amount', 0)
            reporter = tx.get('reporter', 'unknown')
        else:
            # Old format: parsed transaction object
            gas_wanted = int(tx.get('gas_wanted', 0))
            gas_used = int(tx.get('gas_used', 0))

            # Extract fee info
            fee_amount = 0
            auth_info = tx.get('tx', {}).get('auth_info', {})
            fee_info = auth_info.get('fee', {})
            amounts = fee_info.get('amount', [])

            for amount in amounts:
                if amount.get('denom') == 'loya':
                    fee_amount += int(amount.get('amount', 0))

        total_gas_wanted += gas_wanted
        total_gas_used += gas_used
        total_fees_loya += fee_amount

        # Calculate min cost
        min_cost = gas_used * min_gas_price
        total_min_cost += min_cost

        # Extract reporter info
        if isinstance(tx.get('tx'), str):
            # New format: base64 encoded transaction with parsed data
            reporters.append({
                'address': reporter,
                'gas_wanted': gas_wanted,
                'gas_used': gas_used,
                'min_cost': min_cost,
                'fee_loya': fee_amount,
                'tx_hash': tx.get('txhash', ''),
                'height': tx.get('height', ''),
                'efficiency_pct': (gas_used / gas_wanted * 100) if gas_wanted > 0 else 0
            })
        else:
            # Old format: parsed transaction object
            messages = tx.get('tx', {}).get('body', {}).get('messages', [])
            for msg in messages:
                if msg.get('@type') == '/layer.oracle.MsgSubmitValue':
                    reporter = msg.get('creator', '')
                    if reporter:
                        reporters.append({
                            'address': reporter,
                            'gas_wanted': gas_wanted,
                            'gas_used': gas_used,
                            'min_cost': min_cost,
                            'fee_loya': fee_amount,
                            'tx_hash': tx.get('txhash', ''),
                            'height': tx.get('height', ''),
                            'efficiency_pct': (gas_used / gas_wanted * 100) if gas_wanted > 0 else 0
                        })
                    break

    tx_count = len(submit_value_txs)

    # Calculate averages
    avg_gas_wanted = total_gas_wanted / tx_count if tx_count > 0 else 0
    avg_gas_used = total_gas_used / tx_count if tx_count > 0 else 0
    avg_fee_loya = total_fees_loya / tx_count if tx_count > 0 else 0
    avg_min_cost = total_min_cost / tx_count if tx_count > 0 else 0

    return {
        'tx_count': tx_count,
        'total_gas_wanted': total_gas_wanted,
        'total_gas_used': total_gas_used,
        'total_fees_loya': total_fees_loya,
        'avg_gas_wanted': avg_gas_wanted,
        'avg_gas_used': avg_gas_used,
        'avg_fee_loya': avg_fee_loya,
        'avg_min_cost': avg_min_cost,
        'reporters': reporters
    }

def query_mint_events(layerd_path=None, start_height=None, end_height=None, rpc_endpoint=None, rpc_client=None):
    """
    Query mint_coins events from recent blocks using CometBFT RPC
    Returns dict with total minted amount and event details
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

        total_minted = 0
        mint_events = []

        for height in range(start_height, end_height + 1):
            try:
                # Query block results using RPC client
                response = rpc_client.get_block_results(height)
                block_results = response.get('result', {})
                finalize_block_events = block_results.get('finalize_block_events', [])

                for event in finalize_block_events:
                    if event.get('type') == 'mint_coins':
                        # Extract amount from attributes
                        attributes = event.get('attributes', [])
                        amount_str = None
                        destination = None

                        for attr in attributes:
                            if attr.get('key') == 'amount':
                                amount_str = attr.get('value', '')
                            elif attr.get('key') == 'destination':
                                destination = attr.get('value', '')

                        if amount_str and destination == 'mint':  # Changed from 'oracle' to 'mint'
                            # Parse amount (format: "123456loya")
                            if amount_str.endswith('loya'):
                                amount = int(amount_str[:-4])  # Remove 'loya' suffix
                                total_minted += amount
                                mint_events.append({
                                    'height': height,
                                    'amount': amount,
                                    'amount_str': amount_str,
                                    'destination': destination
                                })
                                print(f"Found mint event at height {height}: {amount_str}")

            except Exception as e:
                print(f"Error querying mint events at height {height}: {e}")
                continue

        return {
            'total_minted': total_minted,
            'events': mint_events,
            'event_count': len(mint_events)
        }

    else:
        raise Exception("RPC client is required - layerd binary fallback is disabled")

def print_submit_value_analysis(tx_response, layerd_path, rpc_client=None, config=None):
    """
    Print a formatted analysis of submit value transactions
    """
    analysis = analyze_submit_value_transactions(tx_response, layerd_path, rpc_client, config)

    # Get minimum gas price once
    min_gas_price = get_min_gas_price(layerd_path, rpc_client, config)
    if min_gas_price is None:
        print("Warning: Could not get minimum gas price")
        min_gas_price = 0


    return analysis
