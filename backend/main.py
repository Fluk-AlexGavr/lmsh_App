from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text
# Models
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import json
from pydantic import BaseModel
from datetime import datetime
import qrcode
import io
from fastapi.responses import StreamingResponse
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_= AsyncSession, expire_on_commit=False
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Укажите список разрешённых доменов, например ["http://192.168.1.100:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/update-score")
async def update_score(data: TransactionCreate, db: AsyncSession = Depends(get_db)):
    # Получаем пользователя из базы данных
    print(data)
    user = await db.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем, что значение изменения счета - целое число
    if not isinstance(data.score_change, int):
        raise HTTPException(status_code=400, detail="Score change must be an integer")

    # Если значение отрицательное, проверяем модуль
    if data.score_change < 0 and abs(data.score_change) > user.score:
        raise HTTPException(
            status_code=400, 
            detail="Score reduction exceeds current score"
        )

    # Обновляем счет пользователя
    user.score += data.score_change

    # Записываем транзакцию в базу данных
    new_transaction = Transaction(
        user_id=data.user_id, 
        score=data.score_change
    )
    db.add(new_transaction)
    await db.commit()
    await db.refresh(user)

    return {
        "message": "Score updated successfully",
        "new_score": user.score
    }

@app.get("/qr")
async def generate_qr(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = {
        "id" : user.id,
        "full_name" : user.full_name
    }
    qr_data = json.dumps(user_data)
    qr = qrcode.QRCode()
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")

@app.get("/user/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):

    query = text("SELECT * FROM users WHERE id = :user_id")
    result = await db.execute(query, {"user_id": user_id})
    user = result.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "full_name": user.full_name,
        "score": user.score
    }

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
