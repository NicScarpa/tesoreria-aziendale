"""
Package generatori file bancari per il modulo Pagamenti.

Produce file compatibili con i sistemi bancari italiani:
- SEPA Credit Transfer (pain.001.001.03)
- RiBa CBI (Ricevuta Bancaria)
- SDD SEPA Direct Debit (pain.008.001.02)
- F24 telematico
"""

from app.services.generators.sepa_xml_generator import generate_sepa_ct
from app.services.generators.riba_generator import generate_riba
from app.services.generators.sdd_xml_generator import generate_sdd
from app.services.generators.f24_generator import generate_f24
from app.services.generators.iban_validator import validate_iban

__all__ = [
    "generate_sepa_ct",
    "generate_riba",
    "generate_sdd",
    "generate_f24",
    "validate_iban",
]
