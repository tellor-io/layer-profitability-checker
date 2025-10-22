"""Tests for RPC client functionality with mocks."""

import pytest
from unittest.mock import Mock, patch
from src.chain_data.rpc_client import TellorRPCClient


class TestTellorRPCClient:
    """Test TellorRPCClient with mocked responses."""

    def test_rpc_client_initialization(self):
        """Test RPC client initialization."""
        endpoint = "http://localhost:26657"
        client = TellorRPCClient(endpoint)
        
        assert client.rpc_endpoint == endpoint

    @patch('subprocess.run')
    def test_get_chain_id_success(self, mock_subprocess):
        """Test successful chain ID retrieval."""
        # Mock successful curl response
        mock_result = Mock()
        mock_result.stdout = '{"result": {"node_info": {"network": "testnet"}}}'
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        client = TellorRPCClient("http://localhost:26657")
        chain_id = client.get_chain_id()
        
        assert chain_id == "testnet"

    @patch('subprocess.run')
    def test_get_chain_id_failure(self, mock_subprocess):
        """Test chain ID retrieval failure."""
        # Mock failed curl response
        mock_subprocess.side_effect = Exception("Connection failed")

        client = TellorRPCClient("http://localhost:26657")
        
        with pytest.raises(Exception, match="Connection failed"):
            client.get_chain_id()

    @patch('subprocess.run')
    def test_get_block_height_and_timestamp_success(self, mock_subprocess):
        """Test successful block height and timestamp retrieval."""
        # Mock successful responses
        status_response = Mock()
        status_response.stdout = '{"result": {"sync_info": {"latest_block_height": "12345"}}}'
        
        block_response = Mock()
        block_response.stdout = '{"result": {"block": {"header": {"time": "2024-01-01T00:00:00Z"}}}}'
        
        mock_subprocess.side_effect = [status_response, block_response]

        client = TellorRPCClient("http://localhost:26657")
        height, timestamp = client.get_block_height_and_timestamp()
        
        assert height == 12345
        assert timestamp.year == 2024

    @patch('subprocess.run')
    def test_get_validators_success(self, mock_subprocess):
        """Test successful validators retrieval."""
        # Mock successful response
        mock_result = Mock()
        mock_result.stdout = '{"validators": [{"operator_address": "addr1", "tokens": "1000000"}]}'
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        client = TellorRPCClient("http://localhost:26657")
        validators = client.get_validators()
        
        assert len(validators) == 1
        assert validators[0]["operator_address"] == "addr1"

    @patch('subprocess.run')
    def test_query_rpc_success(self, mock_subprocess):
        """Test successful RPC query."""
        # Mock successful response
        mock_result = Mock()
        mock_result.stdout = '{"result": {"data": "test"}}'
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        client = TellorRPCClient("http://localhost:26657")
        result = client.query_rpc("test_endpoint")
        
        assert result["result"]["data"] == "test"
