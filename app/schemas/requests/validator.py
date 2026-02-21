from pydantic import BaseModel
from typing import List
from app.schemas.common import ParsedTransaction


class ValidatorRequest(BaseModel):
    wage: float
    transactions: List[ParsedTransaction]