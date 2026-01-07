# GreenPlate Backend

Lightweight FastAPI backend for managing college food stalls, menus, and staff. Uses Firebase Authentication + Firestore and supports AI-based menu extraction.

## Quick highlights
- Role-based access: `student`, `staff`, `manager`.
- Staff/manager can manage a single assigned stall; managers can add/remove staff for that stall only.
- Menu scanning: AI (Google Gemini) extracts item name/price from images.

## Quick start
1. Create and activate a virtualenv:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Provide Firebase service account (see `app/firebase_init.py`) via `FIREBASE_SERVICE_ACCOUNT` env var or `serviceAccountKey.json` (not committed).
4. Run:
   ```bash
   python main.py
   ```

## Running with Docker
You can run the app with Docker (image build + run) or with the provided compose file.

- Build and run with Docker:

```bash
# build image (from repo root where Dockerfile is located)
docker build .

# run container (map port 8000). Replace paths/env as needed.
# -v mounts the Firebase service account (if you use a file)
# --env-file points to your local .env containing required env vars
docker run --rm -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/serviceAccountKey.json:/app/serviceAccountKey.json:ro \
  backend
```

- Using Docker Compose (recommended for development with compose file):

```bash
# build and start in background
docker compose up --build

# stop and remove containers
docker compose down --build
```

Notes:
- Ensure your `.env` (not committed) contains the Firebase and GEMINI keys, or pass them via `--env-file` or Docker secrets.
- If you don't use a local `serviceAccountKey.json`, set `FIREBASE_SERVICE_ACCOUNT` (or whichever env var is read in `app/firebase_init.py`) with the JSON string or path as configured.
- The app exposes port 8000 by default. Adjust `-p` or compose ports if needed.

## Auth and headers
- All protected endpoints require a Firebase ID token in the `Authorization` header:
  ```
  Authorization: Bearer {idToken}
  ```
- Do NOT send the Firebase UID in the header — use the ID token issued after login.

## Core endpoints (summary)
- `POST /signup/users` — student signup
- `POST /login/users` — student login (returns `idToken`)
- `POST /auth/verify-staff` — verify staff token and get role/stall
- `POST /staff/menu` — upload menu items (staff only; restricted to their stall)
- `POST /staff/menu/scan-image` — upload image to extract items via AI
- `GET /user/menu` — students view menus for their college
- Manager endpoints: `POST /staff/add-member`, `GET /staff/list`, `DELETE /staff/{staff_uid}`

## Important rules
- Stall-level authorization: staff actions check the authenticated staff's `stall_id` and reject attempts to modify other stalls (HTTP 403).
- Tokens: ID tokens expire; if you receive `{"message": "Authorization header required"}` ensure the header is present and starts with `Bearer ` and the token is valid.
- Image limits: JPEG/PNG, max ~5MB.

## Project layout (relevant files)
- `main.py` — application entry (starts FastAPI)
- `app/app.py` — route mounting and FastAPI app
- `app/auth.py` — authentication helpers and token verification
- `app/firebase_init.py` — Firebase & Firestore initialization
- `app/schema.py` — Pydantic schemas (requests/responses)
- `app/staff.py` — staff & menu operations (upload/scan/manage)
- `app/user.py` — student-facing menu retrieval
- `app/manager.py` — manager/team operations
- `get_token.py` — helper to generate test tokens (dev)
- `compose.yaml`, `Dockerfile`, `README.Docker.md` — container/deployment materials
- `requirements.txt` — Python dependencies

## Notes for contributors
- Read `app/firebase_init.py` to confirm how service account is provided in your environment.
- Use the `/docs` UI (Swagger) at `http://localhost:8000/docs` for quick testing.
- Keep `serviceAccountKey.json` and `.env` out of version control.

## Troubleshooting
- "Authorization header required": ensure header key is exactly `Authorization` and value `Bearer <idToken>`.
- 401 responses usually mean token invalid/expired; re-login to obtain a fresh ID token.
- 403 means your role or stall assignment doesn't allow the action.

## Contact
- See repo `LICENSE` and top-level README for full project information.

Last updated: 2026-01-05
