#app/firebase_init.py

import os
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
from dotenv import load_dotenv

load_dotenv()

IS_CI = os.environ.get("CI") == "true"

firebaseConfig = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
}

firebase = pyrebase.initialize_app(firebaseConfig)

firebase_credentials = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

if not firebase_credentials and not IS_CI:
    raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env variable not set")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)

db = firestore.client()
