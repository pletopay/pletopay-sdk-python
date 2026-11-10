DEFAULT_BASE_URL = "https://api.pletopay.com"
DEFAULT_TIMEOUT_SECONDS = 30.0
# The calls that pay out inline answer only once the bank has (up to 75 s), so their default timeout is longer.
MONEY_OUT_OPERATIONS = frozenset({"createTransfer", "createRefund"})
MONEY_OUT_TIMEOUT_SECONDS = 90.0
DEFAULT_MAX_RETRIES = 2
ENV_SECRET_KEY = "PLETOPAY_SECRET_KEY"
ENV_API_URL = "PLETOPAY_API_URL"
ENV_WEBHOOK_SECRET = "PLETOPAY_WEBHOOK_SECRET"
