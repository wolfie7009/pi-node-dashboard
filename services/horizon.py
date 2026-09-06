import requests


HORIZON_URL = "http://localhost:31401"


def get_wallet_data(wallet_address):
    account_url = (
        f"{HORIZON_URL}/accounts/{wallet_address}"
    )

    response = requests.get(
        account_url,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    free_balance = 0.0

    for balance in data.get("balances", []):
        if balance.get("asset_type") == "native":
            free_balance = float(
                balance.get("balance", 0)
            )
            break

    claimable_url = (
        f"{HORIZON_URL}/claimable_balances"
        f"?claimant={wallet_address}"
        f"&limit=200"
    )

    response = requests.get(
        claimable_url,
        timeout=15,
    )

    response.raise_for_status()

    claimable_data = response.json()

    records = (
        claimable_data
        .get("_embedded", {})
        .get("records", [])
    )

    locked_balance = 0.0

    for record in records:
        if record.get("asset") == "native":
            locked_balance += float(
                record.get("amount", 0)
            )

    return {
        "free": free_balance,
        "locked": locked_balance,
        "total": free_balance + locked_balance,
    }

def get_wallet_details(wallet_address):
    # --------------------------------------------------
    # Account / vrije balance
    # --------------------------------------------------

    account_url = (
        f"{HORIZON_URL}/accounts/{wallet_address}"
    )

    response = requests.get(
        account_url,
        timeout=15,
    )
    response.raise_for_status()

    account_data = response.json()

    free_balance = 0.0

    for balance in account_data.get(
        "balances",
        [],
    ):
        if balance.get("asset_type") == "native":
            free_balance = float(
                balance.get(
                    "balance",
                    0,
                )
            )
            break

    # --------------------------------------------------
    # Claimable balances
    # --------------------------------------------------

    claimable_url = (
        f"{HORIZON_URL}/claimable_balances"
        f"?claimant={wallet_address}"
        f"&limit=200"
    )

    response = requests.get(
        claimable_url,
        timeout=15,
    )
    response.raise_for_status()

    claimable_data = response.json()

    claimable_records = (
        claimable_data
        .get("_embedded", {})
        .get("records", [])
    )

    # --------------------------------------------------
    # Laatste transacties
    # order=desc = nieuwste eerst
    # --------------------------------------------------

    transactions_url = (
        f"{HORIZON_URL}/accounts/"
        f"{wallet_address}/transactions"
        f"?limit=10&order=desc"
    )

    response = requests.get(
        transactions_url,
        timeout=15,
    )
    response.raise_for_status()

    transaction_data = response.json()

    transactions = (
        transaction_data
        .get("_embedded", {})
        .get("records", [])
    )

    return {
        "free": free_balance,
        "claimables": claimable_records,
        "transactions": transactions,
    }

def get_transaction_details(transaction_hash):
    # --------------------------------------------------
    # Transactie
    # --------------------------------------------------

    transaction_url = (
        f"{HORIZON_URL}/transactions/"
        f"{transaction_hash}"
    )

    response = requests.get(
        transaction_url,
        timeout=15,
    )

    response.raise_for_status()

    transaction = response.json()

    # --------------------------------------------------
    # Operations
    # --------------------------------------------------

    operations_url = (
        f"{HORIZON_URL}/transactions/"
        f"{transaction_hash}/operations"
        f"?limit=200&order=asc"
    )

    response = requests.get(
        operations_url,
        timeout=15,
    )

    response.raise_for_status()

    operations_data = response.json()

    operations = (
        operations_data
        .get("_embedded", {})
        .get("records", [])
    )

    # --------------------------------------------------
    # Effects per operation
    # --------------------------------------------------

    for operation in operations:
        operation_id = operation.get("id")

        if not operation_id:
            operation["effects"] = []
            continue

        try:
            operation["effects"] = (
                get_operation_effects(
                    operation_id
                )
            )

        except Exception:
            operation["effects"] = []

    return {
        "transaction": transaction,
        "operations": operations,
    }


def get_operation_effects(operation_id):
    effects_url = (
        f"{HORIZON_URL}/operations/"
        f"{operation_id}/effects"
        f"?limit=200&order=asc"
    )

    response = requests.get(
        effects_url,
        timeout=15,
    )

    response.raise_for_status()

    effects_data = response.json()

    return (
        effects_data
        .get("_embedded", {})
        .get("records", [])
    )