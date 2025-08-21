## HSA Demo App

This is a simple demo of a **Health Savings Account (HSA)** lifecycle.  
Built with **FastAPI**, **SQLite**, and **Jinja2 templates**, it runs entirely locally (no external services).

## What it does

- Create an account (one per email)  
- Deposit funds  
- Issue a virtual debit card (PAN, CVV, Exp)  
- Simulate purchases (approved only if qualified + balance is enough)  
- Show transaction history (deposits, approvals, declines)  

## How to run

1. Clone this repo and move into the folder:

   ```bash
   git clone <your-repo-url>
   cd hsa

2. Set up a virtual environment:

    python -m venv .venv

    # activate it 
    source .venv/bin/activate   # Mac/Linux 
    .venv\Scripts\activate      # Windows

3. Install dependencies

    pip install -r requirements.txt

4. Run the app

    uvicorn app.main:app --reload

5. Open in your browser

    http://127.0.0.1:8000

6. Notes

    - Demo only, no real money involved