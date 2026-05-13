from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
import httpx
import hashlib
import random
import os
import stripe

SUPABASE_URL = "https://yftgbwljsajlqfvhlctk.supabase.co"
SUPABASE_KEY = "sb_publishable_nn95C_w8FMXCUqIAM9pmEQ_yDm2bcXb"
HEADERS = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRO_PRICE_ID = "price_1TTsIkB086HLwwsDD5GH2GCP"
BUSINESS_PRICE_ID = "price_1TTt5vB086HLwwsDx97LB1Vs"

app = FastAPI(
    title="SlangIQ API",
    version="1.0",
    description="The Slang & Culture Intelligence API.",
    docs_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
  <title>SlangIQ API</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css">
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; background: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    .swagger-ui { background: #0a0a0a; }
    .swagger-ui .topbar { background: #0a0a0a; border-bottom: 1px solid #222; padding: 12px 0; }
    .swagger-ui .topbar-wrapper { justify-content: flex-start; padding: 0 40px; }
    .swagger-ui .topbar-wrapper .link { display: flex; align-items: center; gap: 10px; }
    .swagger-ui .topbar-wrapper .link:before { content: "SlangIQ"; font-size: 20px; font-weight: 800; color: #fff; }
    .swagger-ui .topbar-wrapper img { display: none; }
    .swagger-ui .topbar-wrapper input { display: none; }
    .swagger-ui .topbar-wrapper button { display: none; }
    .swagger-ui .info { margin: 40px; }
    .swagger-ui .info .title { color: #fff; font-size: 32px; font-weight: 800; }
    .swagger-ui .info .description p { color: #888; font-size: 16px; }
    .swagger-ui .scheme-container { background: #111; border: 1px solid #222; padding: 16px 40px; margin: 0; box-shadow: none; }
    .swagger-ui select { background: #1a1a1a; border: 1px solid #333; color: #fff; border-radius: 6px; }
    .swagger-ui .opblock-tag { color: #fff; border-bottom: 1px solid #222; font-size: 18px; }
    .swagger-ui .opblock-tag:hover { background: #111; }
    .swagger-ui .opblock { border-radius: 8px; border: 1px solid #222; margin: 8px 0; box-shadow: none; }
    .swagger-ui .opblock.opblock-get { background: #0d1117; border-color: #7c3aed; }
    .swagger-ui .opblock.opblock-get .opblock-summary-method { background: #7c3aed; border-radius: 4px; }
    .swagger-ui .opblock.opblock-get .opblock-summary { border-color: #7c3aed; }
    .swagger-ui .opblock-summary-path { color: #e2e8f0; }
    .swagger-ui .opblock-summary-description { color: #888; }
    .swagger-ui .opblock-body { background: #0a0a0a; }
    .swagger-ui .opblock-description-wrapper p { color: #888; }
    .swagger-ui table thead tr td, .swagger-ui table thead tr th { color: #888; border-bottom: 1px solid #222; }
    .swagger-ui .parameter__name { color: #e2e8f0; }
    .swagger-ui .parameter__type { color: #7c3aed; }
    .swagger-ui .parameter__in { color: #888; }
    .swagger-ui input[type=text], .swagger-ui textarea { background: #1a1a1a; border: 1px solid #333; color: #fff; border-radius: 6px; }
    .swagger-ui .btn { border-radius: 6px; font-weight: 600; }
    .swagger-ui .btn.execute { background: #7c3aed; border-color: #7c3aed; color: #fff; }
    .swagger-ui .btn.execute:hover { background: #6d28d9; }
    .swagger-ui .btn.cancel { border-color: #333; color: #888; }
    .swagger-ui .responses-inner { background: #0a0a0a; }
    .swagger-ui .response-col_status { color: #4ade80; }
    .swagger-ui .microlight { background: #111; border-radius: 6px; }
    .swagger-ui section.models { background: #0a0a0a; border: 1px solid #222; border-radius: 8px; }
    .swagger-ui section.models h4 { color: #fff; }
    .swagger-ui .model-title { color: #e2e8f0; }
    .swagger-ui .model { color: #888; }
    .swagger-ui .prop-type { color: #7c3aed; }
    .swagger-ui .wrapper { background: #0a0a0a; }
    .swagger-ui .no-margin { background: #0a0a0a; }
    body .swagger-ui .wrapper { padding: 0 20px; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/openapi.json",
      dom_id: '#swagger-ui',
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: "BaseLayout",
      defaultModelsExpandDepth: -1,
      syntaxHighlight: { theme: "monokai" }
    })
  </script>
</body>
</html>
""")

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
    url = f"{SUPABASE_URL}/rest/v1/terms?or=(term.ilike.*{q}*,definition.ilike.*{q}*,subculture.ilike.*{q}*)&status=eq.active&order=trend_score.desc&select=term,slug,definition,sentiment,trend_score,subculture"
    r = httpx.get(url, headers=HEADERS)
    data = r.json()
    if not data:
        return {"results": [], "count": 0, "query": q}
    return {"results": data, "count": len(data), "query": q}

@app.get("/v1/by-subculture/{subculture}")
def by_subculture(subculture: str, key=Depends(verify_api_key)):
    url = f"{SUPABASE_URL}/rest/v1/terms?subculture=ilike.*{subculture}*&status=eq.active&order=trend_score.desc&select=term,slug,definition,sentiment,trend_score,subculture"
    r = httpx.get(url, headers=HEADERS)
    data = r.json()
    if not data:
        return {"results": [], "count": 0, "subculture": subculture}
    return {"results": data, "count": len(data), "subculture": subculture}

@app.get("/v1/random")
def random_term():
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/terms?status=eq.active&select=term,slug,definition,sentiment,trend_score,subculture,origin_platform", headers=HEADERS)
    data = r.json()
    if not data:
        raise HTTPException(status_code=404, detail="No terms found")
    return random.choice(data)

@app.get("/subscribe/{plan}")
def subscribe(plan: str):
    if plan == "pro":
        price_id = PRO_PRICE_ID
    elif plan == "business":
        price_id = BUSINESS_PRICE_ID
    else:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose pro or business.")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url="https://slang-api-production.up.railway.app/success",
        cancel_url="https://slang-api-production.up.railway.app/cancel",
    )
    return RedirectResponse(session.url)

@app.get("/success")
def success():
    return {"message": "Payment successful! Your API key will be emailed to you shortly."}

@app.get("/cancel")
def cancel():
    return {"message": "Payment cancelled. Come back when you are ready."}
import secrets

@app.post("/signup")
def signup(email: str):
    check = httpx.get(f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}&select=*", headers=HEADERS)
    if check.json():
        raise HTTPException(status_code=400, detail="Email already registered.")
    api_key = secrets.token_hex(32)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    user_res = httpx.post(f"{SUPABASE_URL}/rest/v1/users", headers={**HEADERS, "Prefer": "return=representation"}, json={"email": email, "plan": "free"})
    user = user_res.json()[0]
    httpx.post(f"{SUPABASE_URL}/rest/v1/api_keys", headers=HEADERS, json={
        "user_id": user["id"],
        "key_hash": key_hash,
        "tier": "free",
        "monthly_limit": 100,
        "calls_this_month": 0
    })
    return {"api_key": api_key, "email": email, "plan": "free", "monthly_limit": 100}
