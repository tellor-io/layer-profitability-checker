"""
24-hour balance tracking for Tellor Layer accounts.
Tracks free-floating (liquid), bonded (staked), and unbonding token balances.
Also tracks rewards_accumulated events to show reporter earnings.
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from termcolor import colored

from .chain_data.rpc_client import TellorRPCClient
from .display_helpers import print_section_header


@dataclass
class RewardAccumulatedEvent:
    """Represents a single rewards_accumulated event."""
    height: int
    tx_hash: str
    reporter: str
    commission_loya: int  # Commission taken by reporter
    net_reward_loya: int  # Net reward for selectors
    period_total_loya: int  # Running period total
    
    @property
    def commission_trb(self) -> float:
        return self.commission_loya / 1_000_000
    
    @property
    def net_reward_trb(self) -> float:
        return self.net_reward_loya / 1_000_000
    
    @property
    def total_reward_loya(self) -> int:
        """Gross reward before commission split."""
        return self.commission_loya + self.net_reward_loya
    
    @property
    def total_reward_trb(self) -> float:
        return self.total_reward_loya / 1_000_000


@dataclass
class AccountBalance:
    """Represents an account's balance snapshot at a specific block."""
    height: int
    timestamp: datetime
    free_floating_loya: int  # Bank balance (liquid)
    bonded_loya: int  # Total delegated/staked
    unbonding_loya: int  # Currently unbonding
    
    @property
    def free_floating_trb(self) -> float:
        return self.free_floating_loya / 1_000_000
    
    @property
    def bonded_trb(self) -> float:
        return self.bonded_loya / 1_000_000
    
    @property
    def unbonding_trb(self) -> float:
        return self.unbonding_loya / 1_000_000
    
    @property
    def total_loya(self) -> int:
        return self.free_floating_loya + self.bonded_loya + self.unbonding_loya
    
    @property
    def total_trb(self) -> float:
        return self.total_loya / 1_000_000


def _curl_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
    """Helper to make GET requests via curl."""
    cmd = ["curl", "-s", "--max-time", str(timeout), "-X", "GET", url, "-H", "accept: application/json"]
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def get_free_floating_balance(
    rest_endpoint: str,
    address: str,
    height: Optional[int] = None,
) -> int:
    """
    Get the free-floating (liquid) balance from the bank module.
    
    API: /cosmos/bank/v1beta1/balances/{address}
    """
    url = f"{rest_endpoint}/cosmos/bank/v1beta1/balances/{address}"
    
    headers = {}
    if height:
        headers["x-cosmos-block-height"] = str(height)
    
    try:
        response = _curl_get(url, headers)
        balances = response.get("balances", [])
        
        for balance in balances:
            if balance.get("denom") == "loya":
                return int(balance.get("amount", 0))
        
        return 0
    except Exception as e:
        print(f"  Error fetching bank balance: {e}")
        return 0


def get_bonded_balance(
    rest_endpoint: str,
    address: str,
    height: Optional[int] = None,
) -> int:
    """
    Get the bonded (delegated/staked) balance from the staking module.
    
    API: /cosmos/staking/v1beta1/delegations/{address}
    """
    url = f"{rest_endpoint}/cosmos/staking/v1beta1/delegations/{address}"
    
    headers = {}
    if height:
        headers["x-cosmos-block-height"] = str(height)
    
    try:
        response = _curl_get(url, headers)
        delegations = response.get("delegation_responses", [])
        
        total_bonded = 0
        for delegation in delegations:
            balance = delegation.get("balance", {})
            if balance.get("denom") == "loya":
                total_bonded += int(balance.get("amount", 0))
        
        return total_bonded
    except Exception as e:
        if "404" not in str(e) and "NotFound" not in str(e):
            print(f"  Error fetching delegations: {e}")
        return 0


