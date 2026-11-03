"""Creates a checkout session and prints the hosted URL and the popup token.

PLETOPAY_SECRET_KEY=sk_test_... python examples/create_checkout_session.py
"""

import time

import pletopay

client = pletopay.Pletopay()
order_id = f"ORDER-{int(time.time())}"

session = client.checkout.sessions.create(
    amount=250000,  # ₦2,500.00 in kobo
    reference=order_id,
    description="Two tickets",
    customer_email="ada@example.com",
    success_url="https://shop.example.com/thanks",
    cancel_url="https://shop.example.com/cart",
    expires_in=1800,
    idempotency_key=f"checkout-{order_id}",
)

print("Redirect the customer to:", session.url)
print("Or open the popup with token:", session.token)
print('Later, confirm on the server with client.checkout.sessions.retrieve(session.id).status == "complete"')
