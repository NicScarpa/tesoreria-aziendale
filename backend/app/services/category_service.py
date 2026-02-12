import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.subcategory import Subcategory
from app.models.transaction import Transaction
from app.models.categorization_rule import CategorizationRule
from app.schemas.category import (
    CreateCategoryRequest, UpdateCategoryRequest,
    CreateSubcategoryRequest, UpdateSubcategoryRequest,
)


def list_categories(db: Session, company_id: uuid.UUID) -> list[Category]:
    return (
        db.query(Category)
        .filter(Category.company_id == company_id)
        .order_by(Category.sort_order, Category.name)
        .all()
    )


def get_category(db: Session, category_id: uuid.UUID, company_id: uuid.UUID) -> Category:
    cat = (
        db.query(Category)
        .filter(Category.id == category_id, Category.company_id == company_id)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria non trovata")
    return cat


def create_category(db: Session, company_id: uuid.UUID, data: CreateCategoryRequest) -> Category:
    existing = (
        db.query(Category)
        .filter(Category.company_id == company_id, Category.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esiste già una categoria con questo nome",
        )
    cat = Category(
        company_id=company_id,
        name=data.name,
        color=data.color,
        sort_order=data.sort_order,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(
    db: Session, category_id: uuid.UUID, company_id: uuid.UUID, data: UpdateCategoryRequest
) -> Category:
    cat = get_category(db, category_id, company_id)
    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != cat.name:
        existing = (
            db.query(Category)
            .filter(
                Category.company_id == company_id,
                Category.name == update_data["name"],
                Category.id != category_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esiste già una categoria con questo nome",
            )

    for key, value in update_data.items():
        setattr(cat, key, value)

    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, category_id: uuid.UUID, company_id: uuid.UUID) -> None:
    cat = get_category(db, category_id, company_id)
    if cat.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le categorie di sistema non possono essere eliminate",
        )

    # Nullify transactions referencing this category
    db.query(Transaction).filter(Transaction.category_id == category_id).update(
        {"category_id": None, "subcategory_id": None, "categorization_source": None}
    )

    # Delete categorization rules referencing this category
    db.query(CategorizationRule).filter(CategorizationRule.category_id == category_id).delete()

    db.delete(cat)
    db.commit()


# --- Subcategory ---

def create_subcategory(
    db: Session, category_id: uuid.UUID, company_id: uuid.UUID, data: CreateSubcategoryRequest
) -> Subcategory:
    cat = get_category(db, category_id, company_id)

    existing = (
        db.query(Subcategory)
        .filter(Subcategory.category_id == category_id, Subcategory.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esiste già una sottocategoria con questo nome",
        )

    sub = Subcategory(
        category_id=cat.id,
        company_id=company_id,
        name=data.name,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def update_subcategory(
    db: Session, subcategory_id: uuid.UUID, company_id: uuid.UUID, data: UpdateSubcategoryRequest
) -> Subcategory:
    sub = (
        db.query(Subcategory)
        .filter(Subcategory.id == subcategory_id, Subcategory.company_id == company_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sottocategoria non trovata")

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != sub.name:
        existing = (
            db.query(Subcategory)
            .filter(
                Subcategory.category_id == sub.category_id,
                Subcategory.name == update_data["name"],
                Subcategory.id != subcategory_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esiste già una sottocategoria con questo nome",
            )

    for key, value in update_data.items():
        setattr(sub, key, value)

    db.commit()
    db.refresh(sub)
    return sub


def delete_subcategory(
    db: Session, subcategory_id: uuid.UUID, company_id: uuid.UUID, mode: str = "mark_uncategorised"
) -> None:
    sub = (
        db.query(Subcategory)
        .filter(Subcategory.id == subcategory_id, Subcategory.company_id == company_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sottocategoria non trovata")

    if mode == "parent_category":
        # Move transactions to parent category (keep category_id, clear subcategory_id)
        db.query(Transaction).filter(Transaction.subcategory_id == subcategory_id).update(
            {"subcategory_id": None}
        )
    else:
        # Mark as uncategorised
        db.query(Transaction).filter(Transaction.subcategory_id == subcategory_id).update(
            {"subcategory_id": None}
        )

    db.delete(sub)
    db.commit()
