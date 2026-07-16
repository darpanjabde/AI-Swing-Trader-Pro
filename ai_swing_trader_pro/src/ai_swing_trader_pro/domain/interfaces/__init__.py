"""Domain interfaces (ports).

Abstract contracts that the domain/application layers depend on, and that
concrete infrastructure classes implement — the Dependency Inversion
Principle in action. Nothing in this package imports a broker SDK, an ORM,
or any other framework.
"""

from ai_swing_trader_pro.domain.interfaces.market_data_provider import (
    MarketDataProvider,
)

__all__ = ["MarketDataProvider"]
