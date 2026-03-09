"""Quick Reference: Risk Simulation Module

Copy-paste examples for Monte Carlo risk analysis.
"""

# ============================================================================
# 1. BASIC MONTE CARLO SIMULATION
# ============================================================================

from backend.finance.risk_simulation import run_monte_carlo_simulation

# Simple portfolio simulation
result = run_monte_carlo_simulation(
    initial_investment=100000,      # ₹100,000 lump sum
    monthly_sip=5000,               # ₹5,000 monthly
    expected_return=0.12,           # 12% expected annual return
    volatility=0.15,                # 15% volatility (risk)
    years=10                        # 10-year period
)

print(f"Median Portfolio Value: ₹{result.final_balance:,.0f}")
print(f"Best Case (95th %ile): ₹{result.best_case:,.0f}")
print(f"Worst Case (5th %ile): ₹{result.worst_case:,.0f}")
print(f"Expected Return: {result.median_return:.1f}%")
print(f"Success Probability: {result.success_probability:.1f}%")


# ============================================================================
# 2. DIFFERENT INVESTMENT SCENARIOS
# ============================================================================

# Conservative: Low risk, low return
conservative = run_monte_carlo_simulation(
    initial_investment=100000,
    monthly_sip=3000,
    expected_return=0.08,       # 8% return
    volatility=0.10,             # 10% volatility
    years=10
)

# Balanced: Medium risk, medium return
balanced = run_monte_carlo_simulation(
    initial_investment=100000,
    monthly_sip=5000,
    expected_return=0.12,        # 12% return
    volatility=0.15,             # 15% volatility
    years=10
)

# Aggressive: High risk, high return
aggressive = run_monte_carlo_simulation(
    initial_investment=100000,
    monthly_sip=10000,
    expected_return=0.16,        # 16% return
    volatility=0.25,             # 25% volatility
    years=10
)

print("SCENARIO COMPARISON")
print(f"Conservative:  ₹{conservative.final_balance:,.0f} (Median)")
print(f"Balanced:      ₹{balanced.final_balance:,.0f} (Median)")
print(f"Aggressive:    ₹{aggressive.final_balance:,.0f} (Median)")


# ============================================================================
# 3. SCENARIO ANALYSIS & COMPARISON
# ============================================================================

from backend.finance.risk_simulation import compare_scenarios

# Define multiple scenarios
scenarios = {
    'Conservative': {
        'initial_investment': 100000,
        'monthly_sip': 3000,
        'expected_return': 0.08,
        'volatility': 0.10,
        'years': 10
    },
    'Moderate': {
        'initial_investment': 100000,
        'monthly_sip': 5000,
        'expected_return': 0.12,
        'volatility': 0.15,
        'years': 10
    },
    'Aggressive': {
        'initial_investment': 100000,
        'monthly_sip': 10000,
        'expected_return': 0.16,
        'volatility': 0.25,
        'years': 10
    }
}

comparison = compare_scenarios(scenarios, num_simulations=1000)

for scenario, metrics in comparison.items():
    print(f"\n{scenario}:")
    print(f"  Median: ₹{metrics['final_balance']:,.0f}")
    print(f"  Best Case: ₹{metrics['best_case']:,.0f}")
    print(f"  Worst Case: ₹{metrics['worst_case']:,.0f}")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")


# ============================================================================
# 4. ADVANCED ANALYSIS - PERCENTILES & DRAWDOWN
# ============================================================================

from backend.finance.risk_simulation import (
    calculate_portfolio_percentiles,
    calculate_drawdown_analysis,
    calculate_probability_of_loss,
    calculate_time_to_goal
)

# Get full percentile breakdown
result = run_monte_carlo_simulation(
    initial_investment=100000,
    monthly_sip=5000,
    expected_return=0.12,
    volatility=0.15,
    years=10
)

# Portfolio value percentiles
percentiles = calculate_portfolio_percentiles(result.final_values)
print("\nPORTFOLIO VALUE PERCENTILES:")
for p in [5, 25, 50, 75, 95]:
    print(f"  {p}th percentile: ₹{percentiles[p]:,.0f}")

