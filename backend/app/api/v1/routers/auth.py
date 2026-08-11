from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import register_user, authenticate_user, get_user_by_username
from app.core.security import create_access_token, verify_token
from app.core.database import get_db
from app.core.logger import get_logger

router = APIRouter(prefix="/auth", tags=["Auth"])
security_scheme = HTTPBearer()
logger = get_logger(__name__)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, register_data.username, register_data.password, register_data.role)
        logger.info(f"API: User '{register_data.username}' registered successfully")
        return UserResponse(username=user.username, role=user.role)
    except ValueError as e:
        logger.error(f"API: Registration failed for user '{register_data.username}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        logger.error(f"API: Login failed for user '{login_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"API: User '{login_data.username}' logged in successfully")
    return TokenResponse(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return UserResponse(username=current_user.username, role=current_user.role)

@router.get("/users/me", response_model=UserResponse)
def get_users_me(current_user = Depends(get_current_user)):
    return UserResponse(username=current_user.username, role=current_user.role)

@router.get("/users/admin-only", response_model=UserResponse)
def get_users_admin_only(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        logger.error(f"API: Access denied for user '{current_user.username}' (role: {current_user.role}) trying to access admin-only path")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin access required"
        )
    logger.info(f"API: Admin user '{current_user.username}' accessed admin-only path")
    return UserResponse(username=current_user.username, role=current_user.role)

@router.get("/admin-only", response_model=UserResponse)
def get_admin_only(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        logger.error(f"API: Access denied for user '{current_user.username}' (role: {current_user.role}) trying to access admin-only path")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin access required"
        )
    logger.info(f"API: Admin user '{current_user.username}' accessed admin-only path")
    return UserResponse(username=current_user.username, role=current_user.role)
