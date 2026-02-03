# app/app.py

import os
import hashlib
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Security, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .schema import (
  MenuSchema, AddStaffSchema, UpdateStaffEmailSchema, UpdateMenuItemSchema,
  MenuScanResponse, CreateOrderSchema, UpdateOrderStatusSchema,
  UpdateUserProfileSchema, VerifyPickupSchema, VerifyPaymentSchema,
  UpdateStaffProfileSchema, UpdateResalePriceSchema
)
from .auth import authenticate_student, verify_staff_access
from .staff import (
  upload_menu, get_menu, scan_menu_image, update_menu_item, delete_menu_item,
  add_staff_member, get_stall_orders, update_order_status_staff, get_staff_me,
  verify_order_pickup, activate_staff, update_staff_profile,
  get_stall_resale_items, update_resale_price
)
from .manager import (
  get_my_staff, remove_staff_member, update_staff_email,
  get_stall_performance_overview
)
from .user import (
  get_user_menu, create_payment_order, get_user_orders,
  verify_payment_and_update_order, update_user_profile, cancel_order,
  get_discounted_feed, buy_resale_item
)
from .webhook import router as webhook_router

def rate_limit_key(request: Request):
  """
    Generate a rate limiting key.
    Uses Authorization token when available, otherwise falls back to IP address.
  """
  auth_header = request.headers.get("authorization")

  if auth_header:
    token_hash = hashlib.sha256(auth_header.encode()).hexdigest()
    return f"user:{token_hash}"

  forwarded = request.headers.get("x-forwarded-for")
  if forwarded:
    return f"ip:{forwarded.split(',')[0].strip()}"

  return f"ip:{request.client.host}"

limiter = Limiter(key_func=rate_limit_key)

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "capacitor://localhost",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://10.0.2.2:3000",
        "http://10.0.2.2:5000",
        "http://10.0.2.2:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

@app.get("/health", tags=["health"])
@limiter.limit("10/minute")
def health_check(request: Request):
  """
    Health check endpoint for monitoring service availability.
  """
  _ = request
  return {
      "status": "ok",
      "service": "greenplate-backend",
      "environment": os.getenv("ENV", "development")
  }

app.include_router(webhook_router)

@app.post('/auth/verify-staff', tags=["auth"])
@limiter.limit("5/minute")
async def verify_staff_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await verify_staff_access(credentials.credentials)

@app.post('/auth/verify-student', tags=["auth"])
@limiter.limit("5/minute")
async def verify_student_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await authenticate_student(credentials.credentials)

