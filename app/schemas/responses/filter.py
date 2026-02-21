from pydantic import BaseModel
from datetime import datetime
from typing import List


class KPeriodResult(BaseModel):
    start: datetime
    end: datetime
    amount: float


class FilterResponse(BaseModel):
    savings_by_period: List[KPeriodResult]