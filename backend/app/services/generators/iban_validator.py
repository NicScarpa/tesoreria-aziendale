"""
Validazione IBAN conforme a ISO 13616 con algoritmo MOD-97.

Supporta i formati IBAN per: IT, DE, FR, ES, NL, AT, BE.
"""

import re

# Lunghezze IBAN per paese (ISO 13616)
COUNTRY_IBAN_LENGTHS: dict[str, int] = {
    "IT": 27,
    "DE": 22,
    "FR": 27,
    "ES": 24,
    "NL": 18,
    "AT": 20,
    "BE": 16,
}

# Paesi supportati come set per lookup rapido
SUPPORTED_COUNTRIES: set[str] = set(COUNTRY_IBAN_LENGTHS.keys())


def validate_iban(iban: str) -> tuple[bool, str]:
    """
    Valida un codice IBAN.

    Esegue:
    1. Pulizia (strip spazi, uppercase)
    2. Verifica formato base (solo alfanumerici)
    3. Verifica lunghezza specifica per paese
    4. Controllo MOD-97 per ISO 13616

    Args:
        iban: Stringa IBAN da validare (con o senza spazi).

    Returns:
        Tupla (valido, messaggio_errore). Se valido, messaggio_errore è stringa vuota.
    """
    if not iban:
        return False, "IBAN vuoto"

    # Pulizia: rimuovi spazi e converti in maiuscolo
    cleaned = iban.replace(" ", "").upper()

    # Verifica che contenga solo caratteri alfanumerici
    if not re.match(r"^[A-Z0-9]+$", cleaned):
        return False, "IBAN contiene caratteri non validi"

    # Verifica lunghezza minima
    if len(cleaned) < 5:
        return False, "IBAN troppo corto"

    # Estrai codice paese (prime 2 lettere)
    country_code = cleaned[:2]

    if not country_code.isalpha():
        return False, f"Codice paese non valido: {country_code}"

    # Verifica che il paese sia supportato
    if country_code not in SUPPORTED_COUNTRIES:
        return False, (
            f"Paese '{country_code}' non supportato. "
            f"Paesi supportati: {', '.join(sorted(SUPPORTED_COUNTRIES))}"
        )

    # Verifica lunghezza specifica per paese
    expected_length = COUNTRY_IBAN_LENGTHS[country_code]
    if len(cleaned) != expected_length:
        return False, (
            f"Lunghezza IBAN non valida per {country_code}: "
            f"attesi {expected_length} caratteri, trovati {len(cleaned)}"
        )

    # Verifica check digits (posizioni 2-3 devono essere numeriche)
    check_digits = cleaned[2:4]
    if not check_digits.isdigit():
        return False, "Check digits non numerici"

    # Controllo MOD-97 (ISO 13616)
    if not _mod97_check(cleaned):
        return False, "Controllo MOD-97 fallito: IBAN non valido"

    return True, ""


def _mod97_check(iban: str) -> bool:
    """
    Esegue il controllo MOD-97 su un IBAN pulito.

    Algoritmo ISO 13616:
    1. Sposta i primi 4 caratteri alla fine
    2. Converti lettere in numeri (A=10, B=11, ..., Z=35)
    3. Il numero risultante modulo 97 deve essere 1
    """
    # Sposta i primi 4 caratteri alla fine
    rearranged = iban[4:] + iban[:4]

    # Converti lettere in numeri
    numeric_str = ""
    for char in rearranged:
        if char.isdigit():
            numeric_str += char
        else:
            # A=10, B=11, ..., Z=35
            numeric_str += str(ord(char) - ord("A") + 10)

    # Calcola modulo 97
    return int(numeric_str) % 97 == 1
