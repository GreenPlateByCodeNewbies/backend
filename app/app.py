#app/app.py

from fastapi import FastAPI
from .schema import LoginSchema, SignUpSchema
from .auth import auth_signup_users, auth_signup_staffs, auth_login_staffs, auth_login_users

app = FastAPI()

@app.post('/signup/users')
async def signup_users(user_data: SignUpSchema):
    return await auth_signup_users(user_data)

@app.post('/login/users')
async def login_users(user_data: LoginSchema):
    return await auth_login_users(user_data)

@app.post('/signup/staffs')
async def signup_staffs(user_data: SignUpSchema):
    return await auth_signup_staffs(user_data)

@app.post('/login/staffs')
async def login_staffs(user_data: LoginSchema):
    return await auth_login_staffs(user_data)
