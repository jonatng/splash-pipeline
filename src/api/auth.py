from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from src.utils.auth import sign_up_user, sign_in_user, sign_out_user, get_current_user, request_password_reset, update_password

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordUpdate(BaseModel):
    new_password: str

@router.post("/signup", response_model=Token)
async def signup(user: UserCreate):
    try:
        response = await sign_up_user(user.email, user.password)
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        response = await sign_in_user(form_data.username, form_data.password)
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        await sign_out_user(token)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest):
    """Request a password reset email."""
    try:
        await request_password_reset(request.email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update-password")
async def update_user_password(
    password_update: PasswordUpdate,
    token: str = Depends(oauth2_scheme)
):
    """Update user's password."""
    try:
        await update_password(token, password_update.new_password)
        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 