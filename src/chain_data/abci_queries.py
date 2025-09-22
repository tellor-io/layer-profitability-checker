"""
ABCI query helpers for Tellor Layer specific module queries.
Converts layerd commands to ABCI queries for unified RPC access.
"""

import json
from typing import Any, Dict, List

from .rpc_client import TellorRPCClient


class TellorABCIClient:
    """ABCI query client for Tellor Layer specific queries."""

    def __init__(self, rpc_client: TellorRPCClient):
        self.rpc = rpc_client

    def query_staking_validators(self) -> List[Dict[str, Any]]:
        """Query staking validators via ABCI."""
        # Try different possible paths for staking validators
        possible_paths = [
            "/cosmos.staking.v1beta1.Query/Validators",
            "/cosmos/staking/v1beta1/validators",
            "/staking/validators",
            "/cosmos.staking.Query/Validators",
        ]

        for path in possible_paths:
            try:
                response = self.rpc.get_abci_query(path, "{}")
                if response.get("result", {}).get("response", {}).get("value"):
                    return json.loads(response["result"]["response"]["value"])
            except Exception:
                continue

        raise Exception("All staking validator query paths failed")

    def query_reporter_reporters(self) -> Dict[str, Any]:
        """Query reporter reporters via ABCI."""
        # Path: /tellor.reporter.Query/Reporters
        path = "/tellor.reporter.Query/Reporters"
        data = "{}"  # Empty request body

        response = self.rpc.get_abci_query(path, data)
        return json.loads(response["result"]["response"]["value"])

    def query_globalfee_minimum_gas_prices(self) -> Dict[str, Any]:
        """Query global fee minimum gas prices via ABCI."""
        # Path: /cosmos.tx.v1beta1.Service/GetTx
        path = "/cosmos.tx.v1beta1.Service/GetTx"
        data = "{}"  # Empty request body

        response = self.rpc.get_abci_query(path, data)
        return json.loads(response["result"]["response"]["value"])

    def query_reporter_tip(self, query_data: str) -> Dict[str, Any]:
        """Query reporter tip for specific query data via ABCI."""
        # Path: /tellor.reporter.Query/Tip
        path = "/tellor.reporter.Query/Tip"
        data = json.dumps({"queryData": query_data})

        response = self.rpc.get_abci_query(path, data)
        return json.loads(response["result"]["response"]["value"])

    def query_reporter_available_tips(self, selector_address: str) -> Dict[str, Any]:
        """Query available tips for selector via ABCI."""
        # Path: /tellor.reporter.Query/AvailableTips
        path = "/tellor.reporter.Query/AvailableTips"
        data = json.dumps({"selectorAddress": selector_address})

        response = self.rpc.get_abci_query(path, data)
        return json.loads(response["result"]["response"]["value"])

    def query_mint_params(self) -> Dict[str, Any]:
        """Query mint parameters via ABCI."""
        # Path: /cosmos.mint.v1beta1.Query/Params
        path = "/cosmos.mint.v1beta1.Query/Params"
        data = "{}"  # Empty request body

        response = self.rpc.get_abci_query(path, data)
        return json.loads(response["result"]["response"]["value"])

    def query_mint_inflation(self) -> Dict[str, Any]:
        """Query mint inflation via ABCI."""
        # Path: /cosmos.mint.v1beta1.Query/Inflation
        path = "/cosmos.mint.v1beta1.Query/Inflation"
        data = "{}"  # Empty request body

        response = self.rpc.get_abci_query(path, data)
        return json.loads(response["result"]["response"]["value"])

    def query_mint_annual_provisions(self) -> Dict[str, Any]:
        """Query mint annual provisions via ABCI."""
        # Path: /cosmos.mint.v1beta1.Query/AnnualProvisions
        path = "/cosmos.mint.v1beta1.Query/AnnualProvisions"
        data = "{}"  # Empty request body

        response = self.rpc.get_abci_query(path, data)
        return json.loads(response["result"]["response"]["value"])
