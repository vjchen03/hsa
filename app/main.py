from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from datetime import datetime, UTC 
import random

from .store import (
    init_db,
    get_user_by_email,
    create_user,
    get_account_for_user,
    deposit,
    get_card_for_account,
    save_card,
    create_txn,
    adjust_balance_for_txn,
    list_txns_for_account
)
from .models import ExpenseCategory, Card

templates = Jinja2Templates(directory="app/templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="HSA App", version="1.0", lifespan = lifespan)


# Helpers
def dollars_to_cents(amount_str: str) -> int:
    return int(round(float(amount_str.strip()) * 100))

def cents_to_dollars(cents: int) -> str:
    return f"${cents/100:.2f}"

# qualified expenses for demo purposes
QUALIFIED = {
    ExpenseCategory.doctor_visit,
    ExpenseCategory.prescription,
}

@app.get("/")
async def home(request: Request, email: str | None = None):
    user = acct = card = None
    balance_display = None
    txns = []
    if email:
        user = get_user_by_email(email)
        if user:
            acct = get_account_for_user(user.id)
            balance_display = cents_to_dollars(acct.balance_cents)
            card = get_card_for_account(acct.id)
            txns = list_txns_for_account(acct.id, limit=25)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "acct": acct,
            "card": card,
            "categories": list(ExpenseCategory),
            "qualified": {c.value for c in QUALIFIED},
            "balance_display": balance_display,
            "txns": txns,
            "fmt_dollars": cents_to_dollars,
        },
    )

@app.post("/register")
async def register(email: str = Form(...), full_name: str = Form(...)):
    existing = get_user_by_email(email)
    if not existing:
        create_user(email=email, full_name=full_name)
        msg = "created"
    else:
        msg = "loaded"
    return RedirectResponse(f"/?email={email}&msg={msg}", status_code=303)

@app.post("/deposit")
async def deposit_route(email: str = Form(...), amount: str = Form(...)):
    user = get_user_by_email(email)
    if user:
        acct = get_account_for_user(user.id)
        # store.deposit() should also create a 'deposit' Transaction row
        deposit(acct.id, dollars_to_cents(amount))
        return RedirectResponse(f"/?email={email}&msg=deposited", status_code=303)
    return RedirectResponse("/", status_code=303)

@app.post("/issue_card")
async def issue_card(email: str = Form(...)):
    user = get_user_by_email(email)
    if not user:
        return RedirectResponse("/", status_code=303)

    acct = get_account_for_user(user.id)
    if get_card_for_account(acct.id):
        msg = "card_exists"  # already has a card; don't create another
    else:
        pan = "".join(str(random.randint(0, 9)) for _ in range(16))
        cvv = "".join(str(random.randint(0, 9)) for _ in range(3))
        now = datetime.now(UTC)
        expiry_month = ((now.month + 5 - 1) % 12) + 1
        expiry_year = now.year + (1 if now.month > 6 else 0)
        card = Card(
            account_id=acct.id,
            pan=pan,
            cvv=cvv,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            # created_at=now  # include if your Card model has this field
        )
        save_card(card)
        msg = "card_issued"

    return RedirectResponse(f"/?email={email}&msg={msg}", status_code=303)

@app.post("/purchase")
async def purchase(
    email: str = Form(...),
    amount: str = Form(...),
    category: ExpenseCategory = Form(...),
    memo: str = Form(""),
):
    user = get_user_by_email(email)
    if not user:
        return RedirectResponse("/", status_code=303)

    acct = get_account_for_user(user.id)
    amt_cents = dollars_to_cents(amount)
    card = get_card_for_account(acct.id)

    approved = bool(card) and (category in QUALIFIED) and (acct.balance_cents >= amt_cents)
    create_txn(acct.id, amt_cents, category, approved, meta=memo)
    if approved:
        adjust_balance_for_txn(acct.id, -amt_cents)

    msg = "purchase_ok" if approved else "purchase_no"
    return RedirectResponse(f"/?email={email}&msg={msg}", status_code=303)