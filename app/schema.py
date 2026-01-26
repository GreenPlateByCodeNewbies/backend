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

# --- FIX START ---
class UpdateUserProfileSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    roll_number: Optional[str] = Field(None, min_length=1)
    phone: Optional[str] = None

class UpdateStaffProfileSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    phone: Optional[str] = None
# --- FIX END ---

class MenuItemSchema(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    description: Optional[str] = None
    image_ref: Optional[str] = Field(
      None,
      description="Reference to menu image (URL, CDN key, or placeholder id)"
    )
    is_available: bool = True

class MenuSchema(BaseModel):
    stall_id: str
    items: List[MenuItemSchema]

class UpdateMenuItemSchema(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_ref: Optional[str] = None
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

class StaffStats(BaseModel):
    uid: str
    name: str
    email: str
    role: str
    month_total: int
    today_total: int
    last_active: Optional[str] = None

class StallPerformanceResponse(BaseModel):
    stall_id: str
    period: str
    staff_stats: List[StaffStats]

class ResaleItemSchema(BaseModel):
  resale_id: str
  items: List[dict]
  original_price: float
  discounted_price: float
  stall_name: str
  status: str

class CancelOrderResponse(BaseModel):
  message: str
  resale_created: bool = False
