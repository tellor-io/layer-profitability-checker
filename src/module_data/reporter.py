import subprocess
import yaml
from typing import Dict, List, Optional


def get_reporters(layerd_path: str) -> tuple[Dict[str, List[Dict[str, any]]], Dict[str, str]]:
    """
    Queries reporter data and separates active vs inactive vs jailed reporters.
    
    Returns:
        Tuple containing:
        - Dict with 'active', 'inactive', and 'jailed' keys containing lists of reporter data
        - Dict with summary metrics formatted for print_info_box
    """
    try:
        # Run the layerd query command
        result = subprocess.run(
            [layerd_path, 'query', 'reporter', 'reporters'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse YAML output
        reporters_data = yaml.safe_load(result.stdout)
        
        active_reporters = []
        inactive_reporters = []
        jailed_reporters = []
        
        # Handle different possible data structures
        if isinstance(reporters_data, str):
            print("Error: Received string instead of structured data")
            return ({'active': [], 'inactive': [], 'jailed': []}, 
                   {'Active Reporters': '0', 'Inactive Reporters': '0', 'Jailed Reporters': '0', 
                    'Total Reporters': '0', 'Total Active Power': '0'})
        
        # Check if it's a dict with a reporters key
        if isinstance(reporters_data, dict):
            if 'reporters' in reporters_data:
                reporters_list = reporters_data['reporters']
            else:
                print(f"Error: Expected 'reporters' key, found: {list(reporters_data.keys())}")
                return ({'active': [], 'inactive': [], 'jailed': []}, 
                       {'Active Reporters': '0', 'Inactive Reporters': '0', 'Jailed Reporters': '0', 
                        'Total Reporters': '0', 'Total Active Power': '0'})
        elif isinstance(reporters_data, list):
            reporters_list = reporters_data
        else:
            print(f"Error: Unexpected data type: {type(reporters_data)}")
            return ({'active': [], 'inactive': [], 'jailed': []}, 
                   {'Active Reporters': '0', 'Inactive Reporters': '0', 'Jailed Reporters': '0', 
                    'Total Reporters': '0', 'Total Active Power': '0'})
        
        # Process each reporter
        for reporter in reporters_list:
            address = reporter.get('address', '')
            power = reporter.get('power', '0')
            metadata = reporter.get('metadata', {})
            
            # Check if reporter is jailed
            is_jailed = metadata.get('jailed', False)
            
            # Convert power to int for comparison
            power_int = int(power) if power.isdigit() else 0
            
            reporter_info = {
                'address': address,
                'power': power,
                'moniker': metadata.get('moniker', ''),
                'commission_rate': metadata.get('commission_rate', ''),
                'min_tokens_required': metadata.get('min_tokens_required', ''),
                'last_updated': metadata.get('last_updated', ''),
                'jailed_until': metadata.get('jailed_until', '')
            }
            
            if is_jailed:
                jailed_reporters.append(reporter_info)
            elif power_int == 0:
                inactive_reporters.append(reporter_info)
            else:
                active_reporters.append(reporter_info)
        
        # Calculate summary metrics
        active_count = len(active_reporters)
        inactive_count = len(inactive_reporters)
        jailed_count = len(jailed_reporters)
        total_count = active_count + inactive_count + jailed_count
        
        active_total_power = sum(int(reporter['power']) if reporter['power'].isdigit() else 0 
                               for reporter in active_reporters)
        
        # Create summary dict for print_info_box
        summary_dict = {
            'Active Reporters': f"{active_count:,}",
            'Total Active Power': f"{active_total_power:,}",
            'Inactive Reporters': f"{inactive_count:,}",
            'Jailed Reporters': f"{jailed_count:,}",
            'Total Reporters': f"{total_count:,}"
        }
        
        detailed_dict = {
            'active': active_reporters,
            'inactive': inactive_reporters,
            'jailed': jailed_reporters
        }
        
        return detailed_dict, summary_dict
        
    except subprocess.CalledProcessError as e:
        print(f"Error running layerd query: {e}")
        print(f"stderr: {e.stderr}")
        empty_summary = {'Active Reporters': '0', 'Inactive Reporters': '0', 'Jailed Reporters': '0', 
                        'Total Reporters': '0', 'Total Active Power': '0'}
        return ({'active': [], 'inactive': [], 'jailed': []}, empty_summary)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        empty_summary = {'Active Reporters': '0', 'Inactive Reporters': '0', 'Jailed Reporters': '0', 
                        'Total Reporters': '0', 'Total Active Power': '0'}
        return ({'active': [], 'inactive': [], 'jailed': []}, empty_summary)
    except Exception as e:
        print(f"Unexpected error: {e}")
        empty_summary = {'Active Reporters': '0', 'Inactive Reporters': '0', 'Jailed Reporters': '0', 
                        'Total Reporters': '0', 'Total Active Power': '0'}
        return ({'active': [], 'inactive': [], 'jailed': []}, empty_summary)





# some of the returned reporters from `./layed query reporter reporters` have nil power but are not jailed. Guessing they stopped running a validator/reporter. 
# Would be nice to show 0 power instead of a not having the field. 

# ```
# /layerd query reporter reporters                
# pagination:
#   total: "36"
# reporters:
# - address: tellor1qma4ngrq2vqz6j82u548lder3ue6m25agqv9rt
#   metadata:
#     commission_rate: "250000000000000000"
#     jailed_until: "0001-01-01T00:00:00Z"
#     last_updated: "0001-01-01T00:00:00Z"
#     min_tokens_required: "1000000"
#     moniker: tekin86
# - address: tellor1q7pamj7v8d3wue5t5pwgejktajrnhuzzthwfel
#   metadata:
#     commission_rate: "250000000000000000"
#     jailed: true
#     jailed_until: "2025-05-31T19:36:07.659845144Z"
#     last_updated: "0001-01-01T00:00:00Z"
#     min_tokens_required: "1000000"
#     moniker: telliots-revenge
# - address: tellor1pn5yc5vdesc6ef05dge95axza5leyy37f7wg8p
#   metadata:
#     commission_rate: "50000000000000000"
#     jailed_until: "0001-01-01T00:00:00Z"
#     last_updated: "0001-01-01T00:00:00Z"
#     min_tokens_required: "1000000"
#     moniker: SpaceStake
# - address: tellor1y7y66xp3vrn8e6k4vxa7ygh7judy2jx40r2ktw
#   metadata:
#     commission_rate: "250000000000000000"
#     jailed_until: "0001-01-01T00:00:00Z"
#     last_updated: "0001-01-01T00:00:00Z"
#     min_tokens_required: "1000000"
#     moniker: warrion08
# - address: tellor198dvh9n2d7aqvrxzcsdfz73xtkv9jcjv5rakr6
#   metadata:
#     commission_rate: "40000000000000000"
#     jailed_until: "0001-01-01T00:00:00Z"
#     last_updated: "2025-05-23T16:50:44.616299185Z"
#     min_tokens_required: "1000000"
#     moniker: tank
#   power: "1191"
# - address: tellor1952ghnp9jat6eraqakdjruplrj9c40f0tn5jld
#   metadata:
#     commission_rate: "100000000000000000"
#     jailed_until: "0001-01-01T00:00:00Z"
#     last_updated: "0001-01-01T00:00:00Z"
#     min_tokens_required: "1000000"
#     moniker: yoda
#   power: "1245"
# ```

