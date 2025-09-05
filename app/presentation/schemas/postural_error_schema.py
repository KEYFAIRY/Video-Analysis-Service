from pydantic import BaseModel, Field


class PosturalErrorResponse(BaseModel):
    """Response with information about a postural error"""
    min_sec: float = Field(..., description="Minute and second when the error occurs", example=12.5)
    explication: str = Field(..., description="Explication of the postural error", example="Incorrect finger placement")

    class Config:
        schema_extra = {
            "example": {
                "min_sec": 12.5,
                "explication": "Incorrect hand placement"
            }
        }