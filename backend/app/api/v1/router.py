from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.companies import router as companies_router
from app.api.v1.reconciliation_rules import router as reconciliation_rules_router
from app.api.v1.team import router as team_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.bank_accounts import router as bank_accounts_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.categories import router as categories_router
from app.api.v1.categorization_rules import router as categorization_rules_router
from app.api.v1.expected_transactions import router as expected_transactions_router
from app.api.v1.reconciliations import router as reconciliations_router
from app.api.v1.schedules import router as schedules_router
from app.api.v1.payments import router as payments_router
from app.api.v1.cash_flow import router as cash_flow_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.reports import router as reports_router
from app.api.v1.integrations import router as integrations_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(companies_router)
router.include_router(reconciliation_rules_router)
router.include_router(team_router)
router.include_router(notifications_router)
router.include_router(bank_accounts_router)
router.include_router(transactions_router)
router.include_router(categories_router)
router.include_router(categorization_rules_router)
router.include_router(expected_transactions_router)
router.include_router(reconciliations_router)
router.include_router(schedules_router)
router.include_router(payments_router)
router.include_router(cash_flow_router)
router.include_router(dashboard_router)
router.include_router(reports_router)
router.include_router(integrations_router)
