# GreenPlate — Backend (FastAPI)

A compact FastAPI backend for managing college food stalls, staff, menus and orders.

### Quick summary
- **Auth:** Firebase ID tokens (verify with firebase_admin).
- **Data:** Firestore collections (colleges, stalls, staffs, users, menu_items, orders).
- **Analytics:** Staff performance tracking (monthly/daily logs) and manager dashboard.
- **AI menu extraction:** optional (Google Gemini) — returns JSON list of items.
- **Payments:** Razorpay integration for orders + webhook validation.
- **Docker ready:** `Dockerfile` + `compose.yaml` included.

### Quick start (local)
1. Create & activate a virtualenv:

```bash
python -m venv .venv && source .venv/bin/activate
```

2. Install deps:

```bash
pip install -r requirements.txt
```

3. Provide Firebase & other secrets (recommended via `.env` or env vars). Important vars listed below.

4. Run the app:

```bash
python main.py
# or
uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
```

### Quick start (Docker)
- Build and run container (simple):

```bash
docker build -t greenplate-backend .
docker run --rm -p 8000:8000 --env-file .env -v $(pwd)/secrets:/app/secrets:ro greenplate-backend
```

- With Compose (repo root, uses `compose.yaml`):

```bash
# build & run in background
docker compose -f compose.yaml --env-file .env up --build -d
# stop & remove
docker compose -f compose.yaml down
```

### Authentication
- Use Firebase ID token (NOT the UID). Send in Authorization header as a Bearer token:

```
Authorization: Bearer <idToken>
```

- Obtain a test idToken via the helper `get_token.py` (dev-only).

### Key environment variables
- FIREBASE_SERVICE_ACCOUNT: required — service account JSON content (or path) used by firebase_admin. For CI you can set `CI=true` to skip strict local validation.
- FIREBASE_API_KEY, FIREBASE_PROJECT_ID, etc. — used by helper scripts.
- GEMINI_API_KEY — optional, required for image-based menu scanning (Gemini model: gemini-2.5-flash).
- RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET — required for creating Razorpay orders.
- RAZORPAY_WEBHOOK_SECRET — required for validating Razorpay webhook signatures (header `X-Razorpay-Signature`).

### Important files
- `app/firebase_init.py` — initializes firebase_admin and exposes `db` (Firestore client).
- `app/auth.py` — verifies tokens and initializes manager records when a manager signs in using the stall email.
- `app/schema.py` — Pydantic models (MenuSchema, MenuItemSchema, MenuScanResponse, CreateOrderSchema, etc.).
- `app/staff.py` — staff routes logic: upload/get/update/delete menus, add staff, image scan (uses Gemini if configured).
- `app/manager.py` — manager-only helpers: list staff, remove staff, update staff email.
- `app/user.py` — student-facing: list menus and create payment orders.
- `app/webhook.py` — Razorpay webhook: validates HMAC signature and updates `orders` documents with `razorpay_payment_id`, `razorpay_payment_data`, `status: 'PAID'`, and a generated `pickup_code`.
- `get_token.py` — helper to exchange email/password for idToken (dev/test only).

### Core rules / behavior (short)
- Staff authorization: tokens are verified and mapped to a `staffs` document. Only staff with `status == 'active'` are allowed to use staff routes.
- Stall ownership: a staff can only manage the stall they belong to (stall_id is enforced on menu writes/updates).
- Manager init: when a user signs in and their email matches a stall's registered email, a manager `staffs` document is auto-created.
- `POST /staff/add-member` returns a `reset_link` (Firebase password reset) to onboard newly created staff users.

### Menu upload & scan
- Menu upload expects JSON matching `MenuSchema` (see `app/schema.py`): `stall_id` must match authenticated staff's stall; `items` cannot be empty; `price` must be > 0.
- Image scan (`POST /staff/menu/scan-image`) accepts JPEG/PNG only and max file size 5MB; uses Gemini (`gemini-2.5-flash`) to extract items and returns a `MenuScanResponse` that must be reviewed before saving.

### API (selected endpoints)
- `GET /health` — health check

