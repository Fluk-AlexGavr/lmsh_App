from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text
# Models
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from pydantic import BaseModel
from datetime import datetime
import qrcode
import io
from fastapi.responses import StreamingResponse
from typing import List

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with async_session() as session:
        yield session

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    score = Column(Integer, default=0)
    transactions = relationship("Transaction", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    transaction_time = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="transactions")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Schemas
class UserCreate(BaseModel):
    full_name: str

class TransactionCreate(BaseModel):
    user_id: int
    score_change: int

class UserOut(BaseModel):
    id: int
    full_name: str
    score: int

    class Config:
        orm_mode = True

class TransactionOut(BaseModel):
    id: int
    user_id: int
    score: int
    transaction_time: datetime

    class Config:
        orm_mode = True

class SessionOut(BaseModel):
    id: int
    session_name: str
    created_at: datetime

    class Config:
        orm_mode = True

# FastAPI app
app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(full_name=user.full_name)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.get("/qr")
async def generate_qr(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    qr_data = f"{user.full_name}|{user.id}"
    qr = qrcode.QRCode()
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")

@app.get("/users", response_model=List[UserOut])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM users"))
    users = result.fetchall()
    return [{"id": row.id, "full_name": row.full_name, "score": row.score} for row in users]

@app.get("/transactions", response_model=List[TransactionOut])
async def get_transactions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM transactions"))
    transactions = result.fetchall()
    return [{"id": row.id, "user_id": row.user_id, "score": row.score, "transaction_time": row.transaction_time} for row in transactions]

@app.get("/sessions", response_model=List[SessionOut])
async def get_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM sessions"))
    sessions = result.fetchall()
    return [{"id": row.id, "session_name": row.session_name, "created_at": row.created_at} for row in sessions]
