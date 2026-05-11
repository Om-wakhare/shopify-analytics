"""
Generate 30 days of realistic D2C test data in Shopify dev store.

Creates:
  - 25 customers
  - 80 orders spread across the last 30 days
  - Repeat buyers (some customers order 2-4 times)
  - Multiple line items per order
  - Mix of financial statuses (mostly paid)

Handles 429 rate limiting with exponential back-off.
"""
import asyncio
import random
import time
from datetime import datetime, timedelta, timezone
import httpx

# ── Config ────────────────────────────────────────────────────────────────────
import os
SHOP  = os.environ.get("SHOP_DOMAIN", "your-store.myshopify.com")
TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
BASE  = f"https://{SHOP}/admin/api/2026-04"
HEADS = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}

DELAY = 1.5   # seconds between API calls (avoids 429)

# ── Data fixtures ─────────────────────────────────────────────────────────────
PRODUCTS = [
    ("Premium Serum Bundle",   "89.99", 3),
    ("Vitamin C Serum 30ml",   "44.99", 2),
    ("Hydrating Face Cream",   "34.99", 3),
    ("Eye Contour Gel",        "29.99", 2),
    ("SPF 50 Daily Moisturizer","39.99",2),
    ("Night Repair Oil",       "54.99", 2),
    ("Brightening Toner",      "24.99", 4),
    ("Hyaluronic Mask 3-Pack", "19.99", 5),
    ("Recovery Serum",         "64.99", 1),
    ("Glow Starter Kit",       "79.99", 1),
    ("Daily Cleanser",         "22.99", 4),
    ("Retinol Night Cream",    "59.99", 2),
]

