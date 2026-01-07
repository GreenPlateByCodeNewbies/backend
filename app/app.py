# app/app.py

from fastapi import FastAPI, Security, File, UploadFile
#newly added for the cors problem 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .schema import (
  LoginSchema,
  SignUpSchema,
  MenuSchema,
  AddStaffSchema,
  UpdateStaffEmailSchema,
  UpdateMenuItemSchema,
  MenuScanResponse
)
from .auth import (
  auth_signup_users,
  auth_login_users,
  verify_staff_access
)
from .staff import (
  upload_menu,
  get_menu,
  scan_menu_image,
  update_menu_item,
  delete_menu_item,
  add_staff_member,
)
from .manager import (
  get_my_staff,
  remove_staff_member,
  update_staff_email,
)
from .user import get_user_menu

app = FastAPI()
# app/app.py

app.add_middleware(
    CORSMiddleware,
    # Allow both localhost and the 127.0.0.1 loopback
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBearer()

@app.post('/auth/verify-staff', tags=["verify"])
async def verify_staff(credentials: HTTPAuthorizationCredentials = Security(security)):
    return await verify_staff_access(credentials.credentials)

@app.post('/signup/users', tags=["user"])
async def signup_users(user_data: SignUpSchema):
    return await auth_signup_users(user_data)

@app.post('/login/users', tags=["user"])
async def login_users(user_data: LoginSchema):
    return await auth_login_users(user_data)

@app.get("/user/menu", tags=["user"])
async def get_student_menu_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await get_user_menu(credentials.credentials)

@app.post('/staff/add-member', tags=["manager"])
async def add_staff_endpoint(
    staff_data: AddStaffSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    return await add_staff_member(staff_data, credentials.credentials)

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
