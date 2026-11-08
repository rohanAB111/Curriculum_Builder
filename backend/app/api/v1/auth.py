import sqlite3
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.database import get_db
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    get_current_user_payload,
    hash_password,
    verify_password,
)
from backend.app.schemas.auth import Token, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
def register(user_in: UserRegister, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (user_in.email.lower().strip(),))
    if cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )
    
    hashed_pwd = hash_password(user_in.password)
    cur.execute(
        """
        INSERT INTO users (email, full_name, hashed_password, role, department_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_in.email.lower().strip(), user_in.full_name, hashed_pwd, user_in.role, user_in.department_id or 1)
    )
    db.commit()
    user_id = cur.lastrowid

    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    return UserResponse(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        role=row["role"],
        department_id=row["department_id"],
        is_active=bool(row["is_active"])
    )


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (login_in.email.lower().strip(),))
    row = cur.fetchone()
    if not row or not verify_password(login_in.password, row["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not bool(row["is_active"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account. Contact administrator.",
        )
    
    token_payload = {
        "sub": row["email"],
        "user_id": row["id"],
        "role": row["role"],
        "full_name": row["full_name"],
        "department_id": row["department_id"],
    }
    access_token = create_access_token(token_payload)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=60 * 24 * 7 * 60,
        role=row["role"],
        user_id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user_payload),
    db: sqlite3.Connection = Depends(get_db)
):
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (current_user["user_id"],))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        role=row["role"],
        department_id=row["department_id"],
        is_active=bool(row["is_active"])
    )
