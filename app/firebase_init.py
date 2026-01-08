#app/firebase_init.py

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

IS_CI = os.environ.get("CI") == "true"

firebase_credentials = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

if not firebase_credentials and not IS_CI:
    raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env variable not set")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)

db = firestore.client()
