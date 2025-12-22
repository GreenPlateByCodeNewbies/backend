#app/auth.py

from .schema import LoginSchema, SignUpSchema
from fastapi.responses import JSONResponse
from starlette import status
from firebase_admin import auth
from .firebase_init import firebase

async def auth_signup_users(user_data: SignUpSchema):
  email = user_data.email
  password = user_data.password
  confirm_password = user_data.confirm_password
  if not email.endswith("@tint.edu.in"):
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"message": "College email required"})
  if password != confirm_password:
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"message": "Passwords do not match"})
  try:
      user = auth.create_user(
        email=email,
        password=password
      )
      return JSONResponse(status_code=status.HTTP_201_CREATED,content={"message": "User created successfully", "uid": user.uid})
  except Exception as e:
      return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content={"message": str(e)})

async def auth_login_users(user_data: LoginSchema):
  email = user_data.email
  password = user_data.password
  if not email.endswith("@tint.edu.in"):
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"message": "College email required"})
  try:
      user = firebase.auth().sign_in_with_email_and_password(
        email=email,
        password=password
      )
      id_token = user['idToken']
      return JSONResponse(status_code=status.HTTP_200_OK,content={"message": "Login successful", "idToken": id_token})
  except Exception as e:
      return (JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,content={"message": str(e)}))

async def auth_signup_staffs(user_data: SignUpSchema):
  email = user_data.email
  password = user_data.password
  confirm_password = user_data.confirm_password
  if password != confirm_password:
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"message": "Passwords do not match"})
  try:
      user = auth.create_user(
        email=email,
        password=password
      )
      return JSONResponse(status_code=status.HTTP_201_CREATED,content={"message": "Staff created successfully", "uid": user.uid})
  except Exception as e:
      return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content={"message": str(e)})

async def auth_login_staffs(user_data: LoginSchema):
  email = user_data.email
  password = user_data.password
  try:
      user = firebase.auth().sign_in_with_email_and_password(
        email=email,
        password=password
      )
      id_token = user['idToken']
      return JSONResponse(status_code=status.HTTP_200_OK,content={"message": "Login successful", "idToken": id_token})
  except Exception as e:
      return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,content={"message": str(e)})
