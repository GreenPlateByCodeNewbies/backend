# app/staff.py

import os
from dotenv import load_dotenv
import json
import google.generativeai as genai
from fastapi import UploadFile
from .schema import MenuSchema, UpdateMenuItemSchema, AddStaffSchema, UpdateOrderStatusSchema, VerifyPickupSchema
from fastapi.responses import JSONResponse
from starlette import status
from .firebase_init import db
from firebase_admin import auth, firestore
from datetime import datetime

load_dotenv()

if os.environ.get("GEMINI_API_KEY"):
  genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

async def get_staff_details(id_token: str):
  try:
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token["uid"]

    staff_doc = db.collection("staffs").document(uid).get()
    if staff_doc.exists:
      data = staff_doc.to_dict()

      if data.get("status", "").strip() != "active":
        return None, None
      
      return data,uid

    return None, None

  except auth.ExpiredIdTokenError:
    print("Token expired")
    return None, None
  except auth.InvalidIdTokenError:
    print("Invalid token")
    return None, None
  except Exception as e:
    print(f"Auth Error: {e}")
    return None, None

def serialize_firestore_data(data: dict):
  for key, value in data.items():
    if isinstance(value, datetime):
      data[key] = value.isoformat()
  return data

def validate_extracted_items(items):
  if not isinstance(items, list):
    raise ValueError("AI output is not a list")

  validated = []
  for item in items:
    if not isinstance(item, dict):
      continue

    name = item.get("name")
    price = item.get("price")
    description = item.get("description")

    if not name or not isinstance(name, str):
      continue

    if price is not None and not isinstance(price, (int, float)):
      price = None

    if not description or not isinstance(description, str):
      description = ""

    description_words = description.split()
    if len(description_words) > 7:
      description = " ".join(description_words[:7])

    validated.append({
      "name": name.strip(),
      "price": price,
      "description": description.strip()
    })

  return validated

async def add_staff_member(staff_data: AddStaffSchema, id_token: str):
  try:
    requester_data, requester_uid = await get_staff_details(id_token)

    if not requester_data:
      return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": "Invalid credentials"})

    if requester_data["role"] != "manager":
      return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": "Only Managers can add staff."})

    email = staff_data.email.lower()
    stall_id = requester_data["stall_id"]
    college_id = requester_data["college_id"]

    existing = db.collection("staffs").where("email", "==", email).limit(1).get()
    if existing:
      doc = existing[0]
      if doc.to_dict().get("status") == "active":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "User is already a staff member."})

    try:
      user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
      user = auth.create_user(email=email)

    reset_link = auth.generate_password_reset_link(email)

    db.collection("staffs").document(user.uid).set({
      "email": email,
      "stall_id": stall_id,
      "college_id": college_id,
      "role": "staff",
      "status":"active",
      "added_by": requester_data["email"],
      "created_at": firestore.SERVER_TIMESTAMP
    })
    return JSONResponse(
      status_code=status.HTTP_201_CREATED,
      content={"message": f"Staff {email} added successfully.",
                "reset_link": reset_link 
              }
    )

  except Exception as e:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})
  
async def get_my_staff_profile(id_token:str):
  staff_data, uid = await get_staff_details(id_token)

  if not staff_data:
    return JSONResponse(
      status_code=status.HTTP_401_UNAUTHORIZED,
      content={"message":"Unauthorized"}
    )
  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={
      "uid":uid,
      "email":staff_data["email"],
      "role":staff_data["role"],
      "stall_id":staff_data["stall_id"],
      "college_id":staff_data["college_id"]
    }
  )

async def get_staff_me(id_token: str):
    staff_data, staff_uid = await get_staff_details(id_token)

    if not staff_data:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Unauthorized"}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "uid": staff_uid,
            "email": staff_data.get("email"),
            "role": staff_data.get("role"),
            "stall_id": staff_data.get("stall_id"),
            "college_id": staff_data.get("college_id"),
        }
    )

