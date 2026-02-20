from fastapi import APIRouter, HTTPException, status, Response, Depends, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt
import httpx
from models.user import UserCreate, User
from middleware.auth import get_current_user
from config.database import get_database

router = APIRouter(prefix="/auth", tags=["authentication"])

# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SessionRequest(BaseModel):
    session_id: str

class LoginResponse(BaseModel):
    user: User
    message: str

@router.post("/register")
async def register(user_data: UserCreate, response: Response):
    """
    Register new user with email and password.
    """
    db = get_database()
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user document
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role,
        "batch_id": user_data.batch_id,
        "profile_pic": user_data.profile_pic,
        "phone_number": user_data.phone_number,
        "telegram_id": user_data.telegram_id,
        "password": hashed_password.decode('utf-8'),
        "created_at": datetime.now(timezone.utc),
        "last_login": None
    }
    
    await db.users.insert_one(user_doc)
    
    # Create session
    session_token = f"session_{uuid.uuid4().hex}"
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    # Return user without password
    user_doc.pop("password", None)
    user_doc.pop("_id", None)
    
    return {
        "user": user_doc,
        "message": "Registration successful"
    }

@router.post("/login")
async def login(login_data: LoginRequest, response: Response):
    """
    Login with email and password.
    """
    db = get_database()
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user_doc["password"].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    await db.users.update_one(
        {"user_id": user_doc["user_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    # Create session
    session_token = f"session_{uuid.uuid4().hex}"
    session_doc = {
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    # Return user without password
    user_doc.pop("password", None)
    user_doc.pop("_id", None)
    
    return {
        "user": user_doc,
        "message": "Login successful"
    }

@router.post("/google/session")
async def google_session(request: Request, response: Response, x_session_id: str = Header(None)):
    """
    Exchange Google OAuth session_id for user data and create session.
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-ID header required"
        )
    
    # Call Emergent Auth API to get session data
    async with httpx.AsyncClient() as http_client:
        try:
            auth_response = await http_client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": x_session_id}
            )
            auth_response.raise_for_status()
            session_data = auth_response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to verify session: {str(e)}"
            )
    
    email = session_data.get("email")
    name = session_data.get("name")
    picture = session_data.get("picture")
    emergent_session_token = session_data.get("session_token")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found in session data"
        )
    
    # Check if user exists
    user_doc = await db.users.find_one({"email": email})
    
    if user_doc:
        # Update existing user
        user_id = user_doc["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "name": name,
                    "profile_pic": picture,
                    "last_login": datetime.now(timezone.utc)
                }
            }
        )
    else:
        # Create new user (default to student role)
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "role": "student",
            "profile_pic": picture,
            "batch_id": None,
            "phone_number": None,
            "telegram_id": None,
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_doc)
    
    # Create session with Emergent token
    session_doc = {
        "user_id": user_id,
        "session_token": emergent_session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=emergent_session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    # Get fresh user data
    user_result = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0, "password": 0}
    )
    
    return {
        "user": user_result,
        "message": "Google authentication successful"
    }

@router.get("/me")
async def get_me(request: Request):
    """
    Get current user data from session.
    """
    user = await get_current_user(request)
    return user

@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Logout user by deleting session.
    """
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    # Clear cookie
    response.delete_cookie(
        key="session_token",
        path="/",
        samesite="none",
        secure=True
    )
    
    return {"message": "Logout successful"}
