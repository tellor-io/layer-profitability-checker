import subprocess
import json
from chain_data.block_data import get_block_height_and_timestamp
from module_data.globalfee import get_min_gas_price

# queries 10 blocks ago and forward, returns dict with up to 10 submit value tx, max 2 per block
def query_recent_reports(layerd_path, limit=10):
    print("Getting current block height..." + "\n")
    current_height, _ = get_block_height_and_timestamp(layerd_path)
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
            
        except subprocess.CalledProcessError as e:
            print(f"Error querying height {height}: {e}")
            height += 1
            continue
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for height {height}: {e}")
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
def analyze_submit_value_transactions(tx_response, layerd_path):
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
    min_gas_price = get_min_gas_price(layerd_path)
    if min_gas_price is None:
        min_gas_price = 0
    
    for tx in submit_value_txs:
        # Extract gas info
        gas_wanted = int(tx.get('gas_wanted', 0))
        gas_used = int(tx.get('gas_used', 0))
        
        total_gas_wanted += gas_wanted
        total_gas_used += gas_used
        
        # Extract fee info
        fee_amount = 0
        auth_info = tx.get('tx', {}).get('auth_info', {})
        fee_info = auth_info.get('fee', {})
        amounts = fee_info.get('amount', [])
        
        for amount in amounts:
            if amount.get('denom') == 'loya':
                fee_amount += int(amount.get('amount', 0))
        
        total_fees_loya += fee_amount
        
        # Calculate min cost
        min_cost = gas_used * min_gas_price
        total_min_cost += min_cost
        
        # Extract reporter info
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

def print_submit_value_analysis(tx_response, layerd_path):
    """
    Print a formatted analysis of submit value transactions
    """
    analysis = analyze_submit_value_transactions(tx_response, layerd_path)
    
    # Get minimum gas price once
    min_gas_price = get_min_gas_price(layerd_path)
    if min_gas_price is None:
        print("Warning: Could not get minimum gas price")
        min_gas_price = 0

    
    return analysis