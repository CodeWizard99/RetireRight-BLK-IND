from pydantic import RootModel
from typing import List
from app.schemas.common import Expense

class ParseRequest(RootModel[List[Expense]]):
    # expenses: List[Expense]
    pass