### Auth
- `POST /auth/verify-staff` — Verify staff token; initializes manager if needed.
- `POST /auth/verify-student` — Verify student token and auto-register student (by college domain).

### User (student)
- `GET /user/menu` — List menus for the student's college (only active & verified stalls returned).
- `POST /user/order/create` — Create a Razorpay order (payload: CreateOrderSchema)
- `POST /user/order/verify` — Client-side payment verification endpoint (accepts razorpay_order_id, razorpay_payment_id, razorpay_signature and internal_order_id); verifies signature and marks the internal order PAID with a pickup code.
- `PATCH /user/profile` — Update student profile (name, roll_number, phone).
- `GET /user/orders` — List student's orders (shows pickup code for PAID/READY orders).

### Staff / Manager
- `PATCH /staff/profile` — Update authenticated staff's profile (name, phone).
- `POST /staff/add-member` — Manager adds a staff (payload: {email}) and receives a `reset_link`.
- `GET /staff/list` — Manager: list staff for manager's stall
- `DELETE /staff/{staff_uid}` — Manager: remove a staff member (must be same stall)
- `PUT /staff/{staff_uid}/email` — Manager: change a staff's email (creates user if needed)

### Staff menu management
- `POST /staff/menu` — Upload menu JSON for the authenticated staff's stall (MenuSchema)
- `GET /staff/menu` — Get menu for authenticated staff's stall
- `POST /staff/menu/scan-image` — Upload image (JPEG/PNG, <5MB) → returns MenuScanResponse (requires GEMINI_API_KEY)
- `PATCH /staff/menu/{item_id}` — Update a menu item
- `DELETE /staff/menu/{item_id}` — Delete a menu item

### Staff order management
- `GET /staff/orders?status=PAID` — List stall orders by status (default PAID)
- `PATCH /staff/orders/{order_id}/status` — Update an order status (only for orders belonging to the staff's stall)
- `POST /staff/orders/verify-pickup` — Verify 4-digit pickup code and mark order CLAIMED

### Analytics & Performance
- `GET /staff/performance/overview?month=X&year=Y` — Manager: Get monthly leaderboard/stats for all staff.

### Webhook
- `POST /webhook/razorpay` — Razorpay will POST payment events here; the endpoint verifies `X-Razorpay-Signature` using `RAZORPAY_WEBHOOK_SECRET` and updates the related `orders/{internal_order_id}` with `razorpay_payment_id`, `razorpay_payment_data`, `status: 'PAID'`, and a generated `pickup_code`. Configure Razorpay webhook to include `notes.internal_order_id` when creating payments.

### Testing & troubleshooting
- Swagger UI: http://localhost:8000/docs — use the Authorize button and paste the idToken (Bearer token).
- If you see {"message":"Authorization header required"} or 401: ensure header name is exactly `Authorization` and value starts with `Bearer ` followed by the idToken.
- If token expired or invalid: re-login to get a fresh idToken.

### Security notes
- Do NOT commit secrets. The repo includes a `secrets/` folder in .gitignore — keep service account JSON and .env out of VCS.
- The server uses Firestore security via server-side checks: stall_id and college_id are validated in code before writes.

### Where to look next (dev pointers)
- To change menu schema, edit `app/schema.py` (Pydantic models used for validation).
- To modify staff authorization behavior, check `app/auth.py` and `app/staff.py:get_staff_details`.
- GEMINI integration is in `app/staff.py` (_extract_menu_from_image) and requires `GEMINI_API_KEY`.

### Short checklist for running locally
1. Populate `.env` (or export env vars). Ensure FIREBASE_SERVICE_ACCOUNT is set.
2. pip install -r requirements.txt
3. uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
4. Use Swagger or a REST client. Authorize with `Authorization: Bearer <idToken>`.

# capacitor setup in backend
        "http://localhost",
        "capacitor://localhost",
        "http://10.0.2.2:3000",
        "http://10.0.2.2:5000",
        "http://10.0.2.2:8000",

        to your app/app.py


### License
- See LICENSE in repo root.

Last updated: 2026-01-20
