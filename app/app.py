# app/app.py

from fastapi import FastAPI, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .schema import (
  LoginSchema,
  SignUpSchema,
  MenuSchema,
  StaffSignUpSchema,
  UpdateMenuItemSchema
)
from .auth import (
  auth_signup_users,
  auth_signup_staffs,
  auth_login_staffs,
  auth_login_users
)
from .staff import (
  upload_menu,
  get_menu,
  update_menu_item
)

app = FastAPI()

security = HTTPBearer()


@app.post('/signup/users', tags=["users"])
async def signup_users(user_data: SignUpSchema):
    return await auth_signup_users(user_data)


@app.post('/login/users', tags=["users"])
async def login_users(user_data: LoginSchema):
    return await auth_login_users(user_data)


@app.post('/signup/staffs', tags=["staff"])
async def signup_staffs(user_data: StaffSignUpSchema):
    return await auth_signup_staffs(user_data)


@app.post('/login/staffs', tags=["staff"])
async def login_staffs(user_data: LoginSchema):
    return await auth_login_staffs(user_data)


@app.post("/staff/upload_menu", tags=["staff"])
async def upload_menu_endpoint(
    menu_data: MenuSchema,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    return await upload_menu(menu_data, token)

@app.get("/staff/menu", tags=["staff"])
async def get_staff_menu(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    return await get_menu(token)

@app.patch("/staff/menu/{item_id}", tags=["staff"])
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
