import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Bundle

app = FastAPI(title="Moniqué Shop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"brand": "Moniqué", "message": "Welcome to Moniqué API"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

# Seed bundles if not present
@app.post("/seed")
def seed_bundles():
    existing = get_documents("bundle", {}) if db else []
    if existing:
        return {"status": "ok", "seeded": False, "count": len(existing)}

    bundles = [
        Bundle(
            name="Essentials Bundle",
            tagline="Start strong with curated basics",
            description="Core pieces to kickstart your style.",
            items=[{"product_title": "Moniqué Tee", "qty": 1}, {"product_title": "Everyday Denim", "qty": 1}],
            price=129.0,
            highlight=True,
            image="/images/essentials.jpg"
        ),
        Bundle(
            name="Sport Selection",
            tagline="Move with intent",
            description="Performance-ready activewear for training and travel.",
            items=[{"product_title": "AeroFlex Leggings", "qty": 1}, {"product_title": "BreathLite Top", "qty": 1}],
            price=159.0,
            highlight=False,
            image="/images/sport.jpg"
        ),
        Bundle(
            name="Luxury Selection",
            tagline="Elevated materials. Effortless detail.",
            description="Premium pieces crafted for statement moments.",
            items=[{"product_title": "Cashmere Knit", "qty": 1}, {"product_title": "Silk Scarf", "qty": 1}],
            price=399.0,
            highlight=False,
            image="/images/luxury.jpg"
        ),
    ]

    for b in bundles:
        create_document("bundle", b)

    return {"status": "ok", "seeded": True, "count": len(bundles)}

class BundleOut(BaseModel):
    name: str
    tagline: Optional[str]
    description: Optional[str]
    price: float
    highlight: bool = False
    image: Optional[str]

@app.get("/bundles", response_model=List[BundleOut])
def list_bundles():
    docs = get_documents("bundle", {}) if db else []
    # transform ObjectId and unknown fields
    out = []
    for d in docs:
        out.append({
            "name": d.get("name"),
            "tagline": d.get("tagline"),
            "description": d.get("description"),
            "price": float(d.get("price", 0)),
            "highlight": bool(d.get("highlight", False)),
            "image": d.get("image"),
        })
    return out

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
