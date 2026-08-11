from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.logger import get_logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger(__name__)

def register_user(db: Session, username: str, password_plain: str, role: str = "user") -> User:
    """
    Register a new user, hashing the password using bcrypt.
    Throws ValueError if the username is already taken.
    """
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        logger.error(f"Registration failed: Username '{username}' already exists")
        raise ValueError("Username already exists")
    
    hashed_password = pwd_context.hash(password_plain)
    db_user = User(
        username=username,
        hashed_password=hashed_password,
        role=role
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User '{username}' registered successfully with role '{role}'")
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed for user '{username}': {str(e)}")
        raise e

def authenticate_user(db: Session, username: str, password_plain: str) -> User | None:
    """
    Authenticate the user against the database.
    Returns the User object if successful, otherwise None.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.error(f"Login failed: User '{username}' not found")
        return None
        
    if not pwd_context.verify(password_plain, user.hashed_password):
        logger.error(f"Login failed: Incorrect password for user '{username}'")
        return None
        
    logger.info(f"User '{username}' authenticated successfully")
    return user

def get_user_by_username(db: Session, username: str) -> User | None:
    """
    Retrieve user information by username from the database.
    """
    return db.query(User).filter(User.username == username).first()
