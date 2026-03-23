from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Company Internal Bots")

class ChatRequest(BaseModel):
    query: str

@app.post("/chat/intranet")
async def intranet_bot(request: ChatRequest):
    query = request.query.lower()
    # Simple mock logic for intranet policy
    if "remote" in query or "wfh" in query:
        return {"response": "Employees are allowed to work from home up to 3 days a week. Tuesdays and Thursdays are mandatory office days."}
    elif "leave" in query or "pto" in query:
        return {"response": "All full-time employees get 20 days of Paid Time Off per year, plus 10 sick days."}
    else:
        return {"response": "I am the Intranet Bot. I can answer questions about PTO, remote work policies, and other company guidelines."}

@app.post("/chat/finance")
async def finance_bot(request: ChatRequest):
    query = request.query.lower()
    # Simple mock logic for finance
    if "revenue" in query or "sales" in query:
        return {"response": "Our latest Q3 revenue was reported at $12.5 Million, an 8% increase from Q2."}
    elif "budget" in query or "expense" in query:
        return {"response": "The marketing budget for next quarter is capped at $2.2 Million. General admin expenses are tracking 5% below budget."}
    else:
        return {"response": "I am the Finance Bot. I can answer questions about revenue, budgets, expenses, and financial performance."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
