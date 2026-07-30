from passlib.context import CryptContext

# Set up pwd_context in case password hashing/verification is needed in the future
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hardcoded mock users with plain passwords (ปกติที่ยังไม่ hash) as requested for demo
MOCK_USERS = [
    {
        "username": "admin",
        "password": "adminpassword123",
        "role": "admin"
    },
    {
        "username": "demo_user",
        "password": "userpassword456",
        "role": "user"
    }
]

def authenticate_user(username: str, password: str) -> dict | None:
    """
    Authenticate the user against the hardcoded mock database.
    Returns the user data (without password) if successful, otherwise None.
    """
    for user in MOCK_USERS:
        if user["username"] == username and user["password"] == password:
            user_info = user.copy()
            user_info.pop("password", None)
            return user_info
    return None

def get_user_by_username(username: str) -> dict | None:
    """
    Retrieve user information by username.
    """
    for user in MOCK_USERS:
        if user["username"] == username:
            user_info = user.copy()
            user_info.pop("password", None)
            return user_info
    return None

