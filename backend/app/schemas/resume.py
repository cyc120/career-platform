from pydantic import BaseModel
from typing import Optional, Dict, Any


class ResumeExtractRequest(BaseModel):
    input_text: str = ""
    supplement_text: str = ""
    supplement_count: int = 0
    user_profile: Optional[Dict[str, Any]] = None
