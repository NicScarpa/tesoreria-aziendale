import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models import (
    Company, User, UserCompany, UserCompanyStatus, UserRole,
    BankAccount, AccountStatus, AccountType,
    BankAccountBalance, BalanceSource,
    Category, Subcategory, Transaction, FlowDirection,
    TransactionStatus, TransactionType, CategorizationSource,
    CategorizationRule, RuleActionType,
    ExpectedTransaction, ExpectedTransactionType, ExpectedDocumentType,
    ExpectedTransactionStatus, ExpectedTransactionSource,
    Reconciliation, ReconciliationLine, ReconciliationLineType,
    ReconciliationType, ReconciliationStatus,
)

engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Nested savepoint per i test
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db_session) -> User:
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("Test1234!"),
        first_name="Test",
        last_name="User",
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def test_company(db_session) -> Company:
    company = Company(name="Test Company SRL", vat_number="99887766554", country="IT")
    db_session.add(company)
    db_session.flush()
    return company


@pytest.fixture()
def test_user_company(db_session, test_user, test_company) -> UserCompany:
    uc = UserCompany(
        user_id=test_user.id,
        company_id=test_company.id,
        role=UserRole.OWNER,
        status=UserCompanyStatus.ACTIVE,
    )
    db_session.add(uc)
    db_session.flush()
    return uc


@pytest.fixture()
def auth_headers(client, test_user, test_user_company) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Test1234!"})
    tokens = resp.json()
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "_refresh_token": tokens["refresh_token"],
    }


@pytest.fixture()
def test_bank_account(db_session, test_company) -> BankAccount:
    account = BankAccount(
        company_id=test_company.id,
        bank_connection_id=None,
        nickname="Conto Test",
        iban="IT60X0542811101000000123456",
        currency="EUR",
        current_balance=Decimal("10000.00"),
        available_balance=Decimal("9500.00"),
        status=AccountStatus.ACTIVE,
        account_type=AccountType.CHECKING,
        is_default=False,
        allow_balance_change=True,
        bank_name="Banco Test",
        bank_abi="05428",
        bank_cab="11101",
    )
    db_session.add(account)
    db_session.flush()
    return account


@pytest.fixture()
def test_bank_account_balance(db_session, test_bank_account, test_company) -> BankAccountBalance:
    balance = BankAccountBalance(
        bank_account_id=test_bank_account.id,
        company_id=test_company.id,
        balance_date=date.today(),
        current_balance=Decimal("10000.00"),
        available_balance=Decimal("9500.00"),
        source=BalanceSource.MANUAL,
    )
    db_session.add(balance)
    db_session.flush()
    return balance


# --- Module 5 fixtures ---

@pytest.fixture()
def test_category(db_session, test_company) -> Category:
    cat = Category(
        company_id=test_company.id,
        name="Fornitori",
        color="#ef4444",
        sort_order=0,
        is_system=False,
    )
    db_session.add(cat)
    db_session.flush()
    return cat


@pytest.fixture()
def test_system_category(db_session, test_company) -> Category:
    cat = Category(
        company_id=test_company.id,
        name="Stipendi",
        color="#22c55e",
        sort_order=0,
        is_system=True,
    )
    db_session.add(cat)
    db_session.flush()
    return cat


@pytest.fixture()
def test_subcategory(db_session, test_company, test_category) -> Subcategory:
    sub = Subcategory(
        category_id=test_category.id,
        company_id=test_company.id,
        name="Materie Prime",
        sort_order=0,
    )
    db_session.add(sub)
    db_session.flush()
    return sub


@pytest.fixture()
def test_transaction(db_session, test_company, test_bank_account, test_category) -> Transaction:
    tx = Transaction(
        company_id=test_company.id,
        bank_account_id=test_bank_account.id,
        amount=Decimal("-1500.00"),
        currency="EUR",
        direction=FlowDirection.OUTFLOW,
        transaction_date=date.today(),
        description="Pagamento fornitore test",
        transaction_type=TransactionType.CREDIT_TRANSFER,
        category_id=test_category.id,
        categorization_source=CategorizationSource.MANUAL,
        counterpart_name="Fornitore Test SRL",
        status=TransactionStatus.BOOKED,
        verified=False,
    )
    db_session.add(tx)
    db_session.flush()
    return tx


