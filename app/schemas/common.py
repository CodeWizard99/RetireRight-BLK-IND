from pydantic import BaseModel, Field
from datetime import datetime

class Expense(BaseModel):
    date: datetime = Field(..., description="Expense timestamp")
    amount: float = Field(..., ge=0)


class ParsedTransaction(BaseModel):
    date: datetime
    amount: float
    ceiling: float
    remanent: float

class Period(BaseModel):
    start: datetime
    end: datetime
    value: float | None = Field(
        default=None,
        description="fixed (q) OR extra (p). Not used for k."
    )
