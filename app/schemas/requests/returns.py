from pydantic import BaseModel
from typing import List


# ──────────────────────────────────────────────
# Period models
# ──────────────────────────────────────────────

class QPeriod(BaseModel):
    fixed: float
    start: str
    end: str


class PPeriod(BaseModel):
    extra: float
    start: str
    end: str


class KPeriod(BaseModel):
    start: str
    end: str


# ──────────────────────────────────────────────
# Transactions
# ──────────────────────────────────────────────

class Transaction(BaseModel):
    date: str
    amount: float


# ──────────────────────────────────────────────
# Returns Request
# ──────────────────────────────────────────────

class ReturnsRequest(BaseModel):
    age: int
    wage: float
    inflation: float

    q: List[QPeriod]
    p: List[PPeriod]
    k: List[KPeriod]

    transactions: List[Transaction]