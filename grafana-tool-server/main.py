from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx
import os

app = FastAPI(title="Grafana › n8n proxy tool server")

N8N_WEBHOOK = os.environ.get(
    "N8N_WEBHOOK", "http://n8n:5678/webhook/grafana-query"
)

class QueryIn(BaseModel):
    query: str
    from_: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None

class QueryOut(BaseModel):
    text: str

@app.post("/grafana-query", response_model=QueryOut)
async def grafana_query(inp: QueryIn):
    payload = {
        "queries": [
            {
                "refId": "A",
                "datasource": {"uid": "ae9t2q2vad4w0e", "type": "prometheus"},
                "expr": inp.query,
                "intervalMs": 15000,
                "maxDataPoints": 43200
            }
        ],
        "from": inp.from_ or "now-1h",
        "to": inp.to or "now"
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(N8N_WEBHOOK, json=payload, timeout=120.0)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    # Parse n8n response JSON, fallback to text if parse fails
    try:
        resp_json = r.json()
    except Exception:
        resp_json = {"text": r.text.strip()}

    return resp_json
