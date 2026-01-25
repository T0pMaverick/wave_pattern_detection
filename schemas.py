from pydantic import BaseModel

class PatternRequest(BaseModel):
    company_symbol: str
