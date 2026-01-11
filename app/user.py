#app/user.py

import os
import razorpay
from fastapi.responses import JSONResponse
from starlette import status
from firebase_admin import auth
from .firebase_init import db
from datetime import datetime
from .schema import CreateOrderSchema

razorpay_client = razorpay.Client(auth=(
    os.environ.get("RAZORPAY_KEY_ID"),
    os.environ.get("RAZORPAY_KEY_SECRET")
))

async def get_user_details(id_token: str):
  try:
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token["uid"]

    user_doc = db.collection("users").document(uid).get()
    if user_doc.exists:
      return user_doc.to_dict(), uid

    return None, None

  except Exception:
    return None, None

def serialize_firestore_data(data: dict):
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
    return data


async def get_user_menu(id_token: str):
    try:
        user_data, user_uid = await get_user_details(id_token)

        if not user_data:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Invalid or expired token."}
            )

        college_id = user_data.get("college_id")

        stalls_ref = (
            db.collection("colleges")
            .document(college_id)
            .collection("stalls")
            .where("status", "==", "active")
            .where("isVerified", "==", True)
        )

        stalls_docs = stalls_ref.stream()

        stalls_response = []

        for stall_doc in stalls_docs:
            stall_data = stall_doc.to_dict()
            stall_id = stall_doc.id

            menu_items_ref = (
                stall_doc.reference
                .collection("menu_items")
                .where("is_available", "==", True)
                .order_by("created_at")
            )

            menu_items_docs = menu_items_ref.stream()

            menu_items = []
            for item_doc in menu_items_docs:
                item = item_doc.to_dict()
                item["item_id"] = item_doc.id
                item = serialize_firestore_data(item)
                item.pop("created_at", None)
                item.pop("updated_at", None)

                menu_items.append(item)

            if menu_items:
                stalls_response.append({
                    "stall_id": stall_id,
                    "stall_name": stall_data.get("name"),
                    "menu_items": menu_items
                })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "college_id": college_id,
                "stalls": stalls_response
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )


async def create_payment_order(order_data: CreateOrderSchema, id_token: str):
  try:
    user_data, user_uid = await get_user_details(id_token)
    if not user_data:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid or expired token."}
      )

    college_id = user_data.get("college_id")
    stall_id = order_data.stall_id

    total_amount = 0

    menu_ref = (
      db.collection("colleges")
      .document(college_id)
      .collection("stalls")
      .document(stall_id)
      .collection("menu_items")
    )

    for cart_item in order_data.items:
      item_doc = menu_ref.document(cart_item.item_id).get()

      if item_doc.exists:
        item_data = item_doc.to_dict()

        if item_data.get('is_available') is False:
          return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"Sorry, {item_data.get('name')} is currently out of stock."}
          )

        price = item_data.get('price', 0)
        total_amount += price * cart_item.quantity
      else:
        return JSONResponse(
          status_code=status.HTTP_400_BAD_REQUEST,
          content={"message": "One or more items in your cart no longer exist."}
        )

    if total_amount <= 0:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Invalid order total (0). Check item availability."}
      )

    data = {
      "amount": int(total_amount * 100),
      "currency": "INR",
      "receipt": f"order_{user_uid[:5]}_{int(datetime.now().timestamp())}",
      "notes": {
        "stall_id": stall_id,
        "user_uid": user_uid,
        "college_id": college_id
      }
    }

    order = razorpay_client.order.create(data=data)

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "id": order['id'],
        "amount": order['amount'],
        "currency": order['currency'],
        "key_id": os.environ.get("RAZORPAY_KEY_ID"),
        "message": "Order created successfully"
      }
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": f"Payment Error: {str(e)}"}
    )
