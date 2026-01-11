# app/schema.py

from pydantic import BaseModel, Field
from typing import List, Optional

class AddStaffSchema(BaseModel):
    email: str

class StaffAuthResponse(BaseModel):
    message: str
    role: str
    stall_id: str
    college_id: str

class UpdateStaffEmailSchema(BaseModel):
    new_email: str

class MenuItemSchema(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    description: Optional[str] = None
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

class CartItemSchema(BaseModel):
  item_id: str
  quantity: int = Field(..., gt=0)

class CreateOrderSchema(BaseModel):
  stall_id: str
  items: List[CartItemSchema]
