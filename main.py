from fastapi import FastAPI, Header, HTTPException, Depends
import httpx
import hashlib
import random

SUPABASE_URL = "https://yftgbwljsajlqfvhlctk.supabase.co"
SUPABASE_KEY = "sb_publishable_nn95C_w8FMXCUqIAM9pmEQ_yDm2bcXb"
HEADERS = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}

app = FastAPI(title="SlangIQ API", version="1.0")

def verify_api_key(x_api_key: str = Header(...)):
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/api_keys?key_hash=eq.{key_hash}&select=*", headers=HEADERS)
    data = r.json()
    if not data or data[0]["calls_this_month"] >= data[0]["monthly_limit"]:
        raise HTTPException(status_code=401, detail="Invalid or rate-limited API key")
    return data[0]

@app.get("/v1/lookup/{term}")
def lookup_term(term: str, key=Depends(verify_api_key)):
    slug = term.lower().replace(" ", "-")
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/terms?slug=eq.{slug}&status=eq.active&select=*", headers=HEADERS)
    data = r.json()
    if not data:
        raise HTTPException(status_code=404, detail="Term not found")
    row = data[0]
    return {
        "term": row["term"],
        "definition": row["definition"],
        "sentiment": row["sentiment"],
        "trend_score": row["trend_score"],
        "origin_platform": row["origin_platform"],
        "subculture": row["subculture"],
        "status": row["status"]
    }

@app.get("/v1/trending")
def trending(limit: int = 10, key=Depends(verify_api_key)):
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/terms?status=eq.active&order=trend_score.desc&limit={limit}&select=term,trend_score,sentiment,subculture", headers=HEADERS)
    return {"trending": r.json()}

@app.get("/v1/brand-safe/{term}")
def brand_safe_check(term: str, key=Depends(verify_api_key)):
    slug = term.lower().replace(" ", "-")
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/terms?slug=eq.{slug}&select=sentiment,status,trend_score", headers=HEADERS)
    data = r.json()
    if not data:
        return {"safe": None, "reason": "Term not in database"}
    row = data[0]
    safe = row["sentiment"] != "negative" and row["status"] == "active"
    return {
        "term": term,
        "brand_safe": safe,
        "sentiment": row["sentiment"],
        "still_relevant": row["status"] == "active",
        "trend_score": row["trend_score"]
    }

@app.get("/v1/search")
def search_terms(q: str, key=Depends(verify_api_key)):
    r = httpx.get(
        f"{SUPABASE_URL}/rest/v1/terms?or=(term.ilike.*{q}*,definition.ilike.*{q}*,subculture.ilike.*{q}*)&status=eq.active&order=trend_score.desc&select=term,slug,definition,sentiment,trend_score,subculture",
        headers=HEADERS
    )
    data = r.json()
    if not data:
        return {"results": [], "count": 0, "query": q}
    return {"results": data, "count": len(data), "query": q}

@app.get("/v1/by-subculture/{subculture}")
def by_subculture(subculture: str, key=Depends(verify_api_key)):
    r = httpx.get(
        f"{SUPABASE_URL}/rest/v1/terms?subculture=ilike.*{subculture}*&status=eq.active&order=trend_score.desc&select=term,slug,definition,sentiment,trend_score,subcultu