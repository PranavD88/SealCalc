from typing import Optional
from sqlmodel import SQLModel, Field, Column, Integer


class Seal(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True)
    )

    timestamp: str = Field(index=True)

    image_id: Optional[str] = None
    image_path: Optional[str] = None

    eyes: int
    mouth: int
    hair: int
    pattern: int
    base_color: int
    pattern_color: int

    predicted_value: Optional[float] = None
    actual_value: Optional[float] = None
    label: Optional[str] = None
    true_value: Optional[float] = None
