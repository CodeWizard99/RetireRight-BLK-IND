from pydantic import BaseModel, Field
from typing import List
from app.schemas.common import Expense, Period


class ReturnsRequest(BaseModel):
    age: int = Field(..., ge=0)
    wage: float = Field(..., ge=0)
    inflation: float = Field(..., ge=0)

    expenses: List[Expense]
    q_periods: List[Period]
    p_periods: List[Period]
    k_periods: List[Period]