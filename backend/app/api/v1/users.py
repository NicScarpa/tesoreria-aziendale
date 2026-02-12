from fastapi import APIRouter

from app.core.deps import DB, CurrentUser
from app.models.enums import AuditAction
from app.schemas.user import UpdateUserRequest, UserCompanyResponse, UserMeResponse
from app.services import audit_service, user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: CurrentUser, db: DB):
    companies = user_service.get_user_companies(db, current_user.id)
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        companies=[
            UserCompanyResponse(
                id=uc.id,
                company_id=uc.company_id,
                company_name=uc.company.name,
                role=uc.role,
                status=uc.status,
            )
            for uc in companies
        ],
    )


@router.patch("/me", response_model=UserMeResponse)
def update_me(body: UpdateUserRequest, current_user: CurrentUser, db: DB):
    data = body.model_dump(exclude_unset=True)
    if not data:
        return get_me(current_user, db)
    user_service.update_user(db, current_user, data)
    audit_service.log_action(db, AuditAction.USER_UPDATE, user_id=current_user.id)
    return get_me(current_user, db)
