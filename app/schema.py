# app/schema.py

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class AddStaffSchema(BaseModel):
    email: EmailStr

class StaffAuthResponse(BaseModel):
    message: str
    role: str
    stall_id: str
    college_id: str

class UpdateStaffEmailSchema(BaseModel):
    new_email: str

class UpdateUserProfileSchema(BaseModel):
  name: str = Field(..., min_length=2)
  roll_number: str = Field(..., min_length=1)
  phone: Optional[str] = None

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

class OrderItemSchema(BaseModel):
  name: str
  quantity: int
  price: float

class OrderResponseSchema(BaseModel):
  order_id: str
  user_id: str
  amount: float
  status: str
  items: List[OrderItemSchema]
  created_at: str

class UpdateOrderStatusSchema(BaseModel):
  status: str

class VerifyPaymentSchema(BaseModel):
  razorpay_order_id: str
  razorpay_payment_id: str
  razorpay_signature: str
  internal_order_id: str

class VerifyPickupSchema(BaseModel):
  order_id: str
  pickup_code: str = Field(..., min_length=4, max_length=4, description="4-digit pickup code")
