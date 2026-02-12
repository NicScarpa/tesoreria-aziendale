/**
 * Formatta un IBAN in gruppi di 4 caratteri.
 * IT60 X054 2811 1010 0000 0123 456
 */
export function formatIBAN(iban: string): string {
  const cleaned = iban.replace(/\s/g, "").toUpperCase();
  return cleaned.replace(/(.{4})/g, "$1 ").trim();
}

/**
 * Maschera un IBAN mostrando solo country code e ultime 4 cifre.
 * IT60X0542811101000000123456 → IT** **** **** **** **** **3 456
 */
export function maskIBAN(iban: string): string {
  const cleaned = iban.replace(/\s/g, "").toUpperCase();
  if (cleaned.length < 8) return cleaned;
  const visible = cleaned.slice(0, 2) + "** **** **** **** **** **" + cleaned.slice(-4);
  return visible;
}

/**
 * Valida un IBAN con il check digit modulo 97.
 */
export function validateIBAN(iban: string): boolean {
  const cleaned = iban.replace(/\s/g, "").toUpperCase();
  if (!/^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$/.test(cleaned)) return false;
  if (cleaned.startsWith("IT") && cleaned.length !== 27) return false;
  const rearranged = cleaned.slice(4) + cleaned.slice(0, 4);
  let numeric = "";
  for (const ch of rearranged) {
    if (/\d/.test(ch)) {
      numeric += ch;
    } else {
      numeric += (ch.charCodeAt(0) - 55).toString();
    }
  }
  return BigInt(numeric) % BigInt(97) === BigInt(1);
}

/**
 * Estrae informazioni da un IBAN italiano.
 */
export function extractIBANInfo(iban: string): {
  country: string;
  checkDigits: string;
  cin: string;
  abi: string;
  cab: string;
  accountNumber: string;
} | null {
  const cleaned = iban.replace(/\s/g, "").toUpperCase();
  if (!cleaned.startsWith("IT") || cleaned.length !== 27) return null;
  return {
    country: cleaned.slice(0, 2),
    checkDigits: cleaned.slice(2, 4),
    cin: cleaned.slice(4, 5),
    abi: cleaned.slice(5, 10),
    cab: cleaned.slice(10, 15),
    accountNumber: cleaned.slice(15, 27),
  };
}
