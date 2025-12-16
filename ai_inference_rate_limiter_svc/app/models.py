from pydantic import BaseModel
from typing import Optional

class LimitCheckRequest(BaseModel):
    user_id: str
    model_id: str
    max_limit: Optional[int] = None