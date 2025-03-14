from fastapi import FastAPI, HTTPException
import requests
import uuid
import hashlib
import hmac
import time
import json
import base64

app = FastAPI()

# Dummy database
merchants = {}
products = {}
payments = {}
payouts = {}

# Rapyd API credentials (Replace with actual values)
RAPYD_ACCESS_KEY = "YOUR_RAPYD_KEY"
RAPYD_SECRET_KEY = "YOUR_RAPYD_PASSWORD"
RAPYD_BASE_URL = "https://sandboxapi.rapyd.net"

# Utility function to generate Rapyd headers
def generate_rapyd_headers(http_method, path, body):
    timestamp = str(int(time.time()))
    salt = str(uuid.uuid4())
    body_string = json.dumps(body) if body else ""
    
    to_sign = http_method + path + salt + timestamp + RAPYD_ACCESS_KEY + RAPYD_SECRET_KEY + body_string
    signature = base64.b64encode(hmac.new(RAPYD_SECRET_KEY.encode(), to_sign.encode(), hashlib.sha256).digest()).decode()
    
    return {
        "Content-Type": "application/json",
        "access_key": RAPYD_ACCESS_KEY,
        "salt": salt,
        "timestamp": timestamp,
        "signature": signature
    }

# Merchant onboarding
@app.post("/merchant/register")
def register_merchant(name: str):
    merchant_id = str(uuid.uuid4())
    merchants[merchant_id] = {
        "name": name,
        "balance": 0.0
    }
    return {"merchant_id": merchant_id, "message": "Merchant registered successfully"}

# Add product
@app.post("/merchant/{merchant_id}/add_product")
def add_product(merchant_id: str, name: str, price: float):
    if merchant_id not in merchants:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    product_id = str(uuid.uuid4())
    products[product_id] = {
        "merchant_id": merchant_id,
        "name": name,
        "price": price
    }
    return {"product_id": product_id, "message": "Product added successfully"}

# Collect payment using Rapyd
@app.post("/pay/{product_id}")
def collect_payment(
    product_id: str, 
    currency: str, 
    payment_method: str, 
    platform_fee_percentage: float = 10.0  # Default fee is 10%
):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    product = products[product_id]
    merchant_id = product["merchant_id"]
    amount = product["price"]

    # Validate platform fee percentage (should be between 0% and 100%)
    if not (0 <= platform_fee_percentage <= 100):
        raise HTTPException(status_code=400, detail="Invalid platform fee percentage")

    # Convert percentage to decimal
    platform_fee_decimal = platform_fee_percentage / 100

    # Calculate platform fee and merchant payout
    platform_fee = amount * platform_fee_decimal
    merchant_payout = amount - platform_fee  # Amount merchant receives

    # Prepare payment data for Rapyd API
    payment_data = {
        "amount": amount,
        "currency": currency,
        "payment_method": payment_method,
        "description": f"Payment for {product['name']}"
    }

    headers = generate_rapyd_headers("post", "/v1/payments", payment_data)
    response = requests.post(f"{RAPYD_BASE_URL}/v1/payments", json=payment_data, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to create payment")

    payment_response = response.json()
    payment_id = payment_response.get("id")

    # Store payment record
    payments[payment_id] = {
        "merchant_id": merchant_id,
        "amount": amount,
        "platform_fee": platform_fee,
        "merchant_payout": merchant_payout
    }

    # Update merchant balance
    merchants[merchant_id]["balance"] += merchant_payout

    return {
        "payment_id": payment_id,
        "platform_fee_percentage": platform_fee_percentage,
        "platform_fee": platform_fee,
        "merchant_payout": merchant_payout,
        "message": "Payment successful"
    }

# Payout to merchant using Rapyd
@app.post("/merchant/{merchant_id}/payout")
def payout_merchant(merchant_id: str):
    if merchant_id not in merchants:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    balance = merchants[merchant_id]["balance"]
    if balance <= 0:
        raise HTTPException(status_code=400, detail="No funds available for payout")
    
    payout_data = {
        "amount": balance,
        "currency": "USD",
        "payout_method_type": "bank_transfer",
        "sender_currency": "USD",
        "beneficiary": {
            "name": merchants[merchant_id]["name"]
        }
    }
    
    headers = generate_rapyd_headers("post", "/v1/payouts", payout_data)
    response = requests.post(f"{RAPYD_BASE_URL}/v1/payouts", json=payout_data, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to process payout")
    
    payout_response = response.json()
    payout_id = payout_response.get("id")
    payouts[payout_id] = {"merchant_id": merchant_id, "amount": balance}
    merchants[merchant_id]["balance"] = 0
    
    return {"payout_id": payout_id, "message": "Payout successful"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
