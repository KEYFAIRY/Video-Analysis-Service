from pydantic import BaseModel, Field


class PosturalErrorResponse(BaseModel):
    """Response with information about a postural error"""
    min_sec: str = Field(..., description="Minute and second when the error occurs", example="00:12.5")
    frame: int = Field(..., description="Frame number where the error is detected", example=300)
    explication: str = Field(..., description="Explication of the postural error", example="Incorrect finger placement")

    class Config:
        schema_extra = {
            "example": {
                "min_sec": "00:12",
                "frame": 300,
                "explication": "Incorrect hand placement"
            }
        }