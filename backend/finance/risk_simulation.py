"""Monte Carlo Simulation for Portfolio Risk Analysis.

Simulate portfolio growth under different market conditions using Monte Carlo methods.
Generates probability distributions of returns, worst/best case scenarios, and value-at-risk metrics.

Key Features:
- 1000+ portfolio path simulations
- Support for SIP (Systematic Investment Plan)
- Volatility and return uncertainty modeling
- Multiple statistical outputs (median, percentiles, VaR)
- Geometric Brownian Motion model for asset prices
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SimulationInput:
    """Input parameters for Monte Carlo simulation."""
    
    initial_investment: float  # Initial lump sum (₹)
    monthly_sip: float = 0.0   # Monthly SIP amount (₹)
    expected_return: float = 0.12  # Annual expected return (12% = 0.12)
    volatility: float = 0.15   # Annual volatility (15% = 0.15)
    years: int = 10            # Investment period (years)
    num_simulations: int = 1000 # Number of Monte Carlo paths
    risk_free_rate: float = 0.05  # Risk-free rate for Sharpe ratio
    inflation: float = 0.06    # Inflation rate for real returns
    
    def validate(self):
        """Validate input parameters."""
        errors = []
        
        if self.initial_investment < 0:
            errors.append(f"initial_investment must be >= 0, got {self.initial_investment}")
        
        if self.monthly_sip < 0:
            errors.append(f"monthly_sip must be >= 0, got {self.monthly_sip}")
        
        if self.expected_return < -1:
            errors.append(f"expected_return must be >= -1, got {self.expected_return}")
        
        if self.volatility < 0:
            errors.append(f"volatility must be >= 0, got {self.volatility}")
        
        if self.years < 1 or self.years > 50:
            errors.append(f"years must be between 1 and 50, got {self.years}")
        
        if self.num_simulations < 100 or self.num_simulations > 10000:
            errors.append(f"num_simulations must be between 100 and 10000, got {self.num_simulations}")
        
        if errors:
            raise ValueError('\n'.join(errors))
        
        return True


@dataclass
class SimulationOutput:
    """Output results from Monte Carlo simulation."""
    
    final_values: np.ndarray        # Final portfolio value for each simulation
    portfolio_paths: np.ndarray     # All portfolio values over time (simulations x months)
    monthly_values: np.ndarray      # Monthly portfolio values for median path
    median_return: float
    best_case: float                # 95th percentile
    worst_case: float               # 5th percentile
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    mean_return: float
    std_return: float
    min_return: float
    max_return: float
    success_probability: float      # % of simulations achieving goal
    value_at_risk_95: float        # VaR at 95% confidence
    sharpe_ratio: float            # Risk-adjusted return metric
    cagr: float                    # Compound Annual Growth Rate
    final_balance: float           # Median final balance
    total_invested: float          # Total amount invested (initial + SIPs)


# ============================================================================
# MONTE CARLO SIMULATION ENGINE
# ============================================================================

def run_monte_carlo_simulation(
    initial_investment: float,
    monthly_sip: float = 0.0,
    expected_return: float = 0.12,
    volatility: float = 0.15,
    years: int = 10,
    num_simulations: int = 1000,
    risk_free_rate: float = 0.05,
    inflation: float = 0.06,
    goal_amount: float = None,
    seed: int = None
) -> SimulationOutput:
    """Run Monte Carlo simulation for portfolio growth.
    
    Uses Geometric Brownian Motion (GBM) to model asset price paths:
    dS/S = μ*dt + σ*dW
    
    Where:
    - S: Asset price/portfolio value
    - μ: Expected return (drift)
    - σ: Volatility (diffusion)
    - dW: Wiener process increment (random shock)
    
    Args:
        initial_investment: Initial lump sum investment (₹)
        monthly_sip: Monthly SIP amount (₹)
        expected_return: Annual expected return (0.12 = 12%)
        volatility: Annual volatility (0.15 = 15%)
        years: Investment period in years
        num_simulations: Number of Monte Carlo paths
        risk_free_rate: Risk-free rate for Sharpe ratio
        inflation: Inflation rate for real returns
        goal_amount: Target amount for success probability
        seed: Random seed for reproducibility
    
    Returns:
        SimulationOutput with all results
    
    Raises:
        ValueError: If inputs are invalid
    """
    
    # Validate inputs
    sim_input = SimulationInput(
        initial_investment=initial_investment,
        monthly_sip=monthly_sip,
        expected_return=expected_return,
        volatility=volatility,
        years=years,
        num_simulations=num_simulations,
        risk_free_rate=risk_free_rate,
        inflation=inflation
    )
    sim_input.validate()
    
    # Set random seed for reproducibility
    if seed is not None:
        np.random.seed(seed)
    
    # Convert annual parameters to monthly
    monthly_return = expected_return / 12
    monthly_volatility = volatility / np.sqrt(12)
    total_months = years * 12
    
    # Initialize results array: (num_simulations, total_months)
    portfolio_paths = np.zeros((num_simulations, total_months + 1))
    portfolio_paths[:, 0] = initial_investment
    
    # Run simulations
    for month in range(1, total_months + 1):
        # Random normal shocks for each simulation (Wiener process)
        random_shocks = np.random.standard_normal(num_simulations)
        
        # Geometric Brownian Motion update
        # S(t) = S(t-1) * exp((μ - σ²/2)*dt + σ*√dt*Z)
        growth_factor = np.exp(
            (monthly_return - 0.5 * monthly_volatility**2) + 
            monthly_volatility * random_shocks
        )
        
        portfolio_paths[:, month] = portfolio_paths[:, month - 1] * growth_factor
        
        # Add monthly SIP
        portfolio_paths[:, month] += monthly_sip
    
    # Extract final values for all simulations
    final_values = portfolio_paths[:, -1]
    
    # Calculate returns
    total_invested = initial_investment + (monthly_sip * total_months)
    returns = final_values - total_invested
    return_percentages = (returns / total_invested) * 100 if total_invested > 0 else np.zeros_like(returns)
    
    # Calculate statistics
    median_value = np.percentile(final_values, 50)
    worst_case = np.percentile(final_values, 5)
    best_case = np.percentile(final_values, 95)
    percentile_10 = np.percentile(final_values, 10)
    percentile_25 = np.percentile(final_values, 25)
    percentile_75 = np.percentile(final_values, 75)
    percentile_90 = np.percentile(final_values, 90)
    
    median_return = np.percentile(return_percentages, 50)
    mean_return = np.mean(return_percentages)
    std_return = np.std(return_percentages)
    min_return = np.min(return_percentages)
    max_return = np.max(return_percentages)
    
    # Value at Risk (95% confidence): loss beyond which we're 95% confident
    var_95 = np.percentile(returns, 5)  # 5th percentile loss
    
    # Success probability (% of simulations exceeding goal)
    if goal_amount is not None:
        success_count = np.sum(final_values >= goal_amount)
        success_probability = (success_count / num_simulations) * 100
    else:
        success_probability = np.sum(final_values >= total_invested) / num_simulations * 100
    
    # Sharpe Ratio: (Expected Return - Risk-Free Rate) / Volatility
    excess_return = np.mean(return_percentages / 100) - risk_free_rate
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0
    
    # CAGR: Compound Annual Growth Rate
    # CAGR = (Final Value / Initial Investment)^(1/years) - 1
    if initial_investment > 0:
        cagr = (median_value / initial_investment) ** (1 / years) - 1
    else:
        cagr = 0
    
    # Get median path for visualization
    median_path_index = int(num_simulations / 2)
    sorted_indices = np.argsort(final_values)
    median_path = portfolio_paths[sorted_indices[median_path_index], :]
    
    # Create monthly values array (for time series visualization)
    months = np.arange(0, total_months + 1)
    
    # Round returns
    median_return = round(median_return, 2)
    mean_return = round(mean_return, 2)
    
    return SimulationOutput(
        final_values=final_values,
        portfolio_paths=portfolio_paths,
        monthly_values=median_path,
        median_return=median_return,
        best_case=round(best_case, 2),
        worst_case=round(worst_case, 2),
        percentile_10=round(np.percentile(final_values, 10), 2),
        percentile_25=round(percentile_25, 2),
        percentile_75=round(percentile_75, 2),
        percentile_90=round(percentile_90, 2),
        mean_return=mean_return,
        std_return=round(std_return, 2),
        min_return=round(min_return, 2),
        max_return=round(max_return, 2),
        success_probability=round(success_probability, 2),
        value_at_risk_95=round(var_95, 2),
        sharpe_ratio=round(sharpe_ratio, 4),
        cagr=round(cagr, 4),
        final_balance=round(median_value, 2),
        total_invested=round(total_invested, 2)
    )


# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_portfolio_percentiles(
    final_values: np.ndarray,
    percentiles: List[int] = [5, 10, 25, 50, 75, 90, 95]
) -> Dict[int, float]:
    """Calculate portfolio value at different percentiles.
    
    Args:
        final_values: Final portfolio values from simulations
        percentiles: List of percentiles to calculate
    
    Returns:
        Dictionary mapping percentile to portfolio value
    """
    return {
        p: round(np.percentile(final_values, p), 2)
        for p in percentiles
    }


def calculate_return_percentiles(
    final_values: np.ndarray,
    total_invested: float,
    percentiles: List[int] = [5, 10, 25, 50, 75, 90, 95]
) -> Dict[int, float]:
    """Calculate return percentage at different percentiles.
    
    Args:
        final_values: Final portfolio values from simulations
        total_invested: Total amount invested
        percentiles: List of percentiles to calculate
    
    Returns:
        Dictionary mapping percentile to return percentage
    """
    returns = final_values - total_invested
    return_percentages = (returns / total_invested) * 100
    
    return {
        p: round(np.percentile(return_percentages, p), 2)
        for p in percentiles
    }


def calculate_drawdown_analysis(
    portfolio_paths: np.ndarray
) -> Dict[str, float]:
    """Analyze maximum drawdown across all simulations.
    
    Maximum Drawdown: Peak-to-trough decline during investment period.
    Represents worst-case loss from peak.
    
    Args:
        portfolio_paths: Portfolio values over time (simulations x periods)
    
    Returns:
        Dictionary with drawdown statistics
    """
    num_simulations = portfolio_paths.shape[0]
    max_drawdowns = []
    
    for sim in range(num_simulations):
        path = portfolio_paths[sim, :]
        running_max = np.maximum.accumulate(path)
        drawdown = (path - running_max) / running_max
        max_drawdown = np.min(drawdown)
        max_drawdowns.append(max_drawdown)
    
    max_drawdowns = np.array(max_drawdowns)
    
    return {
        'average_max_drawdown': round(np.mean(max_drawdowns) * 100, 2),
        'worst_max_drawdown': round(np.min(max_drawdowns) * 100, 2),
        'best_max_drawdown': round(np.max(max_drawdowns) * 100, 2),
        'median_max_drawdown': round(np.median(max_drawdowns) * 100, 2),
    }


def calculate_probability_of_loss(
    final_values: np.ndarray,
    total_invested: float
) -> float:
    """Calculate probability of loss (portfolio value < investment).
    
    Args:
        final_values: Final portfolio values from simulations
        total_invested: Total amount invested
    
    Returns:
        Probability of loss as percentage
    """
    losses = np.sum(final_values < total_invested)
    return round((losses / len(final_values)) * 100, 2)


def calculate_time_to_goal(
    portfolio_paths: np.ndarray,
    goal_amount: float,
    years: int
) -> Dict[str, Any]:
    """Calculate time required to reach goal amount.
    
    Args:
        portfolio_paths: Portfolio values over time (simulations x periods)
        goal_amount: Target portfolio value
        years: Total investment period
    
    Returns:
        Dictionary with time to goal statistics
    """
    total_months = portfolio_paths.shape[1] - 1
    months_to_goal = []
    
    for sim in range(portfolio_paths.shape[0]):
        path = portfolio_paths[sim, :]
        goal_indices = np.where(path >= goal_amount)[0]
        
        if len(goal_indices) > 0:
            months_to_goal.append(goal_indices[0])
        else:
            months_to_goal.append(None)
    
    # Filter valid results
    valid_months = [m for m in months_to_goal if m is not None]
    
    if len(valid_months) == 0:
        return {
            'success_probability': 0.0,
            'median_months': None,
            'min_months': None,
            'max_months': None
        }
    
    return {
        'success_probability': round((len(valid_months) / len(months_to_goal)) * 100, 2),
        'median_months': int(np.median(valid_months)),
        'min_months': int(np.min(valid_months)),
        'max_months': int(np.max(valid_months)),
        'median_years': round(np.median(valid_months) / 12, 1),
        'min_years': round(np.min(valid_months) / 12, 1),
        'max_years': round(np.max(valid_months) / 12, 1),
    }


def sensitivity_analysis(
    initial_investment: float,
    monthly_sip: float = 0.0,
    years: int = 10,
    returns: List[float] = None,
    volatilities: List[float] = None,
    num_simulations: int = 1000
) -> Dict[Tuple[float, float], Dict[str, float]]:
    """Perform sensitivity analysis across return and volatility ranges.
    
    Args:
        initial_investment: Initial investment amount
        monthly_sip: Monthly SIP amount
        years: Investment period
        returns: List of expected returns to test
        volatilities: List of volatilities to test
        num_simulations: Number of simulations per scenario
    
    Returns:
        Dictionary mapping (return, volatility) to results
    """
    if returns is None:
        returns = [0.08, 0.10, 0.12, 0.14, 0.16]
    if volatilities is None:
        volatilities = [0.10, 0.15, 0.20, 0.25]
    
    results = {}
    
    for ret in returns:
        for vol in volatilities:
            output = run_monte_carlo_simulation(
                initial_investment=initial_investment,
                monthly_sip=monthly_sip,
                expected_return=ret,
                volatility=vol,
                years=years,
                num_simulations=num_simulations
            )
            
            results[(ret, vol)] = {
                'median_return': output.median_return,
                'worst_case': output.worst_case,
                'best_case': output.best_case,
                'sharpe_ratio': output.sharpe_ratio,
            }
    
    return results


# ============================================================================
# SCENARIO COMPARISON
# ============================================================================

def compare_scenarios(
    scenarios: Dict[str, Dict[str, Any]],
    num_simulations: int = 1000
) -> Dict[str, Dict[str, Any]]:
    """Compare multiple investment scenarios side-by-side.
    
    Args:
        scenarios: Dictionary of scenario names to parameters
        num_simulations: Number of simulations per scenario
    
    Returns:
        Dictionary mapping scenario names to results
    
    Example:
        scenarios = {
            'Conservative': {
                'initial_investment': 100000,
                'monthly_sip': 5000,
                'expected_return': 0.08,
                'volatility': 0.10,
                'years': 10
            },
            'Moderate': {...},
            'Aggressive': {...}
        }
    """
    results = {}
    
    for scenario_name, params in scenarios.items():
        params['num_simulations'] = num_simulations
        output = run_monte_carlo_simulation(**params)
        
        results[scenario_name] = {
            'median_return': output.median_return,
            'worst_case': output.worst_case,
            'best_case': output.best_case,
            'final_balance': output.final_balance,
            'sharpe_ratio': output.sharpe_ratio,
            'success_probability': output.success_probability,
            'cagr': output.cagr,
            'volatility': params.get('volatility', 'N/A'),
            'expected_return': params.get('expected_return', 'N/A'),
        }
    
    return results
