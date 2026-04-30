from typing import Optional

from .rpc_client import TellorRPCClient


# get current block height and block timestamp
def get_block_height_and_timestamp(rpc_client: Optional[TellorRPCClient] = None):
    if rpc_client is not None:
        # Use RPC client
        try:
            return rpc_client.get_block_height_and_timestamp()
        except Exception as e:
            print(f"Error getting block info via RPC: {e}")
            raise Exception("RPC client is required") from e
    else:
        raise Exception("RPC client is required")


# gets the average block time from recently produced block timestamps
def get_average_block_time(rpc_client: TellorRPCClient, sample_blocks: int = 200):
    """Calculate average block time from timestamps across recent blocks."""

    height2, time2 = get_block_height_and_timestamp(rpc_client)

    if height2 is None or time2 is None:
        print("Failed to get current block info")
        return None

    height1 = max(1, height2 - sample_blocks)
    if height1 == height2:
        print("Not enough block history to calculate block time")
        return None

    try:
        time1 = rpc_client.get_block_timestamp(height1)
    except Exception as e:
        print(f"Failed to get historical block info at height {height1}: {e}")
        return None

    print(f"Sample block 1 - Height: {height1}, Time: {time1}")
    print(f"Sample block 2 - Height: {height2}, Time: {time2}")

    # Calculate differences
    block_diff = height2 - height1
    time_diff = (time2 - time1).total_seconds()

    if block_diff <= 0:
        print("Invalid block sample range")
        return None

    if time_diff <= 0:
        print("Invalid block timestamp sample")
        return None

    avg_block_time = time_diff / block_diff

    return avg_block_time, time_diff, block_diff
