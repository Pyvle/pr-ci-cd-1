
from pydantic import BaseModel, Field

class ImageCreate(BaseModel):
    url: str = Field(..., min_length=3)

class VideoCreate(BaseModel):
    url: str = Field(..., min_length=3)
    title: str | None = Field(None, max_length=200)

class GalleryUpdate(BaseModel):
    urls: list[str] = Field(default_factory=list)
