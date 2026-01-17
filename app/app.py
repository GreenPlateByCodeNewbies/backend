 # app/app.py

import os
from fastapi import FastAPI, Security, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .schema import (
  MenuSchema,
  AddStaffSchema,
  UpdateStaffEmailSchema,
  UpdateMenuItemSchema,
  MenuScanResponse,
  CreateOrderSchema,
  UpdateOrderStatusSchema,
  UpdateUserProfileSchema,
  VerifyPickupSchema,
  VerifyPaymentSchema
)
from .auth import (
  authenticate_student,
  verify_staff_access
)
from .staff import (
  upload_menu,
  get_menu,
  scan_menu_image,
  update_menu_item,
  delete_menu_item,
  add_staff_member,
  get_stall_orders,
  update_order_status_staff,
  get_my_staff_profile,
  get_staff_me,
  verify_order_pickup,
  activate_staff
)
from .manager import (
  get_my_staff,
  remove_staff_member,
  update_staff_email,
)
from .user import (
  get_user_menu,
  create_payment_order,
  get_user_orders,
  verify_payment_and_update_order,
  update_user_profile
)
from .webhook import router as webhook_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

app.include_router(webhook_router)

@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "service": "greenplate-backend",
        "environment": os.getenv("ENV", "development")
    }

@app.post('/auth/verify-staff', tags=["auth"])
async def verify_staff_endpoint(credentials: HTTPAuthorizationCredentials = Security(security)):
    return await verify_staff_access(credentials.credentials)

@app.post('/auth/verify-student', tags=["auth"])
async def verify_student_endpoint(credentials: HTTPAuthorizationCredentials = Security(security)):
    return await authenticate_student(credentials.credentials)

@app.patch("/user/profile", tags=["user"])
async def update_profile_endpoint(
    profile_data: UpdateUserProfileSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_user_profile(profile_data, credentials.credentials)

@app.get("/user/menu", tags=["user"])
async def get_student_menu_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_user_menu(credentials.credentials)

@app.post("/user/order/create", tags=["user"])
async def create_order_endpoint(
    order_data: CreateOrderSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await create_payment_order(order_data, credentials.credentials)

@app.get("/user/orders", tags=["user"])
async def get_student_orders_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_user_orders(credentials.credentials)

@app.post("/user/order/verify",tags=["user"])
async def verify_order_endpoint(
    payment_data: VerifyPaymentSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await verify_payment_and_update_order( payment_data, credentials.credentials )

@app.post('/staff/add-member', tags=["manager"])
async def add_staff_endpoint(
    staff_data: AddStaffSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await add_staff_member(staff_data, credentials.credentials)

@app.post("/staff/activate",tags=["staff"])
async def activate_staff_endpoint(
    credentials:HTTPAuthorizationCredentials = Security(security)
):
    return await activate_staff(credentials.credentials)

@app.get('/staff/list', tags=["manager"])
async def get_staff_list_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_my_staff(credentials.credentials)

@app.delete('/staff/{staff_uid}', tags=["manager"])
async def remove_staff_endpoint(
    staff_uid: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await remove_staff_member(staff_uid, credentials.credentials)

@app.put('/staff/{staff_uid}/email', tags=["manager"])
async def update_staff_email_endpoint(
    staff_uid: str,
    update_data: UpdateStaffEmailSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_staff_email(staff_uid, update_data.new_email, credentials.credentials)

@app.get("/staff/me", tags=["staff", "manager"])
async def get_staff_me_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_staff_me(credentials.credentials)

@app.post("/staff/menu", tags=["staff", "manager"])
async def upload_menu_endpoint(
    menu_data: MenuSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    return await upload_menu(menu_data, token)

@app.get("/staff/menu", tags=["staff", "manager"])
async def get_staff_menu(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    return await get_menu(token)

@app.post("/staff/menu/scan-image", tags=["staff", "manager"], response_model=MenuScanResponse)
async def scan_menu_endpoint(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    return await scan_menu_image(file, token)

@app.patch("/staff/menu/{item_id}", tags=["staff", "manager"])
async def update_menu_item_endpoint(
    item_id: str,
    update_data: UpdateMenuItemSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_menu_item(
        item_id,
        update_data,
        credentials.credentials
    )

@app.delete("/staff/menu/{item_id}", tags=["staff", "manager"])
async def delete_menu_item_endpoint(
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await delete_menu_item(
        item_id,
        credentials.credentials
    )

@app.get("/staff/orders", tags=["staff", "manager"])
async def get_staff_orders_endpoint(
    status: str = "PAID",
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_stall_orders(credentials.credentials, status_filter=status)

@app.patch("/staff/orders/{order_id}/status", tags=["staff", "manager"])
async def update_order_status_endpoint(
    order_id: str,
    status_data: UpdateOrderStatusSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await update_order_status_staff(order_id, status_data, credentials.credentials)

@app.post("/staff/orders/verify-pickup", tags=["staff", "manager"])
async def verify_pickup_endpoint(
    verify_data: VerifyPickupSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await verify_order_pickup(verify_data, credentials.credentials)