# Drawdown analysis
drawdown = calculate_drawdown_analysis(result.portfolio_paths)
print("\nDRAWDOWN ANALYSIS:")
print(f"  Average Max Drawdown: {drawdown['average_max_drawdown']:.1f}%")
print(f"  Worst Case Drawdown: {drawdown['worst_max_drawdown']:.1f}%")
print(f"  Median Max Drawdown: {drawdown['median_max_drawdown']:.1f}%")

# Probability of loss
prob_loss = calculate_probability_of_loss(result.final_values, result.total_invested)
print(f"\nPROBABILITY OF LOSS: {prob_loss:.1f}%")

# Time to reach goal
goal = 500000  # ₹5 lakh goal
time_analysis = calculate_time_to_goal(result.portfolio_paths, goal, years=10)
print(f"\nTIME TO ₹{goal:,.0f} GOAL:")
print(f"  Success Probability: {time_analysis['success_probability']:.1f}%")
if time_analysis['median_months']:
    print(f"  Median Time: {time_analysis['median_years']:.1f} years")


# ============================================================================
# 5. SENSITIVITY ANALYSIS
# ============================================================================

from backend.finance.risk_simulation import sensitivity_analysis

# Analyze impact of different return/volatility combinations
results = sensitivity_analysis(
    initial_investment=100000,
    monthly_sip=5000,
    years=10,
    returns=[0.08, 0.10, 0.12, 0.14, 0.16],      # Test 5 return levels
    volatilities=[0.10, 0.15, 0.20, 0.25]        # Test 4 volatility levels
)

print("\nSENSITIVITY ANALYSIS (Return vs Volatility):")
print("\nMedian Returns (%):")

for vol in [0.10, 0.15, 0.20, 0.25]:
    row = f"Vol {vol*100:.0f}%: "
    for ret in [0.08, 0.10, 0.12, 0.14, 0.16]:
        row += f"{results[(ret, vol)]['median_return']:6.1f}% "
    print(row)


# ============================================================================
# 6. FLASK API ENDPOINT INTEGRATION
# ============================================================================

from flask import Flask, request, jsonify
from backend.finance.risk_simulation import run_monte_carlo_simulation

app = Flask(__name__)

