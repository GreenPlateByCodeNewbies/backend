# GreenPlate Backend

A FastAPI-based backend application for managing college food stalls, menus, and student dining experiences. The application uses Firebase for authentication and Firestore for data storage, with AI-powered menu image scanning using Google's Gemini API.

## 📋 Overview

GreenPlate is a comprehensive platform that connects students with food stalls in their college. The backend provides:
- **Dual-role authentication system** for students and staff with role-based access control
- **Menu management** for stall managers and staff with item upload, update, and deletion
- **AI-powered menu scanning** using Google's Gemini 2.5 Flash for automatic menu extraction from images
- **Menu browsing** for students with college-specific filtering
- **Multi-college support** with domain-based college assignment
- **Stall-based authorization** ensuring staff can only manage their assigned stall
- **Manager functionality** for staff management and team organization

## 🚀 Features

### For Students
- **User registration and login** with email/password and automatic college domain verification
- **View menus** from all active and verified stalls in their college
- **Browse available items** with prices and descriptions
- **Filter menu items** by availability status
- **College-based isolation** - students only see stalls from their registered college

### For Staff
- **User registration and login** with stall assignment
- **Upload menus** with multiple food items, prices, and descriptions in batch
- **Scan menu images** using AI to automatically extract food names and prices
- **Update menu items** partially or completely
- **Delete menu items** from their stall
- **View stall menu** with complete item details and timestamps
- **Stall-based access control** - staff can only manage their assigned stall

