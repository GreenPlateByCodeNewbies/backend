# app/webhook.py
import os
import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException
from firebase_admin import firestore
from .firebase_init import db

router = APIRouter()


@router.post("/webhook/razorpay", tags=["webhook"])
async def razorpay_webhook(request: Request):
  signature = request.headers.get('X-Razorpay-Signature')
  secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET")
  body = await request.body()

  try:
    expected_signature = hmac.new(
      key=secret.encode(),
      msg=body,
      digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
      raise HTTPException(status_code=400, detail="Invalid signature")
  except Exception:
    raise HTTPException(status_code=400, detail="Signature verification failed")

  payload = await request.json()
  event_type = payload.get('event')

  if event_type in ['payment.captured', 'payment_link.paid']:
    payment = payload['payload']['payment']['entity']
    notes = payment.get('notes', {})

    if isinstance(notes, list):
      notes = {}

    stall_id = notes.get('stall_id')
    user_id = notes.get('user_uid')

    if not stall_id:
      stall_id = "manual_test_stall"

    order_data = {
      "order_id": payment['order_id'],
      "payment_id": payment['id'],
      "amount": payment['amount'] / 100,
      "status": "PAID",
      "stall_id": stall_id,
      "user_id": user_id,
      "created_at": firestore.SERVER_TIMESTAMP
    }

    try:
      db.collection('orders').add(order_data)
    except Exception as e:
      print(f"Error saving order to Firestore: {e}")
      raise HTTPException(status_code=500, detail="Failed to save order")

  else:
    print(f"⏭️  Skipping event: {event_type}")

  return {"status": "ok"}
