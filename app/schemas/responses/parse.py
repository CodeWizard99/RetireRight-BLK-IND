from pydantic import BaseModel
from datetime import datetime
from typing import List


class TransactionParsed(BaseModel):
    date: str
    amount: float
    ceiling: float
    remanent: float


class ParseResponse(BaseModel):
    transactions: List[TransactionParsed]
    # total_remanent: float