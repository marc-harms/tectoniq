"""
Portfolio Risk State Engine - Phase 2

Elevates asset-level regime analysis to portfolio-level risk diagnostics.

HARD CONSTRAINTS (NON-NEGOTIABLE):
- NO modification to compute_market_state()
- NO forecasting, strategy, or optimization
- NO look-ahead bias
- Fully explainable and deterministic

Delivers exactly FOUR things:
1. Portfolio Criticality (0-100)
2. Portfolio Regime (GREEN/YELLOW/RED)
3. Risk Attribution (Top Contributors)
4. Temporal Stability (no flicker)
"""

from dataclasses import dataclass
from typing import List, Literal, Optional
import pandas as pd
from logic import MarketState


# =====================================================================
# STEP 1: INPUT CONTRACT
# =====================================================================

@dataclass
class AssetInput:
    """Single asset with weight and computed state."""
    symbol: str
    weight: float
    state: MarketState


@dataclass
class PortfolioInput:
    """Portfolio input: list of assets with weights and states."""
    assets: List[AssetInput]
    
    def validate(self) -> None:
        """
        Validate portfolio input.
        
        Rules:
        - Weights must sum to 1.0 ± 1e-6
        - No negative weights
        - Empty portfolio → explicit error
        
        Raises:
            ValueError: If validation fails
        """
        if not self.assets:
            raise ValueError("Portfolio cannot be empty")
        
        total_weight = sum(asset.weight for asset in self.assets)
        
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError(
                f"Portfolio weights must sum to 1.0, got {total_weight:.6f}"
            )
        
        for asset in self.assets:
            if asset.weight < 0:
                raise ValueError(
                    f"Asset {asset.symbol} has negative weight: {asset.weight}"
                )


# =====================================================================
# STEP 6: OUTPUT CONTRACT (STRICT)
# =====================================================================

@dataclass
class RiskContributor:
    """Risk contribution from a single asset."""
    symbol: str
    weight: float
    criticality: int
    contribution: float  # Absolute contribution to portfolio criticality
    contribution_pct: float  # % of total portfolio criticality


@dataclass
class PortfolioState:
    """
    Portfolio risk state at a single point in time.
    
    This is the SINGLE SOURCE OF TRUTH for portfolio-level risk.
    
    No UI logic. No plotting. Pure state representation.
    """
    date: pd.Timestamp
    portfolio_criticality: int  # 0-100, weighted mean of asset criticalities
    portfolio_regime: Literal["GREEN", "YELLOW", "RED"]
    top_risk_contributors: List[RiskContributor]  # Top 5, sorted descending


# =====================================================================
# STEP 2: PORTFOLIO CRITICALITY (CORE)
# =====================================================================

def compute_portfolio_criticality(portfolio: PortfolioInput) -> float:
    """
    Compute portfolio criticality as weighted mean of asset criticalities.
    
    Formula:
        portfolio_criticality = Σ(weight_i × criticality_i)
    
    Rules:
    - No nonlinear transforms
    - No penalties
    - No smoothing
    - Output must be 0-100
    - Preserves monotonicity and interpretability
    
    Args:
        portfolio: Validated PortfolioInput
    
    Returns:
        Portfolio criticality (float, 0-100)
    """
    portfolio_criticality = sum(
        asset.weight * asset.state.criticality
        for asset in portfolio.assets
    )
    
    # Ensure bounded [0, 100]
    return max(0.0, min(100.0, portfolio_criticality))


# =====================================================================
# STEP 3: PORTFOLIO REGIME MAPPING
# =====================================================================

def map_portfolio_regime(criticality: float) -> Literal["GREEN", "YELLOW", "RED"]:
    """
    Map portfolio criticality to regime using SAME thresholds as asset-level.
    
    Thresholds (STRICT):
        GREEN:  criticality < 40
        YELLOW: 40 ≤ criticality < 70
        RED:    criticality ≥ 70
    
    Rules:
    - Deterministic
    - Threshold-based
    - Stateless (no history at this stage)
    - Uses EXACT same bands as compute_market_state()
    
    Args:
        criticality: Portfolio criticality (0-100)
    
    Returns:
        Portfolio regime: "GREEN", "YELLOW", or "RED"
    """
    if criticality < 40:
        return "GREEN"
    elif criticality < 70:
        return "YELLOW"
    else:
        return "RED"


