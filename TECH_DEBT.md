# Technical Debt & v2 Ideas

- Move auth logic to service layer
- Add role-based dependency guards
- Cache Firebase token verification
- Version APIs (/v1, /v2)
- Add structured logging
- Add async-safe Firebase calls
- Add more tests (unit, integration)
- Improve error handling (custom exceptions, error codes)
- Add rate limiting

# Future Folder Structure

```
app/
├── v1/
│   ├── app.py
│   ├── auth.py
│   ├── user.py
│   ├── staff.py
│   ├── manager.py
│   ├── webhook.py
│   └── schema.py
│
├── v2/
│   ├── api/
│   │   ├── user.py
│   │   ├── staff.py
│   │   └── manager.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── staff_service.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── firebase.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   └── auth.py
│   │
│   └── main.py
```


