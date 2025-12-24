# app/schema.py

from pydantic import BaseModel, Field
from typing import List, Optional

class SignUpSchema(BaseModel):
    email: str
    password: str
    confirm_password: str

class StaffSignUpSchema(BaseModel):
    email: str
    password: str
    confirm_password: str
    stall_id: str

class LoginSchema(BaseModel):
    email: str
    password: str

class MenuItemSchema(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    description: str | None = None
    is_available: bool = True

class MenuSchema(BaseModel):
    stall_id: str
    items: List[MenuItemSchema]

class UpdateMenuItemSchema(BaseModel):
  name: Optional[str] = None
  price: Optional[float] = None
  description: Optional[str] = None
  is_available: Optional[bool] = None


class ExtractedMenuItem(BaseModel):
  name: str = Field(..., description="The name of the food item")
  price: Optional[float] = Field(None, description="The price of the item")
  description: str = Field("", description="Short AI-generated description (6–7 words)")


class MenuScanResponse(BaseModel):
    detected_items: List[ExtractedMenuItem]
    count: int
    message: str = "Scan complete. Please verify items before saving."
