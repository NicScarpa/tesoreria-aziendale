import csv
import io
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.import_batch import ImportBatch
from app.models.enums import (
    FlowDirection, TransactionStatus, TransactionType,
    BatchStatus, CategorizationSource,
)
from app.schemas.transaction import CSVMappingRequest
from app.services import categorization_rule_service


def _detect_encoding(file_bytes: bytes) -> str:
    """Auto-detect encoding: try UTF-8, then fall back to latin-1."""
    for enc in ["utf-8-sig", "utf-8", "iso-8859-1", "windows-1252"]:
        try:
            file_bytes.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def _parse_amount(value: str, decimal_separator: str = ",") -> Decimal:
    """Parse amount string with configurable decimal separator."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Importo vuoto")

    # Remove thousands separator (opposite of decimal separator)
    if decimal_separator == ",":
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"Importo non valido: {value}")


def _parse_date(value: str, date_format: str = "%d/%m/%Y") -> date:
    """Parse date string with configurable format."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Data vuota")
    try:
        return datetime.strptime(cleaned, date_format).date()
    except ValueError:
        raise ValueError(f"Data non valida: {value} (formato atteso: {date_format})")


async def import_csv(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    bank_account_id: uuid.UUID,
    file: UploadFile,
    mapping: CSVMappingRequest,
) -> ImportBatch:
    # Read file
    file_bytes = await file.read()
    encoding = _detect_encoding(file_bytes)
    content = file_bytes.decode(encoding)

    # Create batch
    batch = ImportBatch(
        company_id=company_id,
        bank_account_id=bank_account_id,
        user_id=user_id,
        format="csv",
        filename=file.filename,
        status=BatchStatus.PROCESSING,
        started_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()

    # Parse CSV
    reader = csv.DictReader(io.StringIO(content), delimiter=mapping.csv_separator)

    rows = list(reader)
    batch.total_records = len(rows)
    errors = []

    for i, row in enumerate(rows):
        row_num = i + 2  # +2 for 1-indexed + header row
        try:
            # Parse amount
            amount_str = row.get(mapping.amount_column, "").strip()
            if not amount_str:
                errors.append({"row": row_num, "error": "Importo mancante"})
                batch.error_records += 1
                continue

            amount = _parse_amount(amount_str, mapping.decimal_separator)

            # Parse date
            date_str = row.get(mapping.date_column, "").strip()
            if not date_str:
                errors.append({"row": row_num, "error": "Data mancante"})
                batch.error_records += 1
                continue

            tx_date = _parse_date(date_str, mapping.date_format)

            # Description
            description = row.get(mapping.description_column, "").strip() if mapping.description_column else None

            # Determine direction from sign
            direction = FlowDirection.INFLOW if amount >= 0 else FlowDirection.OUTFLOW

            # Check for duplicates (same bank_account + date + amount + description)
            existing = (
                db.query(Transaction)
                .filter(
                    Transaction.bank_account_id == bank_account_id,
                    Transaction.transaction_date == tx_date,
                    Transaction.amount == amount,
                    Transaction.description == description,
                )
                .first()
            )
            if existing:
                batch.skipped_records += 1
                continue

            tx = Transaction(
                company_id=company_id,
                bank_account_id=bank_account_id,
                amount=amount,
                currency="EUR",
                direction=direction,
                transaction_date=tx_date,
                description=description,
                transaction_type=TransactionType.OTHER,
                status=TransactionStatus.BOOKED,
                import_batch_id=batch.id,
            )
            db.add(tx)
            db.flush()

            # Try auto-categorization
            categorization_rule_service.apply_rules(db, tx)

            batch.imported_records += 1

        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})
            batch.error_records += 1

    # Update batch status
    batch.errors = errors
    batch.completed_at = datetime.now(timezone.utc)
    if batch.error_records == batch.total_records:
        batch.status = BatchStatus.FAILED
    elif batch.error_records > 0:
        batch.status = BatchStatus.PARTIAL
    else:
        batch.status = BatchStatus.COMPLETED

    db.commit()
    db.refresh(batch)
    return batch


def get_batch(db: Session, batch_id: uuid.UUID, company_id: uuid.UUID) -> ImportBatch:
    batch = (
        db.query(ImportBatch)
        .filter(ImportBatch.id == batch_id, ImportBatch.company_id == company_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch non trovato")
    return batch
