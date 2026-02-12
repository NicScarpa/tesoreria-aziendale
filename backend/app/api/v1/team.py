import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.team import (
    InviteMemberRequest,
    TeamMemberResponse,
    TeamMemberUser,
    TransferOwnershipRequest,
    UpdateMemberRequest,
)
from app.services import team_service

router = APIRouter(prefix="/company-users", tags=["team"])


def _build_member_response(uc) -> TeamMemberResponse:
    invited_by_name = None
    return TeamMemberResponse(
        id=uc.id,
        user=TeamMemberUser.model_validate(uc.user),
        role=uc.role,
        status=uc.status,
        invited_at=uc.invited_at,
        joined_at=uc.joined_at,
        invited_by_name=invited_by_name,
        created_at=uc.created_at,
    )


@router.get("", response_model=list[TeamMemberResponse])
def list_members(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    members = team_service.list_members(db, company.id)
    return [_build_member_response(m) for m in members]


@router.post("/invite", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    body: InviteMemberRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    uc = team_service.invite_member(db, company.id, str(body.email), body.role, current_user)
    return _build_member_response(uc)


@router.patch("/{uc_id}", response_model=TeamMemberResponse)
def update_member(
    uc_id: uuid.UUID,
    body: UpdateMemberRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, uc_current = company_data

    result_uc = None
    if body.role is not None:
        result_uc = team_service.update_member_role(db, uc_id, company.id, body.role, uc_current.role)
    if body.status is not None:
        result_uc = team_service.update_member_status(db, uc_id, company.id, body.status, current_user.id)
    if result_uc is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nessuna modifica specificata")
    return _build_member_response(result_uc)


@router.delete("/{uc_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    uc_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    team_service.remove_member(db, uc_id, company.id, current_user.id)


@router.post("/transfer-ownership", status_code=status.HTTP_200_OK)
def transfer_ownership(
    body: TransferOwnershipRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.OWNER))],
    db: DB,
):
    company, _uc = company_data
    team_service.transfer_ownership(db, company.id, current_user, body.target_user_id, body.password)
    return {"detail": "Ownership trasferito con successo"}
