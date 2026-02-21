from pydantic import BaseModel
from typing import List


class InvalidTransaction(BaseModel):
    date: str
    amount: float
    message: str


class ValidatorResponse(BaseModel):
    valid: List[dict]
    invalid: List[InvalidTransaction]