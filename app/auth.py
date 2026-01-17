# app/auth.py

from fastapi.responses import JSONResponse
from starlette import status
from firebase_admin import auth, firestore
from .firebase_init import db


def _create_response(status_code: int, message: str, **kwargs):
  content = {"message": message}
  content.update(kwargs)
  return JSONResponse(status_code=status_code, content=content)


def _get_college_by_domain(email: str):
  try:
    if not email: return None, None
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


async def authenticate_student(token: str):

  try:
    try:
      decoded = auth.verify_id_token(token)
    except Exception:
      return _create_response(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    uid = decoded["uid"]
    email = decoded.get("email")

    if not email:
      return _create_response(status.HTTP_400_BAD_REQUEST, "Invalid token: Email required.")

    user_doc_ref = db.collection("users").document(uid)
    user_doc = user_doc_ref.get()

    if user_doc.exists:
      return _create_response(
        status.HTTP_200_OK,
        "Login successful",
        role="student",
        college_id=user_doc.to_dict().get("college_id")
      )

    college_id, college_data = _get_college_by_domain(email)

    if not college_id:
      try:
        auth.delete_user(uid)
      except:
        pass
      return _create_response(
        status.HTTP_403_FORBIDDEN,
        "Your college domain is not registered with GreenPlate.",
      )

    user_doc_ref.set({
      "email": email,
      "college_id": college_id,
      "college_name": college_data.get("name"),
      "role": "student",
      "created_at": firestore.SERVER_TIMESTAMP,
    })

    return _create_response(
      status.HTTP_201_CREATED,
      "User registered and logged in",
      role="student",
      college_id=college_id
    )

  except Exception as e:
    return _create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


async def verify_staff_access(token: str):
  try:
    decoded = auth.verify_id_token(token)
    email = decoded.get("email")
    uid = decoded.get("uid")

    if not email:
      return _create_response(status.HTTP_400_BAD_REQUEST, "Invalid token: No email found.")

    staff_doc = db.collection("staffs").document(uid).get()

    if staff_doc.exists:
      data = staff_doc.to_dict()
      return _create_response(
        status.HTTP_200_OK,
        "Verified",
        role=data.get("role"),
      )

    college_id, _ = _get_college_by_domain(email)

    if not college_id:
      return _create_response(status.HTTP_403_FORBIDDEN, "Domain not registered.")

    stalls_query = (
      db.collection("colleges")
      .document(college_id)
      .collection("stalls")
      .where("email", "==", email)
      .limit(1)
      .stream()
    )

    found_stall = None
    for doc in stalls_query:
      found_stall = doc
      break

    if found_stall:
      new_staff_data = {
        "email": email,
        "stall_id": found_stall.id,
        "college_id": college_id,
        "role": "manager",
        "created_at": firestore.SERVER_TIMESTAMP,
      }

      db.collection("staffs").document(uid).set(new_staff_data)

      return _create_response(
        status.HTTP_200_OK,
        "Manager account initialized",
        role="manager",
      )

    return _create_response(
      status.HTTP_403_FORBIDDEN,
      "Access Denied. You are not a registered staff member or manager for this college."
    )

  except Exception as e:
    return _create_response(status.HTTP_401_UNAUTHORIZED, str(e))
