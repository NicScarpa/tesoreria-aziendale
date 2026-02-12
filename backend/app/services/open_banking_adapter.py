"""Open Banking adapter layer.

Provides an abstract interface for Open Banking providers
with a mock implementation for development.
"""
import logging
import random
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

ITALIAN_BANKS = [
    {"id": "UNICREDIT_UNCRITMM", "name": "UniCredit", "bic": "UNCRITMM", "logo": "https://cdn.nordigen.com/ais/UNICREDIT_UNCRITMM.png"},
    {"id": "INTESA_BCITITMM", "name": "Intesa Sanpaolo", "bic": "BCITITMM", "logo": "https://cdn.nordigen.com/ais/INTESA_BCITITMM.png"},
    {"id": "BPM_BAPPIT21", "name": "Banco BPM", "bic": "BAPPIT21", "logo": "https://cdn.nordigen.com/ais/BPM_BAPPIT21.png"},
    {"id": "BPER_BPMOIT22", "name": "BPER Banca", "bic": "BPMOIT22", "logo": "https://cdn.nordigen.com/ais/BPER_BPMOIT22.png"},
    {"id": "CREDEM_BACRIT21", "name": "Credem", "bic": "BACRIT21", "logo": "https://cdn.nordigen.com/ais/CREDEM_BACRIT21.png"},
    {"id": "MPS_PASCITMM", "name": "Banca Monte dei Paschi", "bic": "PASCITMM", "logo": "https://cdn.nordigen.com/ais/MPS_PASCITMM.png"},
    {"id": "FINECO_FEBIITM2", "name": "FinecoBank", "bic": "FEBIITM2", "logo": "https://cdn.nordigen.com/ais/FINECO_FEBIITM2.png"},
    {"id": "MEDIOLANUM_MEDBITM1", "name": "Banca Mediolanum", "bic": "MEDBITM1", "logo": "https://cdn.nordigen.com/ais/MEDIOLANUM_MEDBITM1.png"},
    {"id": "POPSO_POSOIT22", "name": "Banca Popolare di Sondrio", "bic": "POSOIT22", "logo": "https://cdn.nordigen.com/ais/POPSO_POSOIT22.png"},
    {"id": "CREVAL_BPCVIT2S", "name": "Credito Valtellinese", "bic": "BPCVIT2S", "logo": "https://cdn.nordigen.com/ais/CREVAL_BPCVIT2S.png"},
]


class OpenBankingAdapter(ABC):
    @abstractmethod
    def get_institutions(self, country: str = "IT") -> list[dict]:
        ...

    @abstractmethod
    def create_connection(self, institution_id: str, redirect_url: str) -> dict:
        ...

    @abstractmethod
    def handle_callback(self, code: str, connection_id: str) -> dict:
        ...

    @abstractmethod
    def get_transactions(self, account_id: str, date_from: date, date_to: date) -> list[dict]:
        ...

    @abstractmethod
    def get_balance(self, account_id: str) -> dict:
        ...

    @abstractmethod
    def revoke_connection(self, connection_id: str) -> bool:
        ...


class MockOpenBankingAdapter(OpenBankingAdapter):
    """Mock adapter for development and testing."""

    def get_institutions(self, country: str = "IT") -> list[dict]:
        return [b for b in ITALIAN_BANKS if country == "IT"]

    def create_connection(self, institution_id: str, redirect_url: str) -> dict:
        return {
            "connection_id": f"mock-conn-{uuid.uuid4().hex[:8]}",
            "consent_id": f"mock-consent-{uuid.uuid4().hex[:8]}",
            "authorization_url": f"{redirect_url}?ref=mock-{uuid.uuid4().hex[:8]}",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        }

    def handle_callback(self, code: str, connection_id: str) -> dict:
        return {
            "status": "active",
            "account_id": f"mock-acct-{uuid.uuid4().hex[:8]}",
            "iban": f"IT60X0542811101000000{random.randint(100000, 999999)}",
        }

    def get_transactions(self, account_id: str, date_from: date, date_to: date) -> list[dict]:
        counterparts = [
            "ABC SRL", "XYZ Trading", "Enel Energia", "Mario Rossi",
            "Tecnoparts SRL", "Studio Verdi", "Telecom Italia",
        ]
        descriptions = [
            "Bonifico in entrata", "Pagamento fattura", "Addebito SDD",
            "Stipendio", "Commissione bancaria", "Accredito",
        ]
        txs = []
        num_days = (date_to - date_from).days
        num_txs = min(max(num_days // 2, 3), 30)

        for i in range(num_txs):
            is_credit = random.choice([True, False])
            amount = Decimal(str(random.uniform(100, 15000))).quantize(Decimal("0.01"))
            tx_date = date_from + timedelta(days=random.randint(0, max(num_days - 1, 0)))

            txs.append({
                "reference": f"REF-{uuid.uuid4().hex[:12]}",
                "amount": amount,
                "direction": "inflow" if is_credit else "outflow",
                "date": tx_date.isoformat(),
                "description": random.choice(descriptions),
                "counterpart_name": random.choice(counterparts),
                "currency": "EUR",
            })

        return txs

    def get_balance(self, account_id: str) -> dict:
        return {
            "current": Decimal(str(random.uniform(10000, 200000))).quantize(Decimal("0.01")),
            "available": Decimal(str(random.uniform(10000, 200000))).quantize(Decimal("0.01")),
            "currency": "EUR",
            "date": datetime.now(timezone.utc).isoformat(),
        }

    def revoke_connection(self, connection_id: str) -> bool:
        return True


class NordigenAdapter(OpenBankingAdapter):
    """GoCardless/Nordigen adapter stub."""

    def __init__(self, secret_id: str = "", secret_key: str = ""):
        self.secret_id = secret_id
        self.secret_key = secret_key

    def get_institutions(self, country: str = "IT") -> list[dict]:
        raise NotImplementedError("Nordigen adapter not yet implemented")

    def create_connection(self, institution_id: str, redirect_url: str) -> dict:
        raise NotImplementedError("Nordigen adapter not yet implemented")

    def handle_callback(self, code: str, connection_id: str) -> dict:
        raise NotImplementedError("Nordigen adapter not yet implemented")

    def get_transactions(self, account_id: str, date_from: date, date_to: date) -> list[dict]:
        raise NotImplementedError("Nordigen adapter not yet implemented")

    def get_balance(self, account_id: str) -> dict:
        raise NotImplementedError("Nordigen adapter not yet implemented")

    def revoke_connection(self, connection_id: str) -> bool:
        raise NotImplementedError("Nordigen adapter not yet implemented")


class OpenBankingAdapterFactory:
    @staticmethod
    def get(provider: str, credentials: dict | None = None) -> OpenBankingAdapter:
        if provider == "nordigen_gocardless" and credentials:
            return NordigenAdapter(
                secret_id=credentials.get("secret_id", ""),
                secret_key=credentials.get("secret_key", ""),
            )
        return MockOpenBankingAdapter()