@pytest.fixture()
def test_categorization_rule(db_session, test_company, test_category) -> CategorizationRule:
    rule = CategorizationRule(
        company_id=test_company.id,
        name="Regola test fornitori",
        direction=FlowDirection.OUTFLOW,
        action_type=RuleActionType.SET_CATEGORY,
        category_id=test_category.id,
        conditions=[{"type": "KEYWORDS", "value": ["fornitore"]}],
        priority=10,
        is_active=True,
    )
    db_session.add(rule)
    db_session.flush()
    return rule


# --- Module 6 fixtures ---

@pytest.fixture()
def test_expected_transaction(db_session, test_company, test_bank_account) -> ExpectedTransaction:
    et = ExpectedTransaction(
        company_id=test_company.id,
        bank_account_id=test_bank_account.id,
        counterpart_name="Fornitore Test SRL",
        counterpart_iban="IT60X0542811101000000123456",
        type=ExpectedTransactionType.EXPECTED_OUTFLOW,
        expected_amount=Decimal("1500.00"),
        currency="EUR",
        due_date=date.today() + timedelta(days=5),
        description="Fattura acquisto materiali",
        reference_number="FT-2026/001",
        document_type=ExpectedDocumentType.PURCHASE_INVOICE,
        status=ExpectedTransactionStatus.OPEN,
        matched_amount=Decimal("0"),
        source=ExpectedTransactionSource.MANUAL,
    )
    db_session.add(et)
    db_session.flush()
    return et


@pytest.fixture()
def test_expected_inflow(db_session, test_company, test_bank_account) -> ExpectedTransaction:
    et = ExpectedTransaction(
        company_id=test_company.id,
        bank_account_id=test_bank_account.id,
        counterpart_name="Cliente Test SpA",
        type=ExpectedTransactionType.EXPECTED_INFLOW,
        expected_amount=Decimal("3000.00"),
        currency="EUR",
        due_date=date.today() + timedelta(days=3),
        description="Fattura vendita servizi",
        reference_number="FV-2026/010",
        document_type=ExpectedDocumentType.SALES_INVOICE,
        status=ExpectedTransactionStatus.OPEN,
        matched_amount=Decimal("0"),
        source=ExpectedTransactionSource.MANUAL,
    )
    db_session.add(et)
    db_session.flush()
    return et


@pytest.fixture()
def test_inflow_transaction(db_session, test_company, test_bank_account) -> Transaction:
    tx = Transaction(
        company_id=test_company.id,
        bank_account_id=test_bank_account.id,
        amount=Decimal("3000.00"),
        currency="EUR",
        direction=FlowDirection.INFLOW,
        transaction_date=date.today(),
        description="Pagamento Cliente Test SpA Rif. FV-2026/010",
        transaction_type=TransactionType.CREDIT_TRANSFER,
        counterpart_name="Cliente Test SpA",
        status=TransactionStatus.BOOKED,
        verified=False,
        reconciliation_status=ReconciliationStatus.UNRECONCILED,
    )
    db_session.add(tx)
    db_session.flush()
    return tx


@pytest.fixture()
def test_reconciliation(db_session, test_company, test_user, test_transaction, test_expected_transaction) -> Reconciliation:
    from datetime import datetime, timezone
    rec = Reconciliation(
        company_id=test_company.id,
        type=ReconciliationType.MANUAL.value,
        status="confirmed",
        reconciliation_date=datetime.now(timezone.utc),
        confirmed_by_user_id=test_user.id,
        confirmed_at=datetime.now(timezone.utc),
        matching_score=Decimal("100"),
    )
    db_session.add(rec)
    db_session.flush()

    line1 = ReconciliationLine(
        reconciliation_id=rec.id,
        transaction_id=test_transaction.id,
        matched_amount=Decimal("1500.00"),
        line_type=ReconciliationLineType.TRANSACTION_MATCH,
    )
    line2 = ReconciliationLine(
        reconciliation_id=rec.id,
        expected_transaction_id=test_expected_transaction.id,
        matched_amount=Decimal("1500.00"),
        line_type=ReconciliationLineType.EXPECTED_MATCH,
    )
    db_session.add_all([line1, line2])

    test_transaction.reconciliation_status = ReconciliationStatus.RECONCILED
    test_transaction.reconciliation_id = rec.id
    test_expected_transaction.matched_amount = Decimal("1500.00")
    test_expected_transaction.status = ExpectedTransactionStatus.MATCHED

    db_session.flush()
    return rec