async def upload_menu(menu_data: MenuSchema, id_token: str):
  try:
    staff_data, staff_uid = await get_staff_details(id_token)

    if not staff_data:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid or expired token."}
      )

    if not menu_data.items:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Menu items cannot be empty."}
      )

    staff_college_id = staff_data.get("college_id")
    staff_stall_id = staff_data.get("stall_id")

    if staff_stall_id != menu_data.stall_id:
      return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
          "message": f"Unauthorized. You can only manage stall: {staff_stall_id}"
        }
      )

    stall_ref = (
      db.collection("colleges")
      .document(staff_college_id)
      .collection("stalls")
      .document(staff_stall_id)
    )

    if not stall_ref.get().exists:
      return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Stall not found. Contact admin."}
      )

    menu_items_ref = stall_ref.collection("menu_items")

    batch = db.batch()

    for item in menu_data.items:
      item_ref = menu_items_ref.document()
      batch.set(item_ref, {
        **item.model_dump(),
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP
      })

    batch.set(
      stall_ref,
      {
        "last_updated_by": staff_uid,
        "last_updated_at": firestore.SERVER_TIMESTAMP
      },
      merge=True
    )

    batch.commit()

    return JSONResponse(
      status_code=status.HTTP_201_CREATED,
      content={
        "message": "Menu uploaded successfully",
        "stall_id": staff_stall_id,
        "items_added": len(menu_data.items)
      }
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": str(e)}
    )

async def get_menu(id_token: str):
  try:
    staff_data, staff_uid = await get_staff_details(id_token)

    if not staff_data:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid or expired token."}
      )

    staff_college_id = staff_data.get("college_id")
    staff_stall_id = staff_data.get("stall_id")

    stall_ref = (
      db.collection("colleges")
      .document(staff_college_id)
      .collection("stalls")
      .document(staff_stall_id)
    )

    if not stall_ref.get().exists:
      return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Stall not found. Contact admin."}
      )

    menu_items_ref = (
      stall_ref
      .collection("menu_items")
      .order_by("created_at")
    )

    menu_items_docs = menu_items_ref.stream()

    menu_items = []
    for doc in menu_items_docs:
      item = doc.to_dict()
      item["item_id"] = doc.id
      item = serialize_firestore_data(item)
      menu_items.append(item)

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "stall_id": staff_stall_id,
        "menu_items": menu_items
      }
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": str(e)}
    )

async def update_menu_item(
    item_id: str,
    update_data: UpdateMenuItemSchema,
    id_token: str
):
  try:
    staff_data, staff_uid = await get_staff_details(id_token)

    if not staff_data:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid or expired token."}
      )

    staff_college_id = staff_data.get("college_id")
    staff_stall_id = staff_data.get("stall_id")

    item_ref = (
      db.collection("colleges")
      .document(staff_college_id)
      .collection("stalls")
      .document(staff_stall_id)
      .collection("menu_items")
      .document(item_id)
    )

    item_doc = item_ref.get()
    if not item_doc.exists:
      return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Menu item not found."}
      )

    updates = {
      key: value
      for key, value in update_data.model_dump().items()
      if value is not None
    }

    if not updates:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "No valid fields provided for update."}
      )

    updates["updated_at"] = firestore.SERVER_TIMESTAMP

    item_ref.update(updates)

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "message": "Menu item updated successfully",
        "item_id": item_id
      }
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": str(e)}
    )

async def delete_menu_item(item_id: str, id_token: str):
  try:
    staff_data, staff_uid = await get_staff_details(id_token)

    if not staff_data:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid or expired token."}
      )

    staff_college_id = staff_data.get("college_id")
    staff_stall_id = staff_data.get("stall_id")

    item_ref = (
      db.collection("colleges")
      .document(staff_college_id)
      .collection("stalls")
      .document(staff_stall_id)
      .collection("menu_items")
      .document(item_id)
    )

    if not item_ref.get().exists:
      return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Menu item not found."}
      )

    item_ref.delete()

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "message": "Menu item deleted successfully",
        "item_id": item_id
      }
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": str(e)}
    )

def _extract_menu_from_image(image_bytes: bytes, mime_type: str) -> list:
  if not os.environ.get("GEMINI_API_KEY"):
    raise Exception("GEMINI_API_KEY is missing from environment variables!")

  model = genai.GenerativeModel('gemini-2.5-flash')

  prompt = """
You are an API that extracts food menu information from images.

Rules:
1. Extract ONLY food item names and prices.
2. The menu may use formats like ': 25/-'. Ignore ':' and '/-' and extract only the number.
3. If a price is missing or unclear, set it to null.
4. For each food item, generate a short description (6–7 words max) based only on the item name.
5. Do NOT hallucinate exotic ingredients. Keep descriptions simple and generic.
6. Return ONLY a valid JSON array. No extra text.

Output format:
[
  {
    "name": "Veg Roll",
    "price": 25,
    "description": "Vegetable filling wrapped in soft roll"
  },
  {
    "name": "Chicken Momo",
    "price": 60,
    "description": "Steamed dumplings filled with chicken"
  }
]
"""

  response = model.generate_content([
    prompt,
    {
      "mime_type": mime_type,
      "data": image_bytes
    }
  ])

  cleaned_text = response.text.strip()
  if cleaned_text.startswith("```json"):
    cleaned_text = cleaned_text[7:]
  if cleaned_text.endswith("```"):
    cleaned_text = cleaned_text[:-3]

  raw_items = json.loads(cleaned_text)
  return validate_extracted_items(raw_items)

async def scan_menu_image(file: UploadFile, id_token: str):
  try:
    staff_data, staff_uid = await get_staff_details(id_token)

    if not staff_data:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid or expired token."}
      )

    if file.content_type not in ["image/jpeg", "image/png"]:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Invalid file type. Only JPEG and PNG allowed."}
      )

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
      return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={"message": "File too large. Max 5MB."}
      )

    extracted_items = _extract_menu_from_image(contents, file.content_type)

    if not extracted_items:
      return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": "Could not extract menu items. Image might be unclear."}
      )

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "message": "Scan complete. Please verify items.",
        "detected_items": extracted_items,
        "count": len(extracted_items)
      }
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": f"Internal Server Error: {str(e)}"}
    )

async def get_stall_orders(id_token: str, status_filter: str = "PAID"):
  try:
    staff_data, _ = await get_staff_details(id_token)

    if not staff_data:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid or expired token."}
      )

    stall_id = staff_data.get("stall_id")

    orders_ref = (
      db.collection("orders")
      .where("stall_id", "==", stall_id)
      .where("status", "==", status_filter)
      .order_by("created_at", direction=firestore.Query.DESCENDING)
    )

    docs = orders_ref.stream()

    orders_list = []
    for doc in docs:
      data = doc.to_dict()
      data['order_id'] = doc.id

      data = serialize_firestore_data(data)

      orders_list.append(data)

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "stall_id": stall_id,
        "count": len(orders_list),
        "orders": orders_list
      }
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": str(e)}
    )

async def update_order_status_staff(order_id: str, status_data: UpdateOrderStatusSchema, id_token: str):
  try:
    staff_data, _ = await get_staff_details(id_token)
    if not staff_data:
      return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": "Unauthorized"})

    stall_id = staff_data.get("stall_id")

    order_ref = db.collection("orders").document(order_id)
    order_doc = order_ref.get()

    if not order_doc.exists:
      return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Order not found"})

    order_data = order_doc.to_dict()

    if order_data.get("stall_id") != stall_id:
      return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"message": "You cannot update orders from other stalls."}
      )

    order_ref.update({
      "status": status_data.status,
      "updated_at": firestore.SERVER_TIMESTAMP,
      "updated_by": staff_data.get("email")
    })

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": f"Order status updated to {status_data.status}"})

  except Exception as e:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})

async def verify_order_pickup(verify_data: VerifyPickupSchema, id_token: str):
  try:
    staff_data, _ = await get_staff_details(id_token)
    if not staff_data:
      return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": "Unauthorized"})

    order_ref = db.collection("orders").document(verify_data.order_id)
    order_doc = order_ref.get()

    if not order_doc.exists:
      return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Order not found"})

    data = order_doc.to_dict()

    if data.get("stall_id") != staff_data.get("stall_id"):
      return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": "Wrong stall"})

    if data.get("status") != "PAID":
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "Order is not PAID yet."})

    stored_code = data.get("pickup_code")
    if stored_code != verify_data.pickup_code:
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "Incorrect Pickup Code!"})

    order_ref.update({
      "status": "CLAIMED",
      "picked_up_at": firestore.SERVER_TIMESTAMP,
      "handled_by": staff_data.get("email")
    })

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={"message": "Order verified and delivered!", "status": "CLAIMED"}
    )

  except Exception as e:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})