def get_unbonding_balance(
    rest_endpoint: str,
    address: str,
    height: Optional[int] = None,
) -> int:
    """
    Get the unbonding balance from the staking module.
    
    API: /cosmos/staking/v1beta1/delegators/{address}/unbonding_delegations
    """
    url = f"{rest_endpoint}/cosmos/staking/v1beta1/delegators/{address}/unbonding_delegations"
    
    headers = {}
    if height:
        headers["x-cosmos-block-height"] = str(height)
    
    try:
        response = _curl_get(url, headers)
        unbonding_responses = response.get("unbonding_responses", [])
        
        total_unbonding = 0
        for unbonding in unbonding_responses:
            entries = unbonding.get("entries", [])
            for entry in entries:
                total_unbonding += int(entry.get("balance", 0))
        
        return total_unbonding
    except Exception as e:
        if "404" not in str(e) and "NotFound" not in str(e):
            print(f"  Error fetching unbonding delegations: {e}")
        return 0


def get_block_timestamp(rpc_client: TellorRPCClient, height: int) -> datetime:
    """Fetch the timestamp for a specific block height."""
    try:
        response = rpc_client.query_rpc("block", {"height": str(height)})
        timestamp_str = response["result"]["block"]["header"]["time"]
        
        if "." in timestamp_str:
            if timestamp_str.endswith("Z"):
                base_time = timestamp_str[:-1]
                date_part, frac = base_time.split(".")
                frac = frac[:6].ljust(6, "0")
                timestamp_str = f"{date_part}.{frac}+00:00"
            elif "+" in timestamp_str:
                base_time, tz = timestamp_str.split("+")
                date_part, frac = base_time.split(".")
                frac = frac[:6].ljust(6, "0")
                timestamp_str = f"{date_part}.{frac}+{tz}"
        
        return datetime.fromisoformat(timestamp_str)
    except Exception:
        return datetime.now(timezone.utc)


def get_account_balance_at_height(
    rpc_client: TellorRPCClient,
    address: str,
    height: Optional[int] = None,
) -> AccountBalance:
    """
    Get a complete account balance snapshot at a specific height.
    
    Queries three endpoints:
    1. Bank module - free floating (liquid) tokens
    2. Staking module - bonded (delegated) tokens
    3. Staking module - unbonding tokens
    """
    rest_endpoint = rpc_client.rest_endpoint
    
    if height:
        timestamp = get_block_timestamp(rpc_client, height)
    else:
        height, timestamp = rpc_client.get_block_height_and_timestamp()
    
    free_floating = get_free_floating_balance(rest_endpoint, address, height)
    bonded = get_bonded_balance(rest_endpoint, address, height)
    unbonding = get_unbonding_balance(rest_endpoint, address, height)
    
    return AccountBalance(
        height=height,
        timestamp=timestamp,
        free_floating_loya=free_floating,
        bonded_loya=bonded,
        unbonding_loya=unbonding,
    )


def parse_dec_to_loya(dec_str: str) -> int:
    """Parse decimal string to loya (integer)."""
    try:
        val = float(dec_str)
        return int(val)
    except:
        return 0


@dataclass
class RewardsAnalysis:
    """Analysis of rewards over a sample window with projections."""
    address: str
    start_height: int
    end_height: int
    start_timestamp: datetime
    end_timestamp: datetime
    blocks_scanned: int
    events: List[RewardAccumulatedEvent]
    
    # Measured values
    avg_block_time_seconds: float
    total_commission_loya: int
    total_net_reward_loya: int
    total_gross_loya: int
    
    # Projections
    blocks_per_day: int
    blocks_per_week: int
    
    @property
    def commission_trb(self) -> float:
        return self.total_commission_loya / 1_000_000
    
    @property
    def net_reward_trb(self) -> float:
        return self.total_net_reward_loya / 1_000_000
    
    @property
    def gross_trb(self) -> float:
        return self.total_gross_loya / 1_000_000
    
    @property
    def projected_commission_1d_trb(self) -> float:
        if self.blocks_scanned == 0:
            return 0
        rate_per_block = self.total_commission_loya / self.blocks_scanned
        return (rate_per_block * self.blocks_per_day) / 1_000_000
    
    @property
    def projected_commission_7d_trb(self) -> float:
        return self.projected_commission_1d_trb * 7
    
    @property
    def projected_gross_1d_trb(self) -> float:
        if self.blocks_scanned == 0:
            return 0
        rate_per_block = self.total_gross_loya / self.blocks_scanned
        return (rate_per_block * self.blocks_per_day) / 1_000_000
    
    @property
    def projected_gross_7d_trb(self) -> float:
        return self.projected_gross_1d_trb * 7


