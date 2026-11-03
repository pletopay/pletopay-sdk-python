"""Resolves a beneficiary and sends a transfer with a deterministic idempotency key.

PLETOPAY_SECRET_KEY=sk_test_... python examples/payout.py
"""

import pletopay

client = pletopay.Pletopay()
payout_id = "PAYOUT-2026-0001"
beneficiary: pletopay.types.Beneficiary = {"bank_code": "058", "account_number": "0123456789"}

who = client.transfers.resolve_account(**beneficiary)
print("Paying", who.account_name)

try:
    transfer = client.transfers.create(
        amount=2500000,
        reference=payout_id,
        narration="Vendor payout",
        beneficiary=beneficiary,
        idempotency_key=f"payout-{payout_id}",  # the same key on every retry: never pays twice
    )
    print(transfer.id, transfer.status)  # processing until the outcome is known
except pletopay.ConflictError as error:
    if error.code == "duplicate_reference":
        print("Already sent:", client.transfers.retrieve_by_reference(payout_id).status)
    else:
        raise
except pletopay.InvalidRequestError as error:
    if error.code == "insufficient_funds":
        print("Top up first:", error.details)
    else:
        raise
