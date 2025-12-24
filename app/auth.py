# app/auth.py

from .schema import LoginSchema, SignUpSchema, StaffSignUpSchema
from fastapi.responses import JSONResponse
from starlette import status
from firebase_admin import auth, firestore
from .firebase_init import db, firebase

def _validate_passwords(password: str, confirm_password: str):
    if password != confirm_password:
        return False, "Passwords do not match"
    return True, ""

def _get_college_by_domain(email: str):
    try:
        domain = email.split("@")[-1]
        query = (
            db.collection("colleges")
            .where("domains", "array_contains", domain)
            .limit(1)
        )
        docs = query.stream()

        for doc in docs:
            return doc.id, doc.to_dict()

        return None, None
    except Exception as e:
        print(f"College lookup error: {e}")
        return None, None

def _create_response(status_code: int, message: str, **kwargs):
    content = {"message": message}
    content.update(kwargs)
    return JSONResponse(status_code=status_code, content=content)

async def auth_signup_users(user_data: SignUpSchema):
    email = user_data.email
    password = user_data.password
    confirm_password = user_data.confirm_password

    valid, msg = _validate_passwords(password, confirm_password)
    if not valid:
        return _create_response(status.HTTP_400_BAD_REQUEST, msg)

    college_id, college_data = _get_college_by_domain(email)
    if not college_id:
        return _create_response(
            status.HTTP_400_BAD_REQUEST,
            "Your college domain is not registered with GreenPlate.",
        )

    try:
        user = auth.create_user(email=email, password=password)

        db.collection("users").document(user.uid).set(
            {
                "email": email,
                "college_id": college_id,
                "college_name": college_data.get("name"),
                "role": "student",
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )

        return _create_response(
            status.HTTP_201_CREATED, "User created successfully", uid=user.uid
        )

    except Exception as e:
        return _create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

async def auth_signup_staffs(user_data: StaffSignUpSchema):
    email = user_data.email
    password = user_data.password
    confirm_password = user_data.confirm_password
    stall_id = user_data.stall_id

    valid, msg = _validate_passwords(password, confirm_password)
    if not valid:
        return _create_response(status.HTTP_400_BAD_REQUEST, msg)

    college_id, _ = _get_college_by_domain(email)
    if not college_id:
        return _create_response(
            status.HTTP_400_BAD_REQUEST, "Your college domain is not registered."
        )

    try:
        user = auth.create_user(email=email, password=password)

        db.collection("staffs").document(user.uid).set(
            {
                "email": email,
                "stall_id": stall_id,
                "college_id": college_id,
                "role": "staff",
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )

        return _create_response(
            status.HTTP_201_CREATED, "Staff created successfully", uid=user.uid
        )

    except Exception as e:
        return _create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

async def auth_login_users(user_data: LoginSchema):
    email = user_data.email
    password = user_data.password

    college_id, _ = _get_college_by_domain(email)
    if not college_id:
        return _create_response(
            status.HTTP_400_BAD_REQUEST,
            "Your college domain is not registered.",
        )

    try:
        user = firebase.auth().sign_in_with_email_and_password(email, password)
        return _create_response(
            status.HTTP_200_OK,
            "Login successful",
            idToken=user["idToken"],
        )
    except Exception as e:
        return _create_response(status.HTTP_401_UNAUTHORIZED, str(e))

async def auth_login_staffs(user_data: LoginSchema):
    email = user_data.email
    password = user_data.password

    try:
        user = firebase.auth().sign_in_with_email_and_password(email, password)
        id_token = user["idToken"]

        decoded = auth.verify_id_token(id_token)
        uid = decoded["uid"]

        staff_doc = db.collection("staffs").document(uid).get()
        if not staff_doc.exists:
            return _create_response(
                status.HTTP_403_FORBIDDEN,
                "Not a staff account.",
            )

        return _create_response(
            status.HTTP_200_OK,
            "Login successful",
            idToken=id_token,
        )

    except Exception as e:
        return _create_response(status.HTTP_401_UNAUTHORIZED, str(e))
