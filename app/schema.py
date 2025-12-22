#app/schema.py

from pydantic import BaseModel

class SignUpSchema(BaseModel):
    email: str
    password: str
    confirm_password: str

class LoginSchema(BaseModel):
    email: str
    password: str
