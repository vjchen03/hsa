from datetime import datetime, UTC
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class ExpenseCategory(str, Enum):
    # qualified expenses
    doctor_visit = "doctor_visit"
    prescription = "prescription"

    # not qualified expenses
    groceries = "groceries" 
    restaurants = "restaurants" 

    deposit = "deposit" 


# user model
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True) 
    full_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # relationships
    account: Optional["HSAAccount"] = Relationship(back_populates="user")


# hsa account 
class HSAAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    balance_cents: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # relationships
    user: User = Relationship(back_populates="account")
    card: Optional["Card"] = Relationship(back_populates="account")


# debit card linked to hsa account
class Card(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="hsaaccount.id", index=True, unique=True)
    pan: str  # 16-digit string
    cvv: str  # 3-digit string
    expiry_month: int
    expiry_year: int

    # relationships
    account: HSAAccount = Relationship(back_populates="card")


# a transaction on the hsa account
class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="hsaaccount.id", index=True)
    amount_cents: int
    category: ExpenseCategory
    approved: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    meta: Optional[str] = None  # additional details
