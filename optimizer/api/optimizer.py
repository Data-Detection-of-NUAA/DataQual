from .diagnosis import router as diagnosis_router
from .strategy import router as strategy_router
from .review import router as review_router
from .execution import router as execution_router

__all__ = ["diagnosis_router", "strategy_router", "review_router", "execution_router"]
