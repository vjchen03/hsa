from contextlib import contextmanager
from typing import Optional
from sqlmodel import SQLModel, Session, create_engine, select

from .models import User, HSAAccount, Card, Transaction, ExpenseCategory

# datebase setup
DB_URL = "sqlite:///hsa.db"   # local file in project root
engine = create_engine(DB_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session

# user and account functions
def get_user_by_email(email: str) -> Optional[User]:
    with get_session() as s:
        return s.exec(select(User).where(User.email == email)).first()

def create_user(email: str, full_name: str) -> User:
    with get_session() as s:
        user = User(email=email, full_name=full_name)
        s.add(user)
        s.commit()
        s.refresh(user)

        # create the user's HSA automatically
        acct = HSAAccount(user_id=user.id)
        s.add(acct)
        s.commit()
        s.refresh(acct)

        return user

def get_account_for_user(user_id: int) -> HSAAccount:
    with get_session() as s:
        return s.exec(select(HSAAccount).where(HSAAccount.user_id == user_id)).one()

def deposit(account_id: int, amount_cents: int) -> HSAAccount:
    with get_session() as s:
        acct = s.get(HSAAccount, account_id)
        acct.balance_cents += amount_cents
        s.add(acct)
        s.commit()
        s.refresh(acct)

        # create a deposit transaction
        txn = Transaction(
            account_id=account_id,
            amount_cents=amount_cents,
            category=ExpenseCategory.deposit,
            approved=True,
            meta="Deposit"
        )
        s.add(txn)
        s.commit()

        return acct


# card functions
def get_card_for_account(account_id: int) -> Optional[Card]:
    with get_session() as s:
        return s.exec(select(Card).where(Card.account_id == account_id)).first()

def save_card(card: Card) -> Card:
    with get_session() as s:
        s.add(card)
        s.commit()
        s.refresh(card)
        return card

# transaction functions
def create_txn(
                account_id: int,
                amount_cents: int,
                category: ExpenseCategory, 
                approved: bool,
                meta: Optional[str] = None,
              ) -> Transaction:
    with get_session() as s:
        txn = Transaction(
            account_id=account_id,
            amount_cents=amount_cents,
            category=category,
            approved=approved,
            meta=meta,
        )
        s.add(txn)
        s.commit()
        s.refresh(txn)
        return txn

def adjust_balance_for_txn(account_id: int, delta_cents: int) -> None:
    with get_session() as s:
        acct = s.get(HSAAccount, account_id)
        acct.balance_cents += delta_cents
        s.add(acct)
        s.commit()


def list_txns_for_account(account_id: int, limit: int = 25):
    with get_session() as s:
        return s.exec(
            select(Transaction)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .limit(limit)
        ).all()
