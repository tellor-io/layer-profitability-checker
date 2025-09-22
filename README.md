# Tellor Layer Profitability Checker

A comprehensive analysis tool for evaluating validator/reporter profitability on the Tellor Layer network. Projections assume a validator and reporter are being ran.

## Quick Start

```bash
# Clone and setup
git clone <repository-url>

cd profitability_checker

# Install UV
# https://docs.astral.sh/uv/#installation

uv sync

cp config_example.yaml config.yaml

# Configure your RPC endpoint
# Edit config.yaml and set your RPC endpoint URL

# Run the tool
uv run prof-check
```

## Requirements

- Python 3.9+
- RPC endpoint (no synced node required)
- UV package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Configuration

Edit `config.yaml`:
```yaml
rpc_endpoint: http://localhost:26657  # Required - RPC endpoint URL
account_address: your_address_here  # Optional
query_datas: [...]
```

## What It Does

- **Staking Analysis** - Validator distribution, stake statistics
- **Block Times** - Live block production rates and projections  
- **Time-Based Rewards** - Event-based minting analysis 
- **Reporting Costs** - Gas analysis and fee projections
- **APR Calculations** - Individual reporter APRs and break-even analysis
- **APR Projections** - APR projections at different network stake levels (50k-10M TRB)

## Output

- Terminal analysis 
- `current_apr_chart.png` - APR vs stake amount
- `apr_by_total_stake.png` - APR by total network stake




## Development

```bash
uv run ruff check --fix  # Lint and format
uv add <package>         # Add dependencies
uv sync                  # Update after changes
```

## Technical Details

## Note

This tool is provided as-is for analysis purposes. Projections are under perfect operating conditions.

- Queries live blockchain data via RPC endpoints
- Event-based TBR detection using CometBFT RPC
- Real-time validation with deterministic calculations
- APR = (annual_profit / stake_amount) * 100

## RPC and REST API Calls

The tool makes several different types of calls to gather blockchain data:

### **CometBFT RPC Calls (Core Blockchain Data)**

**`/status`** - Used multiple times
- **Purpose**: Get basic node information
- **Data**: Chain ID, current block height, sync status
- **Usage**: Chain identification, getting current block height for sampling

**`/block?height={height}`** - Used for block sampling
- **Purpose**: Get block details for a specific height
- **Data**: Block header, timestamp, transactions
- **Usage**: Block time calculations, getting block timestamps

**`/block_results?height={height}`** - Used for event analysis
- **Purpose**: Get block execution results and events
- **Data**: Transaction results, gas usage, events (including `mint_coins` events)
- **Usage**: 
  - Mint events detection for TBR calculations
  - Transaction fee extraction for reporting costs
  - Gas usage analysis

### **Cosmos SDK REST API Calls (Module-Specific Data)**

**`/cosmos/staking/v1beta1/validators`** - Staking data
- **Purpose**: Get validator information
- **Data**: Validator list, tokens, status, commission rates
- **Usage**: Staking distribution analysis, validator statistics

**`/tellor-io/layer/reporter/reporters`** - Reporter data
- **Purpose**: Get reporter information
- **Data**: Reporter list, power, status (active/inactive/jailed)
- **Usage**: Reporter analysis, power distribution

**`/tellor-io/layer/oracle/get_current_tip/{query_data}`** - Tip queries
- **Purpose**: Get current tip for specific price feeds
- **Data**: Tip amounts for each configured query data
- **Usage**: Current tips analysis

**`/tellor-io/layer/reporter/available-tips/{selector_address}`** - Available tips
- **Purpose**: Get claimable tips for a specific reporter
- **Data**: Available tips amount in loya
- **Usage**: Account-specific tip analysis

**`/cosmos/globalfee/v1beta1/minimum_gas_prices`** - Gas price queries
- **Purpose**: Get minimum gas price parameters
- **Data**: Minimum gas prices by denomination
- **Usage**: Cost calculations for reporting

### **Data Flow by Section**

**Staking Distribution:**
- `GET /cosmos/staking/v1beta1/validators` → Process validator data → Display statistics

**Block Times:**
- `GET /status` → Get current height
- `GET /block?height={height}` → Get block timestamps → Calculate averages

**Time-Based Rewards:**
- `GET /block_results?height={height}` → Extract `mint_coins` events → Calculate TBR

**Reporting Costs:**
- `GET /block_results?height={height}` → Extract transaction data → Analyze gas/fees
- `GET /cosmos/globalfee/v1beta1/minimum_gas_prices` → Get min gas price

**Reporters:**
- `GET /tellor-io/layer/reporter/reporters` → Process reporter data → Display statistics

**Current Tips:**
- `GET /tellor-io/layer/oracle/get_current_tip/{query_data}` → For each price feed
- `GET /tellor-io/layer/reporter/available-tips/{address}` → For account tips

### **Key Technical Details**

- **Unified RPC Client**: All calls go through `TellorRPCClient` for consistency
- **Endpoint Conversion**: RPC endpoints are converted to REST endpoints by removing `/rpc`
- **Error Handling**: Each call has fallback mechanisms and timeout handling
- **Data Processing**: Raw blockchain data is processed and converted to user-friendly formats
- **No Binary Dependencies**: All queries use HTTP calls, no need for synced nodes