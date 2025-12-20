from fastapi import FastAPI
from starlette import status
from .config import firebaseConfig
import pyrebase
import firebase_admin
from firebase_admin import credentials, auth
from .schema import LoginSchema, SignUpSchema
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

app = FastAPI()

firebase = pyrebase.initialize_app(firebaseConfig)

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

@app.post('/signup')
async def signup(user_data: SignUpSchema):
  email = user_data.email
  password = user_data.password
  try:
      user = auth.create_user(
        email=email,
        password=password
      )
      auth.send_email_verification(user['idToken'])
      return JSONResponse(status_code=status.HTTP_201_CREATED,content={"message": "User created successfully", "uid": user.uid})
  except Exception as e:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message": str(e)})

@app.post('/login')
async def login(user_data: LoginSchema):
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
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={"message": "Invalid credentials"})