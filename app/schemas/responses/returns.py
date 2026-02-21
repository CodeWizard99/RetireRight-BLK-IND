from pydantic import BaseModel
from datetime import datetime
from typing import List


class ReturnsPeriodResult(BaseModel):
    start: datetime
    end: datetime
    invested: float
    final_value: float
    real_value: float
    tax_benefit: float | None = None


class ReturnsResponse(BaseModel):
    instrument: str
    results: List[ReturnsPeriodResult]