import subprocess

import yaml


def get_layerd_path():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    return config.get("layerd_path", "layerd")  # fallback to 'layerd' in PATH

def get_total_stake():
    layerd_path = get_layerd_path()
    cmd = [
        layerd_path,
        "query",
        "staking",
        "validators",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {result.stderr}")

    # Parse YAML output
    data = yaml.safe_load(result.stdout)
    total_tokens_active = 0
    total_tokens_jailed = 0
    total_tokens_unbonding = 0
    jailed_count = 0
    active_count = 0
    unbonding_count = 0
    active_validator_stakes = []

    # Extract validators from the response structure
    validators = data.get('validators', [])

    # Sum up tokens from all validators
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

    return total_tokens_active, total_tokens_jailed, total_tokens_unbonding, active_count, jailed_count, unbonding_count, median_stake, active_validator_stakes

def get_total_active_tokens():
    """Calculate total active tokens by summing up tokens from all BOND_STATUS_BONDED validators"""
    layerd_path = get_layerd_path()
    cmd = [
        layerd_path,
        "query",
        "staking",
        "validators",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {result.stderr}")

    # Parse YAML output
    data = yaml.safe_load(result.stdout)
    total_active_tokens = 0
    bonded_validators_count = 0

    # Extract validators from the response structure
    validators = data.get('validators', [])

    for validator in validators:
        status = validator.get('status', 0)

        # Status 3 = BOND_STATUS_BONDED
        if status == 3:
            # Get the tokens amount (this should be in uip tokens)
            tokens = int(validator.get('tokens', '0'))
            total_active_tokens += tokens
            bonded_validators_count += 1

    return total_active_tokens, bonded_validators_count

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

# Test the new function
if __name__ == "__main__":
    try:
        total_active_tokens, bonded_count = get_total_active_tokens()
        print(f"Number of bonded validators: {bonded_count}")
        print(f"Total active tokens from BOND_STATUS_BONDED validators (loya): {total_active_tokens:,}")
        print(f"Total active tokens (TRB): {total_active_tokens / 1_000_000:,.6f}")
    except Exception as e:
        print(f"Error: {e}")