### For Managers
- **Add staff members** to their stall team
- **View all staff** members in their stall
- **Remove staff members** (except themselves if they're the manager)
- **Update staff emails** and reassign team members
- **Full team management** capabilities

### Technical Features
- **Firebase authentication** with secure password hashing and token-based access
- **Firestore database** for scalable and real-time data management
- **Email domain-based college verification** - only registered domains allowed
- **Batch operations** for efficient database transactions
- **Image processing validation** - JPEG and PNG support with 5MB size limit
- **Comprehensive error handling** with meaningful HTTP status codes
- **Firestore timestamp tracking** for all records (created_at, updated_at)

## 🏗️ Project Structure

```
GreenPlate/backend/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── app.py                   # FastAPI application and route definitions
│   ├── auth.py                  # Authentication logic (signup, login, staff verification)
│   ├── config.py                # Firebase and application configuration
│   ├── firebase_init.py         # Firebase SDK initialization
│   ├── schema.py                # Pydantic schemas for request/response validation
│   ├── staff.py                 # Staff operations (menu management, AI scanning)
│   ├── user.py                  # Student operations (menu browsing)
│   ├── manager.py               # Manager operations (team management)
│   └── __pycache__/             # Compiled Python files
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── get_token.py                 # Token generation utility for testing
├── README.md                    # Project documentation
└── LICENSE                      # Project license
```

### Key File Responsibilities

- **app.py**: Defines all API routes and endpoint structure using FastAPI
- **auth.py**: Handles user/staff signup, login, college domain verification, and staff verification logic
- **staff.py**: Manages menu operations (upload, scan, update, delete) and AI menu extraction from images
- **user.py**: Retrieves filtered menus for students based on their college and stall status
- **manager.py**: Handles staff management operations (add, remove, update emails)
- **schema.py**: Pydantic models for data validation and automatic API documentation

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- Firebase Project with Authentication and Firestore enabled
- Google Gemini API key
- pip or conda for package management

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
   Create a `.env` file in the root directory with the following variables:
   ```
   FIREBASE_API_KEY=<your-firebase-api-key>
   FIREBASE_AUTH_DOMAIN=<your-firebase-auth-domain>
   FIREBASE_DATABASE_URL=<your-firebase-database-url>
   FIREBASE_PROJECT_ID=<your-firebase-project-id>
   FIREBASE_STORAGE_BUCKET=<your-firebase-storage-bucket>
   FIREBASE_MESSAGING_SENDER_ID=<your-messaging-sender-id>
   FIREBASE_APP_ID=<your-firebase-app-id>
   FIREBASE_MEASUREMENT_ID=<your-measurement-id>
   GEMINI_API_KEY=<your-google-gemini-api-key>
   ```

5. **Add Firebase service account key**
   - Download `serviceAccountKey.json` from Firebase Console (Project Settings → Service Accounts)
   - Place it in the root directory (same level as `main.py`)

6. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000` with auto-reload enabled.

## 📚 API Endpoints

### Authentication Endpoints

#### Student Signup
- **POST** `/signup/users`
- **Tags:** user
- **Request Body:**
  ```json
  {
    "email": "student@college.edu.in",
    "password": "password123",
    "confirm_password": "password123"
  }
  ```
- **Success Response (201):**
  ```json
  {
    "message": "User created successfully",
    "uid": "user-uid-here"
  }
  ```
- **Error Response (400):**
  ```json
  {
    "message": "Your college domain is not registered with GreenPlate."
  }
  ```
- **Notes:**
  - Email domain must be registered in Firebase Firestore under colleges collection
  - Passwords must match
  - Creates a document in `users` collection with student role

#### Student Login
- **POST** `/login/users`
- **Tags:** user
- **Request Body:**
  ```json
  {
    "email": "student@college.edu.in",
    "password": "password123"
  }
  ```
- **Success Response (200):**
  ```json
  {
    "message": "Login successful",
    "idToken": "firebase-id-token-here"
  }
  ```
- **Returns:** Firebase ID token for authorization in protected endpoints

### Staff Verification Endpoint

#### Verify Staff Access
- **POST** `/auth/verify-staff`
- **Tags:** verify
- **Headers:** `Authorization: Bearer {idToken}`
- **Success Response (200):**
  ```json
  {
    "message": "Verified",
    "role": "manager",
    "stall_id": "stall-001",
    "college_id": "college-id-here"
  }
  ```
- **Purpose:** Verifies that the ID token belongs to a staff member and initializes manager account if applicable

### Menu Management Endpoints (Staff)

#### Upload Menu
- **POST** `/staff/menu`
- **Tags:** staff, manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Request Body:**
  ```json
  {
    "stall_id": "stall-001",
    "items": [
      {
        "name": "Veg Roll",
        "price": 25.0,
        "description": "Vegetable filled roll",
        "is_available": true
      },
      {
        "name": "Chicken Roll",
        "price": 40.0,
        "description": "Spiced chicken wrapped in soft roll",
        "is_available": true
      }
    ]
  }
  ```
- **Success Response (201):**
  ```json
  {
    "message": "Menu uploaded successfully",
    "stall_id": "stall-001",
    "items_added": 2
  }
  ```
- **Authorization Logic:** Staff can only upload for their assigned stall
- **Database Operation:** Uses batch write for efficiency

#### Get Menu
- **GET** `/staff/menu`
- **Tags:** staff, manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Success Response (200):**
  ```json
  {
    "stall_id": "stall-001",
    "menu_items": [
      {
        "item_id": "item-001",
        "name": "Veg Roll",
        "price": 25.0,
        "description": "Vegetable filled roll",
        "is_available": true,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00"
      }
    ]
  }
  ```
- **Retrieves:** All menu items for the staff member's assigned stall

#### Scan Menu Image
- **POST** `/staff/menu/scan-image`
- **Tags:** staff, manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Content-Type:** multipart/form-data
- **Parameters:** `file` (JPEG or PNG, max 5MB)
- **Success Response (200):**
  ```json
  {
    "message": "Scan complete. Please verify items.",
    "detected_items": [
      {
        "name": "Chicken Roll",
        "price": 45.0,
        "description": "Spiced chicken wrapped soft roll"
      },
      {
        "name": "Veg Momo",
        "price": 35.0,
        "description": "Steamed dumplings with vegetable filling"
      }
    ],
    "count": 2
  }
  ```
- **Uses:** Google Gemini 2.5 Flash for AI extraction
- **Features:** Automatically extracts names, prices, and generates descriptions
- **Error Cases:**
  - 400: Invalid file type
  - 413: File larger than 5MB
  - 422: Could not extract items from image

#### Update Menu Item
- **PATCH** `/staff/menu/{item_id}`
- **Tags:** staff, manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Request Body (all fields optional):**
  ```json
  {
    "name": "Updated Item Name",
    "price": 30.0,
    "description": "Updated description",
    "is_available": false
  }
  ```
- **Success Response (200):**
  ```json
  {
    "message": "Menu item updated successfully",
    "item_id": "item-001"
  }
  ```
- **Notes:** Only provided fields are updated, timestamp automatically set

#### Delete Menu Item
- **DELETE** `/staff/menu/{item_id}`
- **Tags:** staff, manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Success Response (200):**
  ```json
  {
    "message": "Menu item deleted successfully",
    "item_id": "item-001"
  }
  ```

### Menu Browsing Endpoints (Student)

#### Get College Menus
- **GET** `/user/menu`
- **Tags:** user
- **Headers:** `Authorization: Bearer {idToken}`
- **Success Response (200):**
  ```json
  {
    "college_id": "college-001",
    "stalls": [
      {
        "stall_id": "stall-001",
        "stall_name": "Food Court A",
        "menu_items": [
          {
            "item_id": "item-001",
            "name": "Veg Roll",
            "price": 25.0,
            "description": "Vegetable filled roll",
            "is_available": true
          }
        ]
      }
    ]
  }
  ```
- **Filtering Logic:**
  - Only shows stalls with `status: "active"` and `isVerified: true`
  - Only shows items with `is_available: true`
  - Scoped to student's college only

### Manager Staff Management Endpoints

#### Add Staff Member
- **POST** `/staff/add-member`
- **Tags:** manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Request Body:**
  ```json
  {
    "email": "new_staff@college.edu.in"
  }
  ```
- **Success Response (201):**
  ```json
  {
    "message": "Staff new_staff@college.edu.in added successfully."
  }
  ```
- **Authorization:** Only managers can add staff
- **Logic:** Creates user account if doesn't exist, adds to same stall as manager

#### Get Staff List
- **GET** `/staff/list`
- **Tags:** manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Success Response (200):**
  ```json
  {
    "staff": [
      {
        "uid": "staff-uid-123",
        "email": "staff@college.edu.in",
        "role": "staff",
        "added_at": "2024-01-15T10:30:00"
      }
    ]
  }
  ```
- **Excludes:** Manager's own account

#### Remove Staff Member
- **DELETE** `/staff/{staff_uid}`
- **Tags:** manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Success Response (200):**
  ```json
  {
    "message": "Staff member removed successfully."
  }
  ```
- **Restrictions:**
  - Cannot remove from other stalls
  - Cannot remove another manager

#### Update Staff Email
- **PUT** `/staff/{staff_uid}/email`
- **Tags:** manager
- **Headers:** `Authorization: Bearer {idToken}`
- **Request Body:**
  ```json
  {
    "new_email": "updated_email@college.edu.in"
  }
  ```
- **Success Response (200):**
  ```json
  {
    "message": "Staff email updated to updated_email@college.edu.in."
  }
  ```
- **Uses:** Batch operations to ensure atomicity

## 🔐 Authentication & Authorization

### Token Usage
- All protected endpoints require an **ID Token** in the `Authorization` header
- Format: `Authorization: Bearer {idToken}`
- ID Token is obtained after successful login via `/login/users` or `/login/staffs`
- Tokens are issued by Firebase Authentication

### Authorization Levels

**Student Role:**
- Can view their college's stall menus
- Cannot create, update, or delete menu items
- Cannot access staff management endpoints

**Staff Role:**
- Can manage menu items for their assigned stall only
- Cannot access other stalls' menus
- Cannot add or remove staff members

**Manager Role:**
- Can perform all staff actions plus manage team
- Can add, remove, and update staff emails
- Can only manage staff in their own stall
- Cannot be removed by other managers

### Error Responses
- **401 Unauthorized:** Invalid, expired, or missing token
- **403 Forbidden:** Valid token but insufficient permissions
- **404 Not Found:** Resource doesn't exist
- **400 Bad Request:** Invalid input data
- **422 Unprocessable Entity:** Cannot process request (e.g., invalid menu image)

## 🗄️ Database Schema

### Firestore Collections Structure

#### `colleges` Collection
```
colleges/
└── college_id/
    ├── name: string
    ├── domains: array[string]        (email domains for registration)
    ├── created_at: timestamp
    └── stalls/                        (subcollection)
        └── stall_id/
            ├── name: string
            ├── status: "active" | "inactive"
            ├── isVerified: boolean
            ├── email: string          (manager/owner email)
            ├── last_updated_by: string
            ├── last_updated_at: timestamp
            └── menu_items/            (subcollection)
                └── item_id/
                    ├── name: string
                    ├── price: number
                    ├── description: string
                    ├── is_available: boolean
                    ├── created_at: timestamp
                    └── updated_at: timestamp
```

#### `users` Collection (Students)
```
users/
└── user_id/
    ├── email: string
    ├── college_id: string
    ├── college_name: string
    ├── role: "student"
    └── created_at: timestamp
```

#### `staffs` Collection (Staff and Managers)
```
staffs/
└── staff_id/
    ├── email: string
    ├── stall_id: string
    ├── college_id: string
    ├── role: "staff" | "manager"
    ├── added_by: string               (email of who added them)
    ├── updated_by: string             (optional)
    ├── created_at: timestamp
    └── updated_at: timestamp           (optional)
```

### Data Relationships
- Students are college members (many students per college)
- Staff are stall members (many staff per stall)
- Stalls belong to colleges (many stalls per college)
- Menu items belong to stalls (many items per stall)
- One manager per stall (can have multiple staff)

## 🤖 AI Menu Scanning

The application uses **Google Gemini 2.5 Flash** for intelligent menu image processing:

### Features
- **Automatic extraction** of food names and prices from menu images
- **Price format handling** - supports formats like "₹25/-", "25.00", "25", etc.
- **AI-generated descriptions** - creates concise, accurate descriptions (6-7 words)
- **Image validation** - supports JPEG and PNG, max 5MB file size

### Extraction Process
1. Staff uploads a menu image
2. Gemini AI analyzes the image
3. System extracts item names and prices
4. AI generates short descriptions
5. Results returned for staff verification before saving

### AI Response Validation
- Items must have valid names (string, non-empty)
- Prices can be null if unclear
- Descriptions are auto-generated from item names
- Invalid items are filtered out
- Descriptions capped at 6-7 words to ensure consistency

### Example Workflow
```
Input: Menu image with items and prices
↓
AI Processing: Gemini 2.5 Flash extracts details
↓
Output:
[
  {
    "name": "Chicken Roll",
    "price": 45,
    "description": "Spiced chicken wrapped in soft roll"
  }
]
↓
Staff Review: Verify extracted items are correct
↓
Save or Re-upload: Confirm and add to menu or modify and retry
```

## 📦 Dependencies

### Core Framework
- **FastAPI** (0.127.0) - Modern async Python web framework
- **Uvicorn** - ASGI server for running FastAPI

### Database & Authentication
- **firebase_admin** (7.1.0) - Firebase Admin SDK for server-side operations
- **pyrebase4** (4.8.1) - Firebase SDK for client-side operations
- **google-cloud-firestore** (2.22.0) - Firestore database client

### Data Validation
- **pydantic** (2.12.5) - Data validation and settings management
- **pydantic-core** - Core validation library for Pydantic

### AI & Image Processing
- **google-generativeai** (0.8.6) - Google Generative AI (Gemini) API client

### Utilities
- **python-dotenv** (1.2.1) - Load environment variables from .env file

### See `requirements.txt` for complete dependency list with versions

## 🚨 Error Handling

### HTTP Status Codes
The API returns appropriate status codes for different scenarios:

| Code | Meaning | Example |
|------|---------|---------|
| **200** | Success (GET/existing resource) | Menu retrieved successfully |
| **201** | Created (POST) | Menu item added successfully |
| **400** | Bad Request | Invalid input data, domain not registered |
| **401** | Unauthorized | Invalid or missing token |
| **403** | Forbidden | Staff accessing another stall's menu |
| **404** | Not Found | Menu item or stall doesn't exist |
| **413** | File Too Large | Menu image exceeds 5MB |
| **422** | Unprocessable Entity | Cannot extract menu from image |
| **500** | Server Error | Database or processing error |

### Response Format
All error responses follow a consistent JSON format:
```json
{
  "message": "Descriptive error message explaining what went wrong"
}
```

### Common Error Scenarios

1. **Authentication Errors**
   - Missing Authorization header → 401
   - Expired or invalid token → 401
   - Invalid email domain → 400

2. **Authorization Errors**
   - Student accessing staff endpoints → 403
   - Staff managing other stalls → 403
   - Non-manager adding staff → 403

3. **Data Validation Errors**
   - Passwords don't match → 400
   - Invalid file type → 400
   - Missing required fields → 422

4. **Resource Errors**
   - Menu item doesn't exist → 404
   - Stall not found → 404
   - College domain not registered → 400

## 🔄 Running the Application

### Development Mode
```bash
python main.py
```
- Starts Uvicorn server on `http://localhost:8000`
- Auto-reload enabled for development
- Hot reloading on file changes

### Access API Documentation
- **Swagger UI:** `http://localhost:8000/docs` - Interactive API testing
- **ReDoc:** `http://localhost:8000/redoc` - Beautiful API documentation

### Testing Endpoints
1. Visit `http://localhost:8000/docs`
2. Click "Try it out" on any endpoint
3. Fill in request parameters
4. View response details

## 📝 Code Organization Best Practices

### Authentication Module (`auth.py`)
- Handles all user and staff authentication
- Password validation and college domain verification
- Firebase user creation and token generation
- Helper functions for code modularity

### Staff Module (`staff.py`)
- Manages all staff-related operations
- Menu upload with batch operations
- Image scanning with AI integration
- Staff authorization checks at each operation
- Efficient Firestore transactions

### User Module (`user.py`)
- Handles student operations
- College-based menu retrieval
- Active stall filtering
- Available item filtering

### Manager Module (`manager.py`)
- Team management operations
- Staff member addition and removal
- Email updates with atomic batch operations
- Role-based access control enforcement

### Schema Module (`schema.py`)
- Pydantic models for all request/response types
- Input validation with field constraints
- Automatic OpenAPI documentation generation

## 🔒 Security Considerations

### Authentication Security
1. **Firebase Authentication** - Industry-standard secure password hashing
2. **ID Tokens** - Short-lived tokens with automatic expiration
3. **Token Verification** - All protected endpoints verify tokens server-side

### Authorization Security
1. **Stall-level Access Control** - Staff can only manage assigned stalls
2. **Role-based Authorization** - Different permissions for different roles
3. **Email Domain Verification** - Only registered college domains allowed

### Data Security
1. **Input Validation** - Pydantic validates all request data
2. **File Upload Validation** - Type and size restrictions on images
3. **Environment Variables** - Sensitive credentials in `.env` (not committed)
4. **Firestore Security Rules** - Should be configured separately

### Best Practices Implemented
1. No passwords returned in API responses
2. Batch operations for data consistency
3. Timestamps for audit trails
4. Proper error messages without exposing system details
5. CORS and rate limiting (should be added for production)

## 🛠️ Development Tips

### Local Testing
1. Use `/docs` endpoint for interactive API testing
2. Keep `serviceAccountKey.json` secured (in .gitignore)
3. Test with various college domains
4. Monitor Firestore Console for real-time data updates

### Debugging
1. Check Firebase Console for authentication logs
2. Use Firestore Console to verify document structure
3. Enable debug logging for Firebase operations
4. Test image scanning with various menu images

### Performance Optimization
1. Use batch writes for multiple item insertions
2. Implement pagination for large menu lists (future)
3. Cache college domains (future)
4. Monitor Gemini API usage for cost optimization

### Production Deployment
1. Add request/response logging
2. Implement rate limiting
3. Set up CORS properly
4. Use environment-specific configs
5. Enable Firestore security rules
6. Set up backup and recovery procedures

## 📞 Support & Contribution

For issues, questions, or contributions:
1. Check existing documentation
2. Review Firebase Console for data integrity
3. Check Gemini API status and quota
4. Verify environment variables are set correctly

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

---

**Last Updated:** January 2026  
**Backend Version:** 1.0.0  
**API Version:** 1.0

