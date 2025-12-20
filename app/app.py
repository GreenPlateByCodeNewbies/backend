from fastapi import FastAPI
from .config import firebaseConfig
import pyrebase
import firebase_admin
from firebase_admin import credentials

app = FastAPI()

firebase = pyrebase.initialize_app(firebaseConfig)

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

@app.post('/signup')
async def signup():
  pass

@app.post('/login')
async def login():
  pass

@app.post('/logout')
async def logout():
  pass

@app.post('ping')
async def validate_token():
  pass