# =====================================================================
# STEP 4: RISK ATTRIBUTION (MANDATORY)
# =====================================================================

def compute_risk_attribution(portfolio: PortfolioInput, 
                             portfolio_criticality: float) -> List[RiskContributor]:
    """
    Compute risk contribution per asset.
    
    Formula:
        risk_contribution_i = weight_i × criticality_i
    
    Exposes:
    - Absolute contribution
    - % of total portfolio risk
    
    Answers: "Why is my portfolio RED?"
    
    Args:
        portfolio: Validated PortfolioInput
        portfolio_criticality: Total portfolio criticality
    
    Returns:
        List of RiskContributor objects, sorted descending, limited to top 5
    """
    contributors = []
    
    for asset in portfolio.assets:
        contribution = asset.weight * asset.state.criticality
        
        # Avoid division by zero
        contribution_pct = (contribution / portfolio_criticality * 100) if portfolio_criticality > 0 else 0.0
        
        contributors.append(RiskContributor(
            symbol=asset.symbol,
            weight=asset.weight,
            criticality=asset.state.criticality,
            contribution=contribution,
            contribution_pct=contribution_pct
        ))
    
    # Sort descending by absolute contribution
    contributors.sort(key=lambda x: x.contribution, reverse=True)
    
    # Limit to top 5 contributors
    return contributors[:5]


# =====================================================================
# STEP 5: PORTFOLIO HYSTERESIS (ANTI-FLICKER)
# =====================================================================

def apply_portfolio_hysteresis(
    current_regime: Literal["GREEN", "YELLOW", "RED"],
    previous_regime: Optional[Literal["GREEN", "YELLOW", "RED"]],
    confirmation_count: int
) -> tuple[Literal["GREEN", "YELLOW", "RED"], int]:
    """
    Apply portfolio-level hysteresis to prevent regime flicker.
    
    Rules:
    - Portfolio regime may only transition: GREEN ↔ YELLOW ↔ RED
    - Require 2 consecutive confirmations to change regime
    - Default memory = previous regime
    
    This is PORTFOLIO-LEVEL ONLY. Asset regimes are not affected.
    
    Args:
        current_regime: Regime suggested by current criticality
        previous_regime: Last confirmed portfolio regime (None if first time)
        confirmation_count: How many consecutive periods current regime was seen
    
    Returns:
        Tuple of (confirmed_regime, new_confirmation_count)
    """
    # First time: accept current regime immediately
    if previous_regime is None:
        return current_regime, 1
    
    # Same as previous: no change needed
    if current_regime == previous_regime:
        return current_regime, 1
    
    # Check if transition is valid (must be adjacent)
    valid_transitions = {
        "GREEN": ["YELLOW"],
        "YELLOW": ["GREEN", "RED"],
        "RED": ["YELLOW"]
    }
    
    # Invalid transition (GREEN→RED or RED→GREEN): maintain previous regime
    if current_regime not in valid_transitions.get(previous_regime, []):
        return previous_regime, 0
    
    # Valid transition: check confirmation count
    if confirmation_count >= 2:
        # Confirmed: accept new regime
        return current_regime, 1
    else:
        # Not yet confirmed: stay in previous, increment counter
        return previous_regime, confirmation_count + 1


# =====================================================================
# MAIN FUNCTION: COMPUTE PORTFOLIO STATE
# =====================================================================

def compute_portfolio_state(
    portfolio: PortfolioInput,
    previous_regime: Optional[Literal["GREEN", "YELLOW", "RED"]] = None,
    confirmation_count: int = 0
) -> PortfolioState:
    """
    Compute portfolio risk state at a single point in time.
    
    This is the SINGLE ENTRY POINT for portfolio-level risk analysis.
    
    Process:
    1. Validate input
    2. Compute portfolio criticality (weighted mean)
    3. Map to regime (GREEN/YELLOW/RED)
    4. Apply hysteresis (anti-flicker)
    5. Compute risk attribution (top contributors)
    6. Return PortfolioState
    
    Args:
        portfolio: PortfolioInput with assets, weights, and states
        previous_regime: Last confirmed regime (for hysteresis)
        confirmation_count: Consecutive periods current regime was seen
    
    Returns:
        PortfolioState object
    
    Raises:
        ValueError: If portfolio validation fails
    
    Example:
        >>> # Compute asset states first
        >>> spy_state = compute_market_state(spy_df, len(spy_df)-1)
        >>> qqq_state = compute_market_state(qqq_df, len(qqq_df)-1)
        >>> 
        >>> # Create portfolio
        >>> portfolio = PortfolioInput(assets=[
        ...     AssetInput("SPY", 0.6, spy_state),
        ...     AssetInput("QQQ", 0.4, qqq_state)
        ... ])
        >>> 
        >>> # Compute portfolio state
        >>> pf_state = compute_portfolio_state(portfolio)
        >>> print(f"{pf_state.portfolio_regime}: {pf_state.portfolio_criticality}")
    """
    # Step 1: Validate input
    portfolio.validate()
    
    # Step 2: Compute portfolio criticality (weighted mean)
    portfolio_criticality = compute_portfolio_criticality(portfolio)
    
    # Step 3: Map to regime (same thresholds as asset-level)
    raw_regime = map_portfolio_regime(portfolio_criticality)
    
    # Step 5: Apply hysteresis (anti-flicker)
    final_regime, new_confirmation_count = apply_portfolio_hysteresis(
        raw_regime,
        previous_regime,
        confirmation_count
    )
    
    # Step 4: Compute risk attribution (top contributors)
    top_contributors = compute_risk_attribution(portfolio, portfolio_criticality)
    
    # Get date from first asset (all assets should have same date)
    portfolio_date = portfolio.assets[0].state.date
    
    # Step 6: Return PortfolioState (strict contract)
    return PortfolioState(
        date=portfolio_date,
        portfolio_criticality=int(round(portfolio_criticality)),
        portfolio_regime=final_regime,
        top_risk_contributors=top_contributors
    )


# =====================================================================
# HELPER: Portfolio Time Series
# =====================================================================

def compute_portfolio_time_series(
    asset_states_by_date: dict[pd.Timestamp, dict[str, MarketState]],
    weights: dict[str, float]
) -> List[PortfolioState]:
    """
    Compute portfolio states over time with hysteresis.
    
    This is a convenience function for backtesting or historical analysis.
    It maintains hysteresis state across time.
    
    Args:
        asset_states_by_date: Dict mapping date -> {symbol -> MarketState}
        weights: Dict mapping symbol -> weight (must sum to 1.0)
    
    Returns:
        List of PortfolioState objects, one per date, sorted chronologically
    
    Example:
        >>> # Pre-compute all asset states
        >>> asset_states_by_date = {}
        >>> for idx in range(len(spy_df)):
        ...     date = spy_df.index[idx]
        ...     asset_states_by_date[date] = {
        ...         "SPY": compute_market_state(spy_df, idx),
        ...         "QQQ": compute_market_state(qqq_df, idx)
        ...     }
        >>> 
        >>> # Compute portfolio time series
        >>> weights = {"SPY": 0.6, "QQQ": 0.4}
        >>> pf_states = compute_portfolio_time_series(asset_states_by_date, weights)
    """
    # Sort dates chronologically
    sorted_dates = sorted(asset_states_by_date.keys())
    
    portfolio_states = []
    previous_regime = None
    confirmation_count = 0
    
    for date in sorted_dates:
        asset_states = asset_states_by_date[date]
        
        # Build portfolio input
        assets = [
            AssetInput(symbol, weights[symbol], asset_states[symbol])
            for symbol in weights.keys()
            if symbol in asset_states
        ]
        
        portfolio = PortfolioInput(assets=assets)
        
        # Compute portfolio state with hysteresis
        pf_state = compute_portfolio_state(portfolio, previous_regime, confirmation_count)
        
        portfolio_states.append(pf_state)
        
        # Update hysteresis state
        if pf_state.portfolio_regime != previous_regime:
            confirmation_count = 1
        else:
            confirmation_count += 1
        
        previous_regime = pf_state.portfolio_regime
    
    return portfolio_states

