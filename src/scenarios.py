import numpy as np
import matplotlib.pyplot as plt
from apr import calculate_apr_by_stake

# Set random seed for reproducible results
np.random.seed(42)

def simulate_validator_set(total_stake, num_validators=100, stake_distribution='uniform'):
    """
    Simulate a validator set with uniform stake distribution
    Fixed at 100 validators max for Tellor Layer
    
    Args:
        total_stake: Total stake in the network (loya)
        num_validators: Number of validators (fixed at 100)
        stake_distribution: 'uniform' (only option)
    
    Returns:
        List of stake amounts for each validator
    """
    # Ensure we never exceed 100 validators
    num_validators = min(num_validators, 100)
    
    if stake_distribution == 'uniform':
        # Equal stake distribution
        stake_per_validator = total_stake / num_validators
        return [stake_per_validator] * num_validators
    
    else:
        raise ValueError("Invalid stake_distribution. Use 'uniform'")

def calculate_weighted_avg_apr_scenario(validator_stakes, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time):
    """Calculate weighted average APR for a given validator set scenario"""
    total_weighted_apr = 0.0
    total_power = 0
    
    for stake in validator_stakes:
        if stake > 0:
            apr = calculate_apr_by_stake(stake, total_tokens_active, avg_mint_amount, avg_fee, avg_block_time)
            total_weighted_apr += apr * stake
            total_power += stake
    
    if total_power == 0:
        return 0.0
    
    return total_weighted_apr / total_power

def generate_stake_amount_scenarios(base_total_stake, avg_mint_amount, avg_fee, avg_block_time):
    """Generate scenarios for varying total stake amounts with 100 validators"""
    
    # Stake amounts from 0 to 2 million TRB (converted to loya)
    stake_amounts_trb = np.linspace(100, 2000000, 1000)  # Start at 100 TRB to avoid division by zero
    stake_amounts = stake_amounts_trb * 1e6  # Convert TRB to loya
    
    weighted_avg_aprs = []
    
    for total_stake in stake_amounts:
        # Generate validator set for this total stake (always 100 validators, uniform distribution)
        validator_stakes = simulate_validator_set(total_stake, 100, 'uniform')
        
        # Calculate weighted average APR
        weighted_avg = calculate_weighted_avg_apr_scenario(
            validator_stakes, total_stake, avg_mint_amount, avg_fee, avg_block_time
        )
        
        weighted_avg_aprs.append(weighted_avg)
    
    results = {
        'stake_amounts': stake_amounts,
        'stake_amounts_trb': stake_amounts_trb,
        'weighted_avg_aprs': weighted_avg_aprs
    }
    
    return results

def find_apr_targets(stake_amounts_trb, aprs, target_aprs):
    """Find stake amounts where APR hits target values"""
    targets = {}
    
    for target_apr in target_aprs:
        # Find closest APR to target
        differences = np.abs(np.array(aprs) - target_apr)
        closest_idx = np.argmin(differences)
        
        if differences[closest_idx] < 5:  # Within 5% of target
            targets[target_apr] = {
                'stake_trb': stake_amounts_trb[closest_idx],
                'actual_apr': aprs[closest_idx]
            }
    
    return targets

def plot_stake_scenarios(results, base_total_stake):
    """Plot average APR vs total stake amount"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    target_aprs = [100, 50, 20, 10]
    
    # Set x-axis ticks
    x_ticks = np.arange(0, 2500000, 500000)
    x_tick_labels = [f'{int(x/1000)}k' if x < 1000000 else f'{int(x/1000000)}M' for x in x_ticks]
    
    # Current stake line
    current_stake_trb = base_total_stake * 1e-6
    
    # Plot Average APR
    stake_amounts_trb = results['stake_amounts_trb']
    aprs = results['weighted_avg_aprs']
    
    ax.plot(stake_amounts_trb, aprs, color='blue', linewidth=2, label='Uniform Distribution')
    
    # Add target points
    targets = find_apr_targets(stake_amounts_trb, aprs, target_aprs)
    for target_apr, target_data in targets.items():
        ax.plot(target_data['stake_trb'], target_data['actual_apr'], 'ko', markersize=6)
        stake_k = target_data['stake_trb'] / 1000
        ax.annotate(f'{target_apr}%\n({stake_k:.0f}k)', 
                    xy=(target_data['stake_trb'], target_data['actual_apr']),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=8, ha='center',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
    
    ax.set_xlabel('Total Network Stake (TRB)')
    ax.set_ylabel('Avg APR (%)')
    ax.set_title('Network APR vs Total Stake Amount')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_tick_labels)
    ax.set_ylim(-50, 400)
    if current_stake_trb <= 2000000:
        ax.axvline(x=current_stake_trb, color='black', linestyle='--', alpha=0.5, label='Current Stake')
        ax.legend()
    
    plt.tight_layout()
    plt.savefig('apr_by_total_stake.png', dpi=300, bbox_inches='tight')
    print("Generated apr_by_total_stake.png")
    print("\n")
    print("assuming a uniform distribution...")
    
    return targets

def run_scenarios_analysis(total_tokens_active, avg_mint_amount, avg_fee, avg_block_time):
    """Run stake amount scenarios analysis and generate plots"""
    
    # Generate stake amount scenarios

    stake_results = generate_stake_amount_scenarios(
        total_tokens_active, avg_mint_amount, avg_fee, avg_block_time
    )
    targets = plot_stake_scenarios(stake_results, total_tokens_active)
        
    return stake_results, targets

def format_targets_for_display_with_apr(targets, current_total_stake, stake_results):
    """Format target APR points for display in main.py info box including current APR"""
    current_stake_trb = current_total_stake * 1e-6
    
    display_dict = {}
    
    # Add current stake info first
    display_dict["Current Network Stake"] = f"{current_stake_trb:,.0f} TRB"
    
    # Calculate and add current network APR
    stake_amounts = stake_results['stake_amounts']
    weighted_aprs = stake_results['weighted_avg_aprs']
    closest_idx = np.argmin(np.abs(stake_amounts - current_total_stake))
    current_apr = weighted_aprs[closest_idx]
    
    display_dict["Current Network APR"] = f"{current_apr:.0f}%"
    
    # Add target points in descending order
    sorted_targets = sorted(targets.items(), key=lambda x: x[0], reverse=True)
    
    for target_apr, data in sorted_targets:
        stake_trb = data['stake_trb']
        actual_apr = data['actual_apr']
        
        # Format stake amount nicely
        if stake_trb >= 1000000:
            stake_str = f"{stake_trb/1000000:.1f}M TRB"
        elif stake_trb >= 1000:
            stake_str = f"{stake_trb/1000:.0f}k TRB"
        else:
            stake_str = f"{stake_trb:.0f} TRB"
        
        display_dict[f"{target_apr}% APR at"] = stake_str
    
    return display_dict
