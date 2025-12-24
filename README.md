# GreenPlate Backend

A FastAPI-based backend application for managing college food stalls, menus, and student dining experiences. The application uses Firebase for authentication and Firestore for data storage, with AI-powered menu image scanning.

## 📋 Overview

GreenPlate is a comprehensive platform that connects students with food stalls in their college. The backend provides:
- **Authentication system** for students and staff
- **Menu management** for stall staff
- **AI-powered menu scanning** using Google's Gemini API
- **Menu browsing** for students
- **Multi-college support** with domain-based college assignment
- **Stall-based authorization** ensuring staff can only manage their own stall

## 🚀 Features

### For Staff
- User registration and login with email/password
- Upload menus with food items, prices, and descriptions
- Scan menu images using AI (automatic item extraction)
- Update existing menu items
- Delete menu items
- View their stall's complete menu
- Stall-based access control (staff can only manage assigned stall)

### For Students
- User registration and login with college domain verification
- View menus from all active stalls in their college
- Browse available food items with prices and descriptions
- Filter menu items by availability

### General
- Firebase authentication and authorization
- Email-based college registration (domain-based)
- Firestore database for scalability
- Error handling and validation
- JSON-based API responses

## 🏗️ Project Structure

```
app/
├── __init__.py              # Package initialization
├── app.py                   # FastAPI application and route definitions
├── auth.py                  # Authentication and authorization logic
├── config.py                # Firebase and application configuration
├── firebase_init.py         # Firebase initialization
├── schema.py                # Pydantic schemas for request/response validation
├── staff.py                 # Staff-related operations (menu management)
└── user.py                  # Student-related operations (menu browsing)

main.py                       # Application entry point
requirements.txt              # Python dependencies
serviceAccountKey.json        # Firebase service account credentials
```

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- Firebase Project with Authentication and Firestore enabled
- Google Gemini API key
- Pyrebase4 and Firebase Admin SDK setup

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd GreenPlate/backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory with:
   ```
   FIREBASE_API_KEY=<your-api-key>
   FIREBASE_AUTH_DOMAIN=<your-auth-domain>
   FIREBASE_DATABASE_URL=<your-database-url>
   FIREBASE_PROJECT_ID=<your-project-id>
   FIREBASE_STORAGE_BUCKET=<your-storage-bucket>
   FIREBASE_MESSAGING_SENDER_ID=<your-messaging-sender-id>
   FIREBASE_APP_ID=<your-app-id>
   FIREBASE_MEASUREMENT_ID=<your-measurement-id>
   GEMINI_API_KEY=<your-gemini-api-key>
   ```

5. **Add Firebase service account key**
   - Download `serviceAccountKey.json` from Firebase Console
   - Place it in the root directory (same level as `main.py`)

6. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Authentication Endpoints

#### Student Signup
- **POST** `/signup/users`
- **Body:**
  ```json
  {
    "email": "student@college.edu.in",
    "password": "password123",
    "confirm_password": "password123"
  }
  ```
- **Response:** User UID and success message
- **Note:** Email domain must be registered in Firebase Firestore colleges collection

#### Student Login
- **POST** `/login/users`
- **Body:**
  ```json
  {
    "email": "student@college.edu.in",
    "password": "password123"
  }
  ```
- **Response:** ID token for authentication

#### Staff Signup
- **POST** `/signup/staffs`
- **Body:**
  ```json
  {
    "email": "staff@college.edu.in",
    "password": "password123",
    "confirm_password": "password123",
    "stall_id": "stall-001"
  }
  ```
- **Response:** Staff UID and success message
- **Note:** stall_id must exist in the college's stalls collection

#### Staff Login
- **POST** `/login/staffs`
- **Body:**
  ```json
  {
    "email": "staff@college.edu.in",
    "password": "password123"
  }
  ```
- **Response:** ID token for authentication

### Menu Management Endpoints (Staff)

#### Upload Menu
- **POST** `/staff/menu`
- **Headers:** `Authorization: Bearer {idToken}`
- **Body:**
  ```json
  {
    "stall_id": "stall-001",
    "items": [
      {
        "name": "Veg Roll",
        "price": 25.0,
        "description": "Vegetable filled roll",
        "is_available": true
      }
    ]
  }
  ```
- **Response:** Menu upload success with item count

#### Get Menu
- **GET** `/staff/menu`
- **Headers:** `Authorization: Bearer {idToken}`
- **Response:** List of menu items for the staff's stall

#### Scan Menu Image
- **POST** `/staff/menu/scan-image`
- **Headers:** `Authorization: Bearer {idToken}`
- **Body:** Form data with image file (JPEG or PNG, max 5MB)
- **Response:** Detected menu items with AI-extracted names, prices, and descriptions

#### Update Menu Item
- **PATCH** `/staff/menu/{item_id}`
- **Headers:** `Authorization: Bearer {idToken}`
- **Body:**
  ```json
  {
    "name": "Updated Item Name",
    "price": 30.0,
    "description": "Updated description",
    "is_available": false
  }
  ```
