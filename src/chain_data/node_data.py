import json
import subprocess


def get_chain_id(layerd_path):
    """Get the chain ID from the node by querying consensus comet node-info"""
    try:
        cmd = [layerd_path, "query", "consensus", "comet", "node-info", "--output", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        node_info = json.loads(result.stdout)
        return node_info["default_node_info"]["network"]
    except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as e:
        print(f"Error getting chain ID: {e}")
        return None
