from pydantic import BaseModel
from typing import List
from datetime import datetime


class QPeriod(BaseModel):
    fixed: float
    start: datetime
    end: datetime


class PPeriod(BaseModel):
    extra: float
    start: datetime
    end: datetime


class KPeriod(BaseModel):
    start: datetime
    end: datetime


class Expense(BaseModel):
    date: datetime
    amount: float


class FilterRequest(BaseModel):
    q: List[QPeriod]
    p: List[PPeriod]
    k: List[KPeriod]
    wage: float
    transactions: List[Expense]