#app/user.py

import os
import random
import razorpay
from fastapi.responses import JSONResponse
from starlette import status
from firebase_admin import auth
from .firebase_init import db, firestore
from datetime import datetime
from .schema import CreateOrderSchema, UpdateUserProfileSchema, VerifyPaymentSchema

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

async def update_user_profile(profile_data: UpdateUserProfileSchema, id_token: str):
  try:
    user_data, user_uid = await get_user_details(id_token)

    if not user_data:
      return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": "Unauthorized"})

    user_ref = db.collection("users").document(user_uid)

    user_ref.update({
      "name": profile_data.name,
      "roll_number": profile_data.roll_number,
      "phone": profile_data.phone,
      "updated_at": firestore.SERVER_TIMESTAMP
    })

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={"message": "Profile updated successfully"}
    )

  except Exception as e:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})

async def verify_payment_and_update_order(payment_data: VerifyPaymentSchema, id_token: str):
    try:
        params_dict = {
          "razorpay_order_id": payment_data.razorpay_order_id,
          "razorpay_payment_id": payment_data.razorpay_payment_id,
          "razorpay_signature": payment_data.razorpay_signature,
        }
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"message": "Signature verification failed"}
            )

        internal_order_id = payment_data.internal_order_id

        order_ref = db.collection("orders").document(internal_order_id)
        order_doc = order_ref.get()

        if not order_doc.exists:
            return JSONResponse(
                status_code=400,
                content={"message": "Order not found"}
            )

        pickup_code = str(random.randint(1000, 9999))

        order_ref.update({
            "razorpay_payment_id": payment_data.razorpay_payment_id,
            "status": "PAID",
          "pickup_code": pickup_code,
            "updated_at": firestore.SERVER_TIMESTAMP
        })

        return JSONResponse(
            status_code=200,
            content={"message": "Payment verified & order updated"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"message": str(e)}
        )

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
    order_items = []

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
        quantity = cart_item.quantity
        total_amount += price * quantity

        order_items.append({
          "item_id": cart_item.item_id,
          "name": item_data.get('name'),
          "price": price,
          "quantity": quantity
        })

      else:
        return JSONResponse(
          status_code=status.HTTP_400_BAD_REQUEST,
          content={"message": "One or more items in your cart no longer exist."}
        )

    if total_amount <= 0:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Invalid order total."}
      )

    user_snapshot = {
      "name": user_data.get("name", "Unknown Student"),
      "roll_number": user_data.get("roll_number", "N/A"),
      "phone": user_data.get("phone", "")
    }

    new_order_ref = db.collection('orders').document()
    internal_order_id = new_order_ref.id

    firestore_order_data = {
      "user_id": user_uid,
      "user_details": user_snapshot,
      "stall_id": stall_id,
      "college_id": college_id,
      "items": order_items,
      "total_amount": total_amount,
      "status": "PENDING",
      "created_at": firestore.SERVER_TIMESTAMP,
      "updated_at": firestore.SERVER_TIMESTAMP
    }

    new_order_ref.set(firestore_order_data)

    data = {
      "amount": int(total_amount * 100),
      "currency": "INR",
      "receipt": f"rcpt_{internal_order_id[:8]}",
      "notes": {
        "stall_id": stall_id,
        "user_uid": user_uid,
        "college_id": college_id,
        "internal_order_id": internal_order_id
      }
    }

    order = razorpay_client.order.create(data=data)

    new_order_ref.update({"razorpay_order_id": order['id']})

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "id": order['id'],
        "amount": order['amount'],
        "currency": order['currency'],
        "key_id": os.environ.get("RAZORPAY_KEY_ID"),
        "internal_order_id": internal_order_id,
        "message": "Order created successfully"
      }
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": f"Payment Error: {str(e)}"}
    )

async def get_user_orders(id_token: str):
  try:
    user_data, user_uid = await get_user_details(id_token)
    if not user_data:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid or expired token."}
      )

    docs = (
       db.collection("orders")
       .where("user_id","==",user_uid)
       .order_by("created_at",direction=firestore.Query.DESCENDING)
       .stream()
    )

    orders = []
    for doc in docs:
      data = doc.to_dict()

      visible_code = data.get("pickup_code") if data.get("status") in ["PAID", "READY"] else None

      orders.append({
         "id": doc.id,
         "items": data["items"],
         "cafeteriaName": data.get("stall_id", "Unknown Stall"),
         "status": normalize_order_status(data["status"]),
         "qrCode": visible_code,
        "total_amount": data.get("total_amount", 0)
      })
      
    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content=orders
    )

  except Exception as e:
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": str(e)}
    )

def normalize_order_status(status:str):
   return{
      "PENDING": "Payment Pending",
      "PAID": "Reserved",
      "CLAIMED": "Claimed",
      "READY": "Ready",
      "COMPLETED": "Completed"
   }.get(status,"Unknown")
