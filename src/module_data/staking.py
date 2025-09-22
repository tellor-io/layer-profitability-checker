from typing import Optional

from ..chain_data.abci_queries import TellorABCIClient
from ..chain_data.rpc_client import TellorRPCClient


def get_total_stake(rpc_client: Optional[TellorRPCClient] = None, abci_client: Optional[TellorABCIClient] = None):
    if rpc_client is not None:
        # Use RPC client - query validators directly via RPC
        try:
            print("Querying validators via RPC...")
            # Query validators using the standard RPC endpoint
            response = rpc_client.get_validators()
            data = {"validators": response}
            return process_validator_data(data)
        except Exception as e:
            print(f"Error querying validators via RPC: {e}")
            # If RPC fails, return empty data
            return 0, 0, 0, 0, 0, 0, 0, 0, 0, []
    else:
        raise Exception("RPC client is required")

def process_validator_data(data):
    """Process validator data from RPC response"""
    total_tokens_active = 0
    total_tokens_jailed = 0
    total_tokens_unbonding = 0
    total_tokens_unbonded = 0
    jailed_count = 0
    active_count = 0
    unbonding_count = 0
    unbonded_count = 0
    active_validator_stakes = []

    # Extract validators from the response structure
    validators = data.get('validators', [])

    # Check if this is REST API format (has tokens)
    is_rest_api_format = validators and 'tokens' in validators[0]

    if is_rest_api_format:
        # REST API format: has actual token amounts
        for validator in validators:
            tokens_str = validator.get('tokens', '0')
            # Convert from uloya to TRB (divide by 1,000,000) and round to 6 decimals
            tokens = round(int(tokens_str) / 1_000_000, 6)  # Convert uloya to TRB

            # Check if validator is active (not jailed and has tokens)
            is_jailed = validator.get('jailed', False)
            status = validator.get('status', '')

            if not is_jailed and status == 'BOND_STATUS_BONDED' and tokens > 0:
                total_tokens_active += tokens
                active_count += 1
                active_validator_stakes.append(tokens)
            elif not is_jailed and status == 'BOND_STATUS_UNBONDING' and tokens > 0:
                total_tokens_unbonding += tokens
                unbonding_count += 1
            elif is_jailed:
                total_tokens_jailed += tokens
                jailed_count += 1
            else:
                # Unbonded validators (not jailed but not bonded)
                total_tokens_unbonded += tokens
                unbonded_count += 1
    else:
        # layerd format: has tokens, status, and jailed fields
        for validator in validators:
            tokens = int(validator.get('tokens', '0'))
            is_jailed = validator.get('jailed', False)
            status = validator.get('status', 0)

            # Status 1 = UNBONDED, Status 2 = UNBONDING, Status 3 = BONDED
            if status == 3 and not is_jailed:
                # Only count validators with status 3 (BONDED) as active
                total_tokens_active += tokens
                active_count += 1
                active_validator_stakes.append(tokens)
            elif status == 2 and not is_jailed:
                # Count unbonding validators separately
                total_tokens_unbonding += tokens
                unbonding_count += 1
            else:
                # Jailed or unbonded validators
                total_tokens_jailed += tokens
                jailed_count += 1

    # Calculate median stake from ONLY active validators
    median_stake = calculate_median_from_list(active_validator_stakes)

    return total_tokens_active, total_tokens_jailed, total_tokens_unbonding, total_tokens_unbonded, active_count, jailed_count, unbonding_count, unbonded_count, median_stake, active_validator_stakes


def calculate_median_from_list(token_amounts):
    """Calculate median from a list of token amounts"""
    if not token_amounts:
        return 0

    # Sort the amounts
    sorted_amounts = sorted(token_amounts)

    n = len(sorted_amounts)

    # Calculate median
    if n % 2 == 0:
        # Even number of values - average of middle two
        median = (sorted_amounts[n//2 - 1] + sorted_amounts[n//2]) / 2
    else:
        # Odd number of values - middle value
        median = sorted_amounts[n//2]

    return median

