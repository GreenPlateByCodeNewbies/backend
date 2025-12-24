# app/staff.py

from .schema import MenuSchema
from fastapi.responses import JSONResponse
from starlette import status
from .firebase_init import db
from firebase_admin import auth, firestore
from datetime import datetime


async def get_staff_details(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]

        staff_doc = db.collection("staffs").document(uid).get()
        if staff_doc.exists:
            return staff_doc.to_dict(), uid

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
        # Firestore timestamps & Python datetimes
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data

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

        # 🔥 NEW: Store menu items in subcollection
        menu_items_ref = stall_ref.collection("menu_items")

        batch = db.batch()

        for item in menu_data.items:
            item_ref = menu_items_ref.document()  # auto-generated item_id
            batch.set(item_ref, {
                **item.model_dump(),
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP
            })

        # Update stall metadata (lightweight)
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