@app.patch("/user/profile", tags=["user"])
@limiter.limit("10/minute")
async def update_profile_endpoint(
    request: Request,
    profile_data: UpdateUserProfileSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_user_profile(profile_data, credentials.credentials)

@app.get("/user/menu", tags=["user"])
@limiter.limit("30/minute")
async def get_student_menu_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_user_menu(credentials.credentials)

@app.get("/user/feed/discounted", tags=["user"])
@limiter.limit("30/minute")
async def get_discounted_feed_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_discounted_feed(credentials.credentials)

@app.post("/user/order/create", tags=["user"])
@limiter.limit("5/minute")
async def create_order_endpoint(
    request: Request,
    order_data: CreateOrderSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await create_payment_order(order_data, credentials.credentials)

@app.get("/user/orders", tags=["user"])
@limiter.limit("20/minute")
async def get_student_orders_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_user_orders(credentials.credentials)

@app.post("/user/order/verify",tags=["user"])
@limiter.limit("5/minute")
async def verify_order_endpoint(
    request: Request,
    payment_data: VerifyPaymentSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await verify_payment_and_update_order( payment_data, credentials.credentials )

@app.post("/user/order/{order_id}/cancel", tags=["user"])
@limiter.limit("5/minute")
async def cancel_order_endpoint(
    request: Request,
    order_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await cancel_order(order_id, credentials.credentials)

@app.post("/user/resale/{resale_id}/buy", tags=["user"])
@limiter.limit("10/minute") # Prevent race-condition spamming on hot items
async def buy_resale_item_endpoint(
    request: Request,
    resale_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await buy_resale_item(resale_id, credentials.credentials)

@app.get("/staff/performance/overview", tags=["manager"])
@limiter.limit("10/minute")
async def get_stall_performance_overview_endpoint(
    request: Request,
    month: int,
    year: int,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_stall_performance_overview(month, year, credentials.credentials)

@app.post('/staff/add-member', tags=["manager"])
@limiter.limit("5/minute")
async def add_staff_endpoint(
    request: Request,
    staff_data: AddStaffSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await add_staff_member(staff_data, credentials.credentials)

@app.get('/staff/list', tags=["manager"])
@limiter.limit("20/minute")
async def get_staff_list_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_my_staff(credentials.credentials)

@app.delete('/staff/{staff_uid}', tags=["manager"])
@limiter.limit("5/minute")
async def remove_staff_endpoint(
    request: Request,
    staff_uid: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await remove_staff_member(staff_uid, credentials.credentials)

@app.put('/staff/{staff_uid}/email', tags=["manager"])
@limiter.limit("5/minute")
async def update_staff_email_endpoint(
    request: Request,
    staff_uid: str,
    update_data: UpdateStaffEmailSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_staff_email(staff_uid, update_data.new_email, credentials.credentials)

@app.post("/staff/activate",tags=["staff", "manager"])
@limiter.limit("5/minute")
async def activate_staff_endpoint(
    request: Request,
    credentials:HTTPAuthorizationCredentials = Security(security)
):
    return await activate_staff(credentials.credentials)

@app.get("/staff/me", tags=["staff", "manager"])
@limiter.limit("20/minute")
async def get_staff_me_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_staff_me(credentials.credentials)

@app.patch("/staff/profile", tags=["staff", "manager"])
@limiter.limit("10/minute")
async def update_staff_profile_endpoint(
    request: Request,
    profile_data: UpdateStaffProfileSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_staff_profile(profile_data, credentials.credentials)

@app.post("/staff/menu", tags=["staff", "manager"])
@limiter.limit("5/minute")
async def upload_menu_endpoint(
    request: Request,
    menu_data: MenuSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await upload_menu(menu_data, credentials.credentials)

@app.get("/staff/menu", tags=["staff", "manager"])
@limiter.limit("30/minute")
async def get_staff_menu(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_menu(credentials.credentials)

@app.post("/staff/menu/scan-image", tags=["staff", "manager"], response_model=MenuScanResponse)
@limiter.limit("5/minute")
async def scan_menu_endpoint(
    request: Request,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await scan_menu_image(file, credentials.credentials)

@app.patch("/staff/menu/{item_id}", tags=["staff", "manager"])
@limiter.limit("20/minute")
async def update_menu_item_endpoint(
    request: Request,
    item_id: str,
    update_data: UpdateMenuItemSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_menu_item(item_id, update_data, credentials.credentials)

@app.delete("/staff/menu/{item_id}", tags=["staff", "manager"])
@limiter.limit("20/minute")
async def delete_menu_item_endpoint(
    request: Request,
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await delete_menu_item(item_id, credentials.credentials)

@app.get("/staff/orders", tags=["staff", "manager"])
@limiter.limit("60/minute")
async def get_staff_orders_endpoint(
    request: Request,
    status: str = "PAID",
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_stall_orders(credentials.credentials, status_filter=status)

@app.patch("/staff/orders/{order_id}/status", tags=["staff", "manager"])
@limiter.limit("30/minute")
async def update_order_status_endpoint(
    request: Request,
    order_id: str,
    status_data: UpdateOrderStatusSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_order_status_staff(order_id, status_data, credentials.credentials)

@app.post("/staff/orders/verify-pickup", tags=["staff", "manager"])
@limiter.limit("100/minute")
async def verify_pickup_endpoint(
    request: Request,
    verify_data: VerifyPickupSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await verify_order_pickup(verify_data, credentials.credentials)

@app.get("/staff/resale/items", tags=["staff"])
@limiter.limit("30/minute")
async def get_staff_resale_items_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_stall_resale_items(credentials.credentials)

@app.patch("/staff/resale/{resale_id}/price", tags=["staff"])
@limiter.limit("20/minute")
async def update_resale_price_endpoint(
    request: Request,
    resale_id: str,
    body: UpdateResalePriceSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_resale_price(resale_id, body.new_price, credentials.credentials)
