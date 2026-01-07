#get_token.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FIREBASE_API_KEY")

def get_test_token(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload, timeout=(3, 10))
    if response.status_code == 200:
        token = response.json()['idToken']
        print("\n✅ SUCCESS! Here is your Bearer Token for Swagger:\n")
        print(token)
        print("\n(Copy the long string above and paste it into the 'Authorize' button in Swagger UI)\n")
    else:
        print("\n❌ Error:", response.json())

if __name__ == "__main__":
    print("--- Get Test Token for GreenPlate ---")
    e = input("Enter Email (must exist in Firebase Auth): ")
    p = input("Enter Password: ")
    get_test_token(e, p)