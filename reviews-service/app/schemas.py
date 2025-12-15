
from pydantic import BaseModel, Field

class ReviewCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    text: str = Field(..., min_length=1)

class ReviewUpdate(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    text: str | None = Field(None, min_length=1)

class ReportCreate(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)

class VoteRequest(BaseModel):
    value: int = Field(..., description="+1 = полезный, -1 = бесполезный")
