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

# Configure your layerd path
which layerd  # Copy this path
# Edit config.yaml and paste the path

# Run the tool
uv run prof-check
```

## Requirements

- Python 3.9+
- `layerd` binary with synced node
- UV package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Configuration

Edit `config.yaml`:
```yaml
layerd_path: /path/to/your/layerd  # Required
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

- Queries live blockchain data via `layerd` binary
- Event-based TBR detection using CometBFT RPC
- Real-time validation with deterministic calculations
- APR = (annual_profit / stake_amount) * 100