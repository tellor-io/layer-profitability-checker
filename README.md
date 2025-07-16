# Tellor Layer Profitability Checker

A comprehensive analysis tool for evaluating validator/reporter profitability on the Tellor Layer network.

## Features

- **Staking Analysis**: Detailed validator distribution statistics
- **APR Calculations**: Precise Annual Percentage Rate calculations for different stake amounts
- **Profitability Projections**: Time-based profit projections (per block, hour, day, month, year)
- **Reporter Analysis**: Individual reporter performance and APR analysis
- **Cost Analysis**: Reporting fees and gas cost analysis

## Requirements

### System Requirements
- Python 3.9 or higher
- `layerd` binary and a [synced node](https://docs.tellor.io/layer-docs/running-tellor-layer/node-setup) (Tellor Layer node software)
- Terminal with Unicode support for proper display

### Python Dependencies
- `numpy` - Numerical calculations and array operations
- `matplotlib` - Chart generation and visualization
- `PyYAML` - Configuration file parsing
- `termcolor` - Colored terminal output

## Installation

### Quick Setup
```bash
./setup.sh
```
This will automatically create a virtual environment, install dependencies, and set up your config file.

### Manual Setup

### 1. Clone or Download the Project
```bash
git clone <repository-url>
cd profitability_checker
```

### 2. Set Up Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Alternatively, install manually:
```bash
pip install numpy matplotlib PyYAML termcolor
```

### 4. Install Tellor Layer Binary
You need the `layerd` binary and a synced node to query the blockchain. Follow the official Tellor Layer documentation:
- Visit: https://docs.tellor.io/layer-docs/running-tellor-layer/node-setup

## Configuration

### 1. Create Configuration File
Copy the example configuration:
```bash
cp config_example.yaml config.yaml
```

### 2. Edit Configuration
Edit `config.yaml` and set your `layerd` path:

**Step 1: Find your layerd path**
```bash
which layerd
```

**Step 2: Copy the output and paste it into config.yaml**
```yaml
# Path to your layerd binary
layerd_path: /path/to/your/layerd  # Replace this with the output from 'which layerd'
```


## Usage

### Basic Usage
```bash
python src/main.py
```

### What the Tool Does

The profitability checker analyzes the Tellor Layer network and provides:

1. **Staking Distribution Analysis**
   - Total active/jailed validator tokens
   - Validator count statistics
   - Stake distribution box plots and histograms
   - Quartile analysis (Q1, median, Q3)

2. **Block Time Analysis**
   - Live block times
   - Block production statistics
   - Time-based projections

3. **Time-Based Rewards (TBR)**
   - Live minting rates
   - Block provision calculations
   - Daily/annual TBR projections

4. **Reporting Cost Analysis**
   - Average gas costs for submit_value transactions
   - Fee projections (daily, monthly, yearly)
   - Gas usage statistics

5. **Reporter Performance**
   - Individual reporter APR calculations
   - Commission rate analysis
   - Power distribution among reporters

6. **APR Calculations**
   - Detailed APR tables for different stake amounts
   - Break-even point analysis (⚖️ marked in tables)
   - Median stake analysis (📊 marked in tables)
   - Visual APR charts saved as PNG files

7. **Validator/Reporter Profitability Projections**
   - Per-block, hourly, daily, monthly, and yearly profit projections
   - Comparisons between average and median validator performance

### Output Files

The tool generates several output files:
- `current_apr_chart.png` - APR vs Individual Stake Amount chart
- `apr_by_total_stake.png` - APR analysis by total network stake


## Project Structure

```
profitability_checker/
├── src/
│   ├── main.py              # Main application entry point
│   ├── apr.py               # APR calculations and table formatting
│   ├── scenarios.py         # Scenario analysis and projections
│   ├── chain_data/          # Blockchain data queries
│   │   ├── block_data.py    # Block time and height queries
│   │   ├── node_data.py     # Chain ID and node information
│   │   └── tx_data.py       # Transaction analysis
│   └── module_data/         # Cosmos SDK module data
│       ├── globalfee.py     # Global fee parameters
│       ├── mint.py          # Minting module calculations
│       ├── reporter.py      # Reporter/validator data
│       └── staking.py       # Staking module data
├── config.yaml              # Configuration file (you create this)
├── config_example.yaml      # Example configuration
├── requirements.txt         # Python dependencies
├── setup.sh                 # Quick setup script
└── README.md               # This file
```

## Technical Details

### Data Sources
- All data is queried live from the Tellor Layer blockchain using your nodes' `layerd` binary
- No external APIs or cached data is used
- Calculations are performed in real-time based on current network state

### APR Calculation Method
APR is calculated using the formula:
```
proportion_stake = stake_amount / total_tokens_active
profit_per_block = (proportion_stake * avg_mint_amount) - (avg_fee/2)
blocks_per_year = (365 * 24 * 3600) / avg_block_time
annual_profit = profit_per_block * blocks_per_year
APR = (annual_profit / stake_amount) * 100
```

### Break-even Calculation
The break-even point is calculated analytically where APR = 0:
```
break_even_stake = (avg_fee / 2) * total_tokens_active / avg_mint_amount
```

This represents the minimum stake needed to cover reporting costs.

## Note

This tool is provided as-is for analysis purposes. Please ensure you understand the risks of validator and reporter operations before making financial decisions based on this analysis.
