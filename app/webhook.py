# app/webhook.py

import os
import hmac
import hashlib
import secrets
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

    internal_order_id = notes.get('internal_order_id')
    payment_id = payment.get('id')

    if internal_order_id:
      order_ref = db.collection('orders').document(internal_order_id)

      transaction = db.transaction()

      @firestore.transactional
      def update_in_transaction(transaction, order_ref):
        snapshot = order_ref.get(transaction=transaction)
        if not snapshot.exists:
          print(f"❌ Order {internal_order_id} not found!")
          return

        current_data = snapshot.to_dict()

        if current_data.get("status") == "PAID":
          print(f"ℹ️ Order {internal_order_id} was already PAID. Skipping update.")
          return

        pickup_code = str(1000 + secrets.randbelow(9000))

        transaction.update(order_ref, {
          "status": "PAID",
          "razorpay_payment_id": payment_id,
          "razorpay_payment_data": payment,
          "pickup_code": pickup_code,
          "updated_at": firestore.SERVER_TIMESTAMP
        })
        print(f"✅ SUCCESS: Generated Pickup Code {pickup_code} for Order {internal_order_id}")

      try:
        update_in_transaction(transaction, order_ref)
      except Exception as e:
        print(f"❌ Transaction failed: {e}")

    else:
      print(f"⚠️ Payment received without internal_order_id: {payment.get('id')}")

  return {"status": "ok"}