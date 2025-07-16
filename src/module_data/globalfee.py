import subprocess

def get_min_gas_price(layerd_path):
    try:
        # run `layerd query globalfee minimum-gas-prices`
        result = subprocess.run([layerd_path, 'query', 'globalfee', 'minimum-gas-prices'], 
                               capture_output=True, text=True, check=True)
        
        # Parse output to find the amount for loya denom
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'amount:' in line:
                # Extract amount from line like: - amount: "0.000025000000000000"
                amount_str = line.split('"')[1]
                return float(amount_str)
        
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"Error running layerd query globalfee: {e}")
        return None
    except Exception as e:
        print(f"Error parsing minimum gas price: {e}")
        return None
    