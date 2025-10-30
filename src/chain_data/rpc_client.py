"""
Unified RPC client for Tellor Layer blockchain queries.
Uses configured RPC and REST API endpoints directly.
"""

import json
import subprocess
from datetime import datetime
from typing import Any, Dict, List
from ..config import get_rpc_endpoint, get_rest_endpoint


class TellorRPCClient:
    """Unified RPC client for Tellor Layer blockchain queries."""

    def __init__(self, rpc_endpoint: str = None, rest_endpoint: str = None):
        """
        Initialize RPC client with configured endpoints.
        
        Args:
            rpc_endpoint: RPC endpoint URL (optional, defaults to config value)
            rest_endpoint: REST API endpoint URL (optional, defaults to config value)
        """
        self.rpc_endpoint = (rpc_endpoint or get_rpc_endpoint()).rstrip("/")
        self.rest_endpoint = (rest_endpoint or get_rest_endpoint()).rstrip("/")

    def query_rpc(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query the RPC endpoint directly."""
        url = f"{self.rpc_endpoint}/{endpoint}"

        if params:
            # Build query string
            query_parts = []
            for key, value in params.items():
                query_parts.append(f"{key}={value}")
            url += "?" + "&".join(query_parts)

        try:
            result = subprocess.run(
                ["curl", "-s", url],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )

            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise Exception(f"RPC query failed: {e.stderr}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}") from e

    def get_chain_id(self) -> str:
        """Get chain ID from node info."""
        response = self.query_rpc("status")
        return response["result"]["node_info"]["network"]

    def get_block_height_and_timestamp(self) -> tuple[int, datetime]:
        """Get current block height and timestamp."""
        from datetime import datetime

        response = self.query_rpc("status")
        latest_block_height = int(
            response["result"]["sync_info"]["latest_block_height"]
        )

        # Get block details
        block_response = self.query_rpc("block", {"height": str(latest_block_height)})
        timestamp_str = block_response["result"]["block"]["header"]["time"]

        # Parse timestamp string to datetime object
        # Handle nanoseconds by truncating to microseconds (Python only supports up to microseconds)
        if "." in timestamp_str:
            if timestamp_str.endswith("Z"):
                # Format: 2025-05-28T20:35:31.196915692Z
                base_time = timestamp_str[:-1]  # Remove Z
                date_part, frac = base_time.split(".")
                frac = frac[:6].ljust(6, "0")  # Truncate to microseconds
                timestamp_str = f"{date_part}.{frac}+00:00"
            elif "+" in timestamp_str:
                # Format: 2025-05-28T20:35:31.196915692+00:00
                base_time, tz = timestamp_str.split("+")
                date_part, frac = base_time.split(".")
                frac = frac[:6].ljust(6, "0")  # Truncate to microseconds
                timestamp_str = f"{date_part}.{frac}+{tz}"

        timestamp = datetime.fromisoformat(timestamp_str)

        return latest_block_height, timestamp

    def get_block_results(self, height: int) -> Dict[str, Any]:
        """Get block results for a specific height."""
        return self.query_rpc("block_results", {"height": str(height)})

    def get_validators(self, height: int = None) -> List[Dict[str, Any]]:
        """Get validator set using Cosmos SDK REST API."""
        url = f"{self.rest_endpoint}/cosmos/staking/v1beta1/validators"

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
                return response.get("validators", [])
            else:
                raise Exception(f"Unexpected response format: {output[:100]}...")
        except subprocess.CalledProcessError as e:
            raise Exception(f"REST API query failed: {e.stderr}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}") from e

    def get_transactions(
        self, query: str = None, page: int = 1, per_page: int = 30
    ) -> Dict[str, Any]:
        """Search for transactions using block queries since tx_search is not available."""
        # Since tx_search is not working, we'll query blocks directly
        # This is a simplified implementation that returns empty results for now
        # The actual transaction querying will be done in query_recent_reports
        return {"result": {"txs": []}}

    def get_block_with_txs(self, height: int) -> Dict[str, Any]:
        """Get block with transactions for a specific height."""
        return self.query_rpc("block", {"height": str(height)})

    def get_abci_query(
        self, path: str, data: str, height: int = None
    ) -> Dict[str, Any]:
        """Query ABCI application state."""
        params = {"path": path, "data": data}
        if height:
            params["height"] = str(height)

        return self.query_rpc("abci_query", params)

    def get_consensus_params(self, height: int = None) -> Dict[str, Any]:
        """Get consensus parameters."""
        params = {}
        if height:
            params["height"] = str(height)

        return self.query_rpc("consensus_params", params)

    def get_net_info(self) -> Dict[str, Any]:
        """Get network information."""
        return self.query_rpc("net_info")

    def get_genesis(self) -> Dict[str, Any]:
        """Get genesis information."""
        return self.query_rpc("genesis")

    def get_health(self) -> Dict[str, Any]:
        """Check node health."""
        return self.query_rpc("health")

    def get_status(self) -> Dict[str, Any]:
        """Get node status."""
        return self.query_rpc("status")
