# app/manager.py

from fastapi.responses import JSONResponse
from starlette import status
from .staff import (
  get_staff_details,
  serialize_firestore_data
)
from firebase_admin import firestore, auth
from .firebase_init import db
from datetime import datetime, time
import calendar

async def get_my_staff(id_token: str):
  try:
    requester_data, _ = await get_staff_details(id_token)
    if not requester_data or requester_data.get("role") != "manager":
      return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": "Access denied."})

    stall_id = requester_data.get("stall_id")

    staff_query = db.collection("staffs").where("stall_id", "==", stall_id).stream()

    staff_list = []
    for doc in staff_query:
      data = doc.to_dict()

      staff_list.append({
        "uid": doc.id,
        "email": data.get("email"),
        "name" : data.get("name"),
        "role": data.get("role"),
        "status": data.get("status","inactive"),
        "added_at": data.get("created_at")
      })

    staff_list = [serialize_firestore_data(s) for s in staff_list]

    return JSONResponse(status_code=status.HTTP_200_OK, content={"staff": staff_list})

  except Exception as e:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})

async def remove_staff_member(target_uid: str, id_token: str):
  try:
    requester_data, _ = await get_staff_details(id_token)
    if not requester_data or requester_data.get("role") != "manager":
      return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": "Access denied."})

    target_ref = db.collection("staffs").document(target_uid)
    target_doc = target_ref.get()

    if not target_doc.exists:
      return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Staff member not found."})

    target_data = target_doc.to_dict()

    if target_data.get("stall_id") != requester_data.get("stall_id"):
      return JSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                          content={"message": "You cannot remove staff from other stalls."})

    if target_data.get("role") == "manager":
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "You cannot remove a Manager."})

    target_ref.delete()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Staff member removed successfully."})

  except Exception as e:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})

async def update_staff_email(target_uid: str, new_email: str, id_token: str):
  try:
    requester_data, _ = await get_staff_details(id_token)
    if not requester_data or requester_data.get("role") != "manager":
      return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": "Access denied."})

    old_ref = db.collection("staffs").document(target_uid)
    old_doc = old_ref.get()

    if not old_doc.exists:
      return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Staff member not found."})

    old_data = old_doc.to_dict()

    if old_data.get("stall_id") != requester_data.get("stall_id"):
      return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": "Unauthorized."})
    if old_data.get("role") == "manager":
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                          content={"message": "Cannot change Manager email here."})

    try:
      user = auth.get_user_by_email(new_email)
      new_uid = user.uid
    except auth.UserNotFoundError:
      user = auth.create_user(email=new_email)
      new_uid = user.uid

    if db.collection("staffs").document(new_uid).get().exists:
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                          content={"message": "New email is already a staff member."})

    batch = db.batch()

    new_ref = db.collection("staffs").document(new_uid)

    new_data = old_data.copy()
    new_data["email"] = new_email
    new_data["updated_by"] = requester_data.get("email")
    new_data["updated_at"] = firestore.SERVER_TIMESTAMP

    batch.set(new_ref, new_data)
    batch.delete(old_ref)

    batch.commit()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": f"Staff email updated to {new_email}."})

  except Exception as e:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})

async def get_stall_performance_overview(month: int, year: int, id_token: str):
  try:
    requester_data, _ = await get_staff_details(id_token)
    if not requester_data or requester_data.get("role") != "manager":
      return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": "Access denied."})

    stall_id = requester_data.get("stall_id")

    month_start = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = datetime(year, month, last_day, 23, 59, 59)

    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    today_end = datetime.combine(now.date(), time.max)

    staff_docs = db.collection("staffs").where("stall_id", "==", stall_id).stream()

    staff_map = {}
    for doc in staff_docs:
      data = doc.to_dict()
      email = data.get("email")
      if email:
        staff_map[email] = {
          "uid": doc.id,
          "name": data.get("name", "Unknown"),
          "email": email,
          "role": data.get("role"),
          "month_total": 0,
          "today_total": 0,
          "last_active": None
        }

    orders_query = (
      db.collection("orders")
      .where("stall_id", "==", stall_id)
      .where("status", "==", "CLAIMED")
      .where("picked_up_at", ">=", month_start)
      .where("picked_up_at", "<=", month_end)
      .select(["handled_by", "picked_up_at"])
    )

    order_docs = orders_query.stream()

    for doc in order_docs:
      data = doc.to_dict()
      handler_email = data.get("handled_by")
      pickup_time = data.get("picked_up_at")

      if handler_email in staff_map and pickup_time:
        staff_map[handler_email]["month_total"] += 1

        if today_start.timestamp() <= pickup_time.timestamp() <= today_end.timestamp():
          staff_map[handler_email]["today_total"] += 1

        current_last = staff_map[handler_email]["last_active"]
        if current_last is None or pickup_time.timestamp() > current_last.timestamp():
          staff_map[handler_email]["last_active"] = pickup_time

    results = list(staff_map.values())

    results.sort(key=lambda x: x["month_total"], reverse=True)

    for staff in results:
      if staff["last_active"] is not None:
        staff["last_active"] = staff["last_active"].isoformat()

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "stall_id": stall_id,
        "period": f"{month}-{year}",
        "staff_stats": results
      }
    )

  except Exception as e:
    return JSONResponse(status_code=500, content={"message": str(e)})