- **Response:** Update success message

#### Delete Menu Item
- **DELETE** `/staff/menu/{item_id}`
- **Headers:** `Authorization: Bearer {idToken}`
- **Response:** Deletion success message

### Menu Browsing Endpoints (Student)

#### Get College Menus
- **GET** `/user/menu`
- **Headers:** `Authorization: Bearer {idToken}`
- **Response:** List of all active stalls with their available menu items

## 🔐 Authentication & Authorization

### Token Usage
- All protected endpoints require an **ID Token** in the `Authorization` header
- Format: `Authorization: Bearer {idToken}`
- ID Token is obtained after successful login

### Authorization Logic
- **Students** can only view menus from their college
- **Staff** can only manage menus for their assigned stall
- Staff cannot upload or modify menus for other stalls
- Authentication errors return 401 Unauthorized
- Authorization errors return 403 Forbidden

## 🗄️ Database Schema

### Firestore Collections

#### `colleges`
```
college_id/
├── name: string
├── domains: array[string] (email domains for registration)
└── stalls/ (subcollection)
    └── stall_id/
        ├── name: string
        ├── status: "active" | "inactive"
        ├── isVerified: boolean
        ├── last_updated_by: string (staff uid)
        ├── last_updated_at: timestamp
        └── menu_items/ (subcollection)
            └── item_id/
                ├── name: string
                ├── price: number
                ├── description: string
                ├── is_available: boolean
                ├── created_at: timestamp
                └── updated_at: timestamp
```

#### `users`
```
user_id/
├── email: string
├── college_id: string
├── college_name: string
├── role: "student"
└── created_at: timestamp
```

#### `staffs`
```
staff_id/
├── email: string
├── stall_id: string
├── college_id: string
├── role: "staff"
└── created_at: timestamp
```

## 🤖 AI Menu Scanning

The application uses **Google Gemini 2.5 Flash** to extract menu items from images:
- Supports JPEG and PNG images
- Maximum file size: 5MB
- Extracts: food item names, prices, and generates short descriptions
- Returns structured JSON data ready for verification before saving

### Example AI Response
```json
{
  "detected_items": [
    {
      "name": "Chicken Roll",
      "price": 45.0,
      "description": "Spiced chicken wrapped in soft roll"
    }
  ],
  "count": 1,
  "message": "Scan complete. Please verify items before saving."
}
```

## 📦 Dependencies

### Key Libraries
- **FastAPI** (0.127.0) - Modern web framework
- **Firebase Admin SDK** (7.1.0) - Server-side Firebase integration
- **Pyrebase4** (4.8.1) - Client-side Firebase library
- **Pydantic** (2.12.5) - Data validation
- **Google Generative AI** (0.8.6) - Gemini API integration
- **Python-dotenv** (1.2.1) - Environment variable management
- **Uvicorn** - ASGI server

See `requirements.txt` for complete dependency list.

## 🚨 Error Handling

The API returns appropriate HTTP status codes:
- **200** - Successful GET request
- **201** - Successful POST/resource creation
- **400** - Bad request (validation error)
- **401** - Unauthorized (invalid/missing token)
- **403** - Forbidden (insufficient permissions)
- **404** - Not found
- **413** - File too large
- **422** - Unprocessable entity
- **500** - Internal server error

All error responses follow a consistent JSON format:
```json
{
  "message": "Error description"
}
```

## 🔄 Running the Application

### Development Mode
```bash
python main.py
```
The server starts with auto-reload enabled on `http://localhost:8000`

### Access API Documentation
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## 📝 Code Organization

### auth.py
Handles user and staff authentication:
- Password validation
- College domain verification
- Firebase user creation
- Login and token generation
- Separated helper functions for code clarity

### staff.py
Manages all staff-related operations:
- Menu upload with batch operations
- Menu item updates and deletions
- Image scanning with AI integration
- Staff authorization checks
- Firestore transactions

### user.py
Handles student operations:
- Retrieve menus for college
- Filter active stalls and available items
- Authorization based on college assignment

### schema.py
Pydantic models for request/response validation:
- SignUpSchema
- LoginSchema
- MenuSchema
- MenuItemSchema
- UpdateMenuItemSchema
- MenuScanResponse

## 🔒 Security Considerations

1. **Firebase Authentication** - Secure password hashing and token-based auth
2. **ID Token Verification** - All protected endpoints verify tokens
3. **Authorization Checks** - Stall-level access control
4. **Input Validation** - Pydantic schemas validate all inputs
5. **File Upload Validation** - Size and type restrictions on menu images
6. **Environment Variables** - Sensitive credentials stored in `.env`

## 🛠️ Development Tips

1. Use `/docs` endpoint during development for API testing
2. Check Firebase Console for real-time database updates
3. Monitor Gemini API usage for cost optimization
4. Implement rate limiting for production
5. Add request logging for debugging

## 📞 Support & Contribution

For issues, questions, or contributions, please refer to the main GreenPlate repository.

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

