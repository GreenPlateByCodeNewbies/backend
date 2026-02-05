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
    if not secret:
      raise Exception("RAZORPAY_WEBHOOK_SECRET not set")

    expected_signature = hmac.new(
      key=secret.encode(),
      msg=body,
      digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
      raise HTTPException(status_code=400, detail="Invalid signature")
  except Exception as e:
    print(f"Webhook Signature Error: {e}")
    raise HTTPException(status_code=400, detail="Signature verification failed")

  payload = await request.json()
  event_type = payload.get('event')

  if event_type in ['payment.captured', 'payment_link.paid']:
    payment = payload['payload']['payment']['entity']
    notes = payment.get('notes', {})

    internal_order_id = notes.get('internal_order_id')
    payment_id = payment.get('id')

    is_resale = notes.get('type') == 'RESALE'
    resale_item_id = notes.get('resale_item_id')

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

        if is_resale and resale_item_id:
          resale_ref = db.collection("resale_items").document(resale_item_id)
          transaction.update(resale_ref, {
            "status": "SOLD",
            "sold_to_order_id": internal_order_id,
            "sold_at": firestore.SERVER_TIMESTAMP
          })
          print(f"✅ SUCCESS: Marked Resale Item {resale_item_id} as SOLD")

      try:
        update_in_transaction(transaction, order_ref)
      except Exception as e:
        print(f"❌ Transaction failed: {e}")

    else:
      print(f"⚠️ Payment received without internal_order_id: {payment.get('id')}")

  elif event_type == 'refund.processed':
    try:
      refund_entity = payload['payload']['refund']['entity']
      payment_id = refund_entity.get('payment_id')

      notes = refund_entity.get('notes', {})
      order_id = notes.get('order_id')

      if order_id:
        order_ref = db.collection('orders').document(order_id)

        snapshot = order_ref.get()
        if snapshot.exists:
          if snapshot.to_dict().get("refund", {}).get("status") == "COMPLETED":
            print("ℹ️ Refund already completed, skipping")
            return

        order_ref.update({
          "refund.status": "COMPLETED",
          "refund.processed_at": firestore.SERVER_TIMESTAMP,
          "refund.razorpay_refund_id": refund_entity.get('id'),
          "refund.bank_ref": refund_entity.get('acquirer_data', {}).get('rrn'),
          "updated_at": firestore.SERVER_TIMESTAMP
        })
        print(f"✅ REFUND COMPLETE: Order {order_id} refunded successfully.")
      else:
        print(f"⚠️ Refund processed but no order_id found in notes. Payment ID: {payment_id}")

    except Exception as e:
      print(f"❌ Error processing refund webhook: {e}")

  elif event_type == 'refund.failed':
    try:
      refund_entity = payload['payload']['refund']['entity']
      notes = refund_entity.get('notes', {})
      order_id = notes.get('order_id')

      if order_id:
        db.collection('orders').document(order_id).update({
          "refund.status": "FAILED",
          "refund.failure_reason": refund_entity.get('status_details', {}).get('description', 'Unknown Error'),
          "updated_at": firestore.SERVER_TIMESTAMP
        })
        print(f"❌ REFUND FAILED: Order {order_id}")
    except Exception as e:
      print(f"❌ Error handling refund failure: {e}")

  return {"status": "ok"}