CUSTOMERS_DATA = [
    ("Emma",     "Smith",    "emma.smith"),
    ("Liam",     "Johnson",  "liam.johnson"),
    ("Olivia",   "Williams", "olivia.williams"),
    ("Noah",     "Brown",    "noah.brown"),
    ("Ava",      "Jones",    "ava.jones"),
    ("James",    "Garcia",   "james.garcia"),
    ("Isabella", "Miller",   "isabella.miller"),
    ("Oliver",   "Davis",    "oliver.davis"),
    ("Sophia",   "Wilson",   "sophia.wilson"),
    ("William",  "Moore",    "william.moore"),
    ("Mia",      "Taylor",   "mia.taylor"),
    ("Ethan",    "Anderson", "ethan.anderson"),
    ("Charlotte","Thomas",   "charlotte.thomas"),
    ("Lucas",    "Jackson",  "lucas.jackson"),
    ("Amelia",   "White",    "amelia.white"),
    ("Mason",    "Harris",   "mason.harris"),
    ("Harper",   "Martin",   "harper.martin"),
    ("Logan",    "Thompson", "logan.thompson"),
    ("Evelyn",   "Martinez", "evelyn.martinez"),
    ("Aiden",    "Robinson", "aiden.robinson"),
    ("Aria",     "Clark",    "aria.clark"),
    ("Jackson",  "Lewis",    "jackson.lewis"),
    ("Luna",     "Lee",      "luna.lee"),
    ("Caden",    "Walker",   "caden.walker"),
    ("Chloe",    "Hall",     "chloe.hall"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def days_ago(n):
    """Return ISO timestamp for N days ago."""
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


async def api_post(client, url, payload, retries=6):
    """POST with exponential back-off on 429."""
    wait = 3
    for attempt in range(retries):
        try:
            r = await client.post(url, headers=HEADS, json=payload, timeout=60.0)
            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", wait))
                print(f"    ⏳ Rate limited — waiting {retry_after}s…")
                await asyncio.sleep(retry_after)
                wait = min(wait * 2, 30)
                continue
            return r
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
            print(f"    ⚠ Network error ({e}) — retry {attempt+1}/{retries}")
            await asyncio.sleep(wait)
            wait = min(wait * 2, 20)
    return None


def make_line_items(count=1):
    """Generate 1-3 realistic line items."""
    items = []
    chosen = random.sample(PRODUCTS, min(count, len(PRODUCTS)))
    for name, price, max_qty in chosen:
        items.append({
            "title":    name,
            "price":    price,
            "quantity": random.randint(1, min(max_qty, 3)),
        })
    return items


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:

        # ── Step 1: Create customers ─────────────────────────────────────────
        print("=" * 55)
        print("  Creating 25 customers")
        print("=" * 55)

        customers = []   # list of (shopify_id, email)

        uid = int(time.time()) % 100000  # unique suffix per run
        for i, (first, last, handle) in enumerate(CUSTOMERS_DATA):
            email = f"{handle}{uid}{i}@shoptest.dev"
            r = await api_post(client, f"{BASE}/customers.json", {
                "customer": {
                    "first_name":        first,
                    "last_name":         last,
                    "email":             email,
                    "verified_email":    True,
                    "accepts_marketing": random.choice([True, True, False]),
                    "tags":              random.choice(["vip", "wholesale", "", "new", ""]),
                }
            })

            if r and r.status_code == 201:
                cid = r.json()["customer"]["id"]
                customers.append((cid, email))
                print(f"  ✓ {i+1:02d}/25  {email}")
            else:
                code = r.status_code if r else "timeout"
                print(f"  ✗ {i+1:02d}/25  {email}  ({code})")

            await asyncio.sleep(DELAY)

        print(f"\n  → {len(customers)} customers created\n")

        if not customers:
            print("No customers created — aborting.")
            return

        # ── Step 2: Generate order schedule ──────────────────────────────────
        # Spread 80 orders over last 30 days.
        # ~60% of customers order multiple times (repeat buyers).

        orders_schedule = []

        # Every customer gets at least 1 order
        for cid, email in customers:
            orders_schedule.append((cid, email, random.randint(0, 29)))

        # Top 40% of customers get 1-3 extra orders (repeat buyers)
        repeat_buyers = random.sample(customers, k=max(1, len(customers) * 40 // 100))
        for cid, email in repeat_buyers:
            for _ in range(random.randint(1, 3)):
                orders_schedule.append((cid, email, random.randint(0, 29)))

        # Shuffle so orders aren't grouped by customer
        random.shuffle(orders_schedule)
        # Cap at 80
        orders_schedule = orders_schedule[:80]

        # ── Step 3: Create orders ─────────────────────────────────────────────
        print("=" * 55)
        print(f"  Creating {len(orders_schedule)} orders (last 30 days)")
        print("=" * 55)

        ok = 0
        for j, (cid, email, d_ago) in enumerate(orders_schedule):
            ts            = days_ago(d_ago)
            line_items    = make_line_items(random.randint(1, 3))
            fin_status    = random.choices(
                ["paid", "paid", "paid", "paid", "refunded", "pending"],
                weights=[70, 70, 70, 70, 5, 5]
            )[0]

            r = await api_post(client, f"{BASE}/orders.json", {
                "order": {
                    "customer":              {"id": cid},
                    "email":                 email,
                    "financial_status":      fin_status,
                    "created_at":            ts,
                    "processed_at":          ts,
                    "line_items":            line_items,
                    "send_receipt":          False,
                    "send_fulfillment_receipt": False,
                }
            })

            status = r.status_code if r else 0
            ok    += status == 201
            items_str = ", ".join(li["title"][:18] for li in line_items)
            print(f"  {'✓' if status==201 else '✗'} {j+1:02d}/{len(orders_schedule)}  "
                  f"day-{d_ago:02d}  {fin_status:8s}  [{items_str}]")

            await asyncio.sleep(DELAY)

        # ── Summary ───────────────────────────────────────────────────────────
        print(f"\n{'='*55}")
        print(f"  ✅  {len(customers)} customers  |  {ok} orders created")
        print(f"{'='*55}")
        print("\nNow run the sync:")
        print(f"  curl -s -X POST http://localhost:8000/sync/bulk \\")
        print(f"    -H 'Content-Type: application/json' \\")
        print(f"    -d '{{\"shop_domain\":\"{SHOP}\",\"entity\":\"all\"}}'")


asyncio.run(main())
