from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, UserProfile
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

class UserRegister(BaseModel):
    email: str
    username: str
    password: str
    deity_preference: Optional[str] = "Ganesha"
    philosophy_preference: Optional[str] = "Advaita"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    deity_preference: Optional[str] = None
    philosophy_preference: Optional[str] = None
    spiritual_goals: Optional[str] = None

class ProfileOut(BaseModel):
    id: int
    full_name: Optional[str]
    deity_preference: str
    philosophy_preference: str
    spiritual_goals: Optional[str]

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    profile: Optional[ProfileOut]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserOut)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
        
    hashed_pwd = get_password_hash(user_in.password)
    user = User(email=user_in.email, username=user_in.username, hashed_password=hashed_pwd)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create profile
    profile = UserProfile(
        user_id=user.id,
        deity_preference=user_in.deity_preference,
        philosophy_preference=user_in.philosophy_preference
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=ProfileOut)
def update_profile(
    profile_in: ProfileUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        
    if profile_in.full_name is not None:
        profile.full_name = profile_in.full_name
    if profile_in.deity_preference is not None:
        profile.deity_preference = profile_in.deity_preference
    if profile_in.philosophy_preference is not None:
        profile.philosophy_preference = profile_in.philosophy_preference
    if profile_in.spiritual_goals is not None:
        profile.spiritual_goals = profile_in.spiritual_goals
        
    db.commit()
    db.refresh(profile)
    return profile