@app.route('/api/risk/simulate', methods=['POST'])
def simulate_risk():
    """API endpoint for Monte Carlo simulation."""
    
    try:
        data = request.json
        
        # Validate required fields
        required = ['initial_investment', 'monthly_sip', 'expected_return', 'volatility', 'years']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Run simulation
        result = run_monte_carlo_simulation(
            initial_investment=data['initial_investment'],
            monthly_sip=data['monthly_sip'],
            expected_return=data['expected_return'],
            volatility=data['volatility'],
            years=data['years'],
            num_simulations=data.get('num_simulations', 1000)
        )
        
        # Return results
        return jsonify({
            'success': True,
            'data': {
                'median_return': result.median_return,
                'worst_case': result.worst_case,
                'best_case': result.best_case,
                'final_balance': result.final_balance,
                'sharpe_ratio': result.sharpe_ratio,
                'success_probability': result.success_probability,
                'cagr': result.cagr,
                'value_at_risk': result.value_at_risk_95,
                'total_invested': result.total_invested
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 7. TEST ENDPOINT WITH CURL
# ============================================================================

"""
# Test the API endpoint with sample data:

curl -X POST http://localhost:5000/api/risk/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "initial_investment": 100000,
    "monthly_sip": 5000,
    "expected_return": 0.12,
    "volatility": 0.15,
    "years": 10,
    "num_simulations": 1000
  }'

Expected response:
{
  "success": true,
  "data": {
    "median_return": 186.5,
    "worst_case": 285000.00,
    "best_case": 925000.00,
    "final_balance": 515000.00,
    "sharpe_ratio": 0.4667,
    "success_probability": 95.2,
    "cagr": 0.1234,
    "value_at_risk": -45000.00,
    "total_invested": 660000.00
  }
}
"""


# ============================================================================
# 8. REPRODUCIBLE RESULTS WITH SEED
# ============================================================================

# For testing/debugging, use same seed to get same results
result1 = run_monte_carlo_simulation(
    initial_investment=100000,
    monthly_sip=5000,
    expected_return=0.12,
    volatility=0.15,
    years=10,
    seed=42  # Fixed seed
)

result2 = run_monte_carlo_simulation(
    initial_investment=100000,
    monthly_sip=5000,
    expected_return=0.12,
    volatility=0.15,
    years=10,
    seed=42  # Same seed
)

# Results will be identical
assert result1.final_balance == result2.final_balance
print("✓ Reproducible results with seed=42")


# ============================================================================
# 9. VISUALIZATION WITH MATPLOTLIB
# ============================================================================

import matplotlib.pyplot as plt

result = run_monte_carlo_simulation(
    initial_investment=100000,
    monthly_sip=5000,
    expected_return=0.12,
    volatility=0.15,
    years=10
)

# Plot 1: Distribution of final portfolio values
plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
plt.hist(result.final_values, bins=50, alpha=0.7, color='blue', edgecolor='black')
plt.axvline(result.final_balance, color='green', linestyle='--', linewidth=2, label='Median')
plt.axvline(result.worst_case, color='red', linestyle='--', linewidth=2, label='Worst Case (5%)')
plt.axvline(result.best_case, color='darkgreen', linestyle='--', linewidth=2, label='Best Case (95%)')
plt.xlabel('Final Portfolio Value (₹)')
plt.ylabel('Frequency')
plt.title('Distribution of Final Portfolio Values')
plt.legend()
plt.grid(alpha=0.3)

# Plot 2: Portfolio growth paths
plt.subplot(1, 2, 2)
for i in range(0, result.portfolio_paths.shape[0], 10):  # Plot every 10th path
    plt.plot(result.portfolio_paths[i, :], alpha=0.1, color='blue')
median_path = result.portfolio_paths[int(result.portfolio_paths.shape[0]/2), :]
plt.plot(median_path, color='darkblue', linewidth=2, label='Median Path')
plt.xlabel('Months')
plt.ylabel('Portfolio Value (₹)')
plt.title('1000 Simulated Portfolio Trajectories')
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('monte_carlo_analysis.png', dpi=150, bbox_inches='tight')
plt.show()


# ============================================================================
# 10. REAL-WORLD USE CASE: FINANCIAL GOAL PLANNING
# ============================================================================

def plan_for_goal(goal_amount, years, risk_level='moderate'):
    """Helper function to plan investments to reach a goal."""
    
    if risk_level == 'conservative':
        ret, vol = 0.08, 0.10
        initial = 100000
        sip_range = range(2000, 10000, 1000)
    elif risk_level == 'moderate':
        ret, vol = 0.12, 0.15
        initial = 100000
        sip_range = range(3000, 15000, 1000)
    else:  # aggressive
        ret, vol = 0.16, 0.25
        initial = 100000
        sip_range = range(5000, 20000, 1000)
    
    print(f"\nPlanning to reach ₹{goal_amount:,.0f} goal in {years} years ({risk_level})")
    print("SIP Amount | Median Value | Best Case | Worst Case | Success %")
    print("-" * 70)
    
    for sip in sip_range:
        result = run_monte_carlo_simulation(
            initial_investment=initial,
            monthly_sip=sip,
            expected_return=ret,
            volatility=vol,
            years=years,
            num_simulations=500
        )
        
        print(f"₹{sip:,}     | ₹{result.final_balance:>12,.0f} | "
              f"₹{result.best_case:>9,.0f} | ₹{result.worst_case:>10,.0f} | "
              f"{result.success_probability:>8.1f}%")


# Find SIP needed for ₹50 lakh goal
plan_for_goal(goal_amount=5000000, years=15, risk_level='moderate')


# ============================================================================
# COMMAND LINE USAGE
# ============================================================================

"""
Run the Streamlit dashboard:

$ streamlit run frontend/risk_simulation_dashboard.py

Run the test suite:

$ python -m pytest tests/test_risk_simulation.py -v

Generate sample report:

$ python backend/finance/risk_simulation.py
"""
