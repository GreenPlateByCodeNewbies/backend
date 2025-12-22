#app/firebase_init.py

import firebase_admin
from firebase_admin import credentials
import pyrebase
from .config import firebaseConfig

firebase = pyrebase.initialize_app(firebaseConfig)

if not firebase_admin._apps:
    cred = credentials.Certificate("/Users/skakibahammed/code_playground/GreenPlate/backend/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