def query_rewards_accumulated_events(
    rpc_client: TellorRPCClient,
    address: str,
    sample_blocks: int = 500,
) -> RewardsAnalysis:
    """
    Query rewards_accumulated events for a reporter address over a sample window.
    
    Scans a small window of blocks completely, measures actual block time,
    and provides projections for 1d and 7d.
    """
    rpc_endpoint = rpc_client.rpc_endpoint
    events = []
    
    # Get current height and timestamp
    end_height, end_timestamp = rpc_client.get_block_height_and_timestamp()
    start_height = end_height - sample_blocks
    
    # Get start block timestamp
    start_timestamp = get_block_timestamp(rpc_client, start_height)
    
    # Calculate actual block time
    time_diff = (end_timestamp - start_timestamp).total_seconds()
    avg_block_time = time_diff / sample_blocks if sample_blocks > 0 else 2.0
    
    # Calculate blocks per day/week based on measured block time
    blocks_per_day = int(86400 / avg_block_time)  # 86400 seconds in a day
    blocks_per_week = blocks_per_day * 7
    
    print(f"    Scanning {sample_blocks} blocks for rewards_accumulated events...")
    print(f"    Address: {address[:20]}...")
    print(f"    Block range: {start_height} → {end_height}")
    print(f"    Time range: {start_timestamp.strftime('%H:%M:%S')} → {end_timestamp.strftime('%H:%M:%S')}")
    print(f"    Measured avg block time: {avg_block_time:.2f} seconds")
    print(f"    Estimated blocks/day: {blocks_per_day:,}")
    print()
    
    blocks_scanned = 0
    events_found = 0
    
    # Scan all blocks in the window
    for height in range(end_height, start_height - 1, -1):
        try:
            block_url = f"{rpc_endpoint}/block_results?height={height}"
            block_result = subprocess.run(
                ["curl", "-s", "--max-time", "10", block_url],
                capture_output=True, text=True, check=True
            )
            block_response = json.loads(block_result.stdout)
            result_data = block_response.get("result", {})
            
            # Check finalize_block_events for rewards_accumulated
            for event in result_data.get("finalize_block_events", []):
                etype = event.get("type", "")
                
                if etype == "rewards_accumulated":
                    attrs = {}
                    for attr in event.get("attributes", []):
                        key = attr.get("key", "")
                        value = attr.get("value", "")
                        attrs[key] = value
                    
                    # Check if this is for our reporter
                    if attrs.get("reporter") == address:
                        events.append(RewardAccumulatedEvent(
                            height=height,
                            tx_hash="",
                            reporter=address,
                            commission_loya=parse_dec_to_loya(attrs.get("commission", "0")),
                            net_reward_loya=parse_dec_to_loya(attrs.get("net_reward", "0")),
                            period_total_loya=parse_dec_to_loya(attrs.get("period_total", "0")),
                        ))
                        events_found += 1
            
            blocks_scanned += 1
            
            # Progress update every 100 blocks
            if blocks_scanned % 100 == 0:
                print(f"      Scanned {blocks_scanned}/{sample_blocks} blocks, found {events_found} events...")
                
        except Exception:
            continue
    
    print(f"    Scanned {blocks_scanned} blocks, found {events_found} rewards_accumulated events")
    
    # Sort by height ascending
    events.sort(key=lambda e: e.height)
    
    # Calculate totals
    total_commission = sum(e.commission_loya for e in events)
    total_net = sum(e.net_reward_loya for e in events)
    total_gross = total_commission + total_net
    
    return RewardsAnalysis(
        address=address,
        start_height=start_height,
        end_height=end_height,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        blocks_scanned=blocks_scanned,
        events=events,
        avg_block_time_seconds=avg_block_time,
        total_commission_loya=total_commission,
        total_net_reward_loya=total_net,
        total_gross_loya=total_gross,
        blocks_per_day=blocks_per_day,
        blocks_per_week=blocks_per_week,
    )
    

def print_rewards_analysis_report(analysis: RewardsAnalysis) -> None:
    """Print a formatted rewards analysis with projections."""
    
    print_section_header("REPORTER REWARDS ANALYSIS")
    
    if not analysis.events:
        print("  No rewards_accumulated events found in this period.")
        print()
        return
    
    # Sample info
    sample_duration = (analysis.end_timestamp - analysis.start_timestamp).total_seconds()
    sample_minutes = sample_duration / 60
    
    print(f"  Reporter: {analysis.address[:30]}...")
    print(f"  Sample: {analysis.blocks_scanned} blocks ({sample_minutes:.1f} minutes)")
    print(f"  Avg block time: {analysis.avg_block_time_seconds:.2f} seconds")
    print(f"  Events found: {len(analysis.events)}")
    print()
    
    # Measured values table
    print("  ┌─────────────────────────────────────────────────────────────────┐")
    print("  │                    MEASURED (Sample Period)                      │")
    print("  ├────────────────────────┬──────────────────────────────────────────┤")
    print(f"  │ Gross Rewards          │ {analysis.gross_trb:>16,.6f} TRB              │")
    print(f"  │ Reporter Commission    │ {analysis.commission_trb:>16,.6f} TRB              │")
    print(f"  │ Net to Selectors       │ {analysis.net_reward_trb:>16,.6f} TRB              │")
    print("  └────────────────────────┴──────────────────────────────────────────┘")
    print()
    
    # Projections table
    print("  ┌─────────────────────────────────────────────────────────────────┐")
    print("  │                    PROJECTED (Extrapolated)                      │")
    print("  ├────────────────────────┬───────────────────┬────────────────────┤")
    print("  │ Metric                 │ 1 Day             │ 7 Days             │")
    print("  ├────────────────────────┼───────────────────┼────────────────────┤")
    print(f"  │ Gross Rewards          │ {analysis.projected_gross_1d_trb:>13,.4f} TRB │ {analysis.projected_gross_7d_trb:>14,.4f} TRB │")
    print(f"  │ Reporter Commission    │ {analysis.projected_commission_1d_trb:>13,.4f} TRB │ {analysis.projected_commission_7d_trb:>14,.4f} TRB │")
    print("  └────────────────────────┴───────────────────┴────────────────────┘")
    print()
    
    # Show recent events
    if analysis.events:
        print(colored("  Recent Events (last 5):", "cyan"))
        print()
        
        recent_events = analysis.events[-5:] if len(analysis.events) > 5 else analysis.events
        for event in reversed(recent_events):
            gross = event.total_reward_trb
            print(f"    Block {event.height}: {colored(f'+{gross:.6f}', 'green')} TRB gross")
            print(f"      Commission: {event.commission_trb:.6f} | Net: {event.net_reward_trb:.6f}")
            print()


def print_balance_report(
    address: str,
    start_balance: AccountBalance,
    end_balance: AccountBalance,
) -> None:
    """Print a formatted balance comparison report."""
    
    print_section_header("24-HOUR BALANCE REPORT")
    
    # Helper for formatting
    def fmt_trb(loya: int) -> str:
        return f"{loya / 1_000_000:,.6f}"
    
    def fmt_change(start_loya: int, end_loya: int) -> str:
        change = end_loya - start_loya
        trb = change / 1_000_000
        if change > 0:
            return colored(f"+{trb:,.6f}", "green")
        elif change < 0:
            return colored(f"{trb:,.6f}", "red")
        else:
            return f"{trb:,.6f}"
    
    # Header info
    start_str = start_balance.timestamp.strftime("%Y-%m-%d %H:%M UTC")
    end_str = end_balance.timestamp.strftime("%Y-%m-%d %H:%M UTC")
    
    print(f"  Address: {address}")
    print(f"  Period:  {start_str} → {end_str}")
    print(f"  Blocks:  {start_balance.height} → {end_balance.height}")
    print()
    
    # Balance table
    print("  ┌─────────────────┬──────────────────┬──────────────────┬──────────────────┐")
    print("  │ Balance Type    │ Start            │ End              │ Change           │")
    print("  ├─────────────────┼──────────────────┼──────────────────┼──────────────────┤")
    
    # Free Floating
    print(f"  │ Free Floating   │ {fmt_trb(start_balance.free_floating_loya):>16} │ {fmt_trb(end_balance.free_floating_loya):>16} │ {fmt_change(start_balance.free_floating_loya, end_balance.free_floating_loya):>16} │")
    
    # Bonded
    print(f"  │ Bonded (Staked) │ {fmt_trb(start_balance.bonded_loya):>16} │ {fmt_trb(end_balance.bonded_loya):>16} │ {fmt_change(start_balance.bonded_loya, end_balance.bonded_loya):>16} │")
    
    # Unbonding
    print(f"  │ Unbonding       │ {fmt_trb(start_balance.unbonding_loya):>16} │ {fmt_trb(end_balance.unbonding_loya):>16} │ {fmt_change(start_balance.unbonding_loya, end_balance.unbonding_loya):>16} │")
    
    print("  ├─────────────────┼──────────────────┼──────────────────┼──────────────────┤")
    
    # Total
    total_change = end_balance.total_loya - start_balance.total_loya
    total_change_str = fmt_change(start_balance.total_loya, end_balance.total_loya)
    print(f"  │ TOTAL           │ {fmt_trb(start_balance.total_loya):>16} │ {fmt_trb(end_balance.total_loya):>16} │ {total_change_str:>16} │")
    
    print("  └─────────────────┴──────────────────┴──────────────────┴──────────────────┘")
    print()
    
    # Summary
    total_change_trb = total_change / 1_000_000
    if total_change > 0:
        print(colored(f"  Net change: +{total_change_trb:,.6f} TRB", "green", attrs=["bold"]))
    elif total_change < 0:
        print(colored(f"  Net change: {total_change_trb:,.6f} TRB", "red", attrs=["bold"]))
    else:
        print(f"  Net change: {total_change_trb:,.6f} TRB")
    print()


def run_historical_rewards_check(
    rpc_client: TellorRPCClient,
    address: str,
) -> Dict[str, Any]:
    """
    Main function to run 24-hour balance check for an address.
    
    Uses 2-second block time assumption:
    - 24 hours = 43,200 blocks
    """
    print(f"\n  Checking 24-hour balance changes for: {address[:20]}...\n")
    
    # Get current balance (end of period)
    print("  Fetching current balance...")
    end_balance = get_account_balance_at_height(rpc_client, address)
    
    # Get block from 24 hours ago (43,200 blocks with 2s block time)
    blocks_per_day = 43200
    start_height = max(1, end_balance.height - blocks_per_day)
    
    print(f"  Fetching balance at block {start_height} (~24 hours ago)...")
    start_balance = get_account_balance_at_height(rpc_client, address, start_height)
    
    # Print balance report
    print_balance_report(address, start_balance, end_balance)
    
    # Query and print rewards analysis with projections
    print("  Analyzing reporter rewards...")
    rewards_analysis = query_rewards_accumulated_events(
        rpc_client,
        address,
        sample_blocks=500,  # Scan 500 blocks completely
    )
    print_rewards_analysis_report(rewards_analysis)
    
    return {
        "address": address,
        "start_balance": start_balance,
        "end_balance": end_balance,
        "rewards_analysis": rewards_analysis,
    }
