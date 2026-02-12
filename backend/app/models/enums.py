import enum


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

    def __ge__(self, other: "UserRole") -> bool:
        order = {UserRole.VIEWER: 0, UserRole.EDITOR: 1, UserRole.ADMIN: 2, UserRole.OWNER: 3}
        return order[self] >= order[other]

    def __gt__(self, other: "UserRole") -> bool:
        order = {UserRole.VIEWER: 0, UserRole.EDITOR: 1, UserRole.ADMIN: 2, UserRole.OWNER: 3}
        return order[self] > order[other]

    def __le__(self, other: "UserRole") -> bool:
        return not self.__gt__(other)

    def __lt__(self, other: "UserRole") -> bool:
        return not self.__ge__(other)


class UserCompanyStatus(str, enum.Enum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    REMOVED = "removed"


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGE = "password_change"
    USER_UPDATE = "user_update"
    COMPANY_UPDATE = "company_update"
    USER_REGISTER = "user_register"
    ROLE_CHANGED = "role_changed"
    USER_INVITED = "user_invited"
    USER_REMOVED = "user_removed"


class ConsentStatus(str, enum.Enum):
    ACTIVE = "active"
    AUTHORIZED = "authorized"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    DISABLED = "disabled"
    ERROR = "error"


class ConsentPurpose(str, enum.Enum):
    AISP = "aisp"       # Account Information
    PISP = "pisp"       # Payment Initiation
    BOTH = "both"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    HIDDEN = "hidden"
    CLOSED = "closed"
    BLOCKED = "blocked"


class AccountType(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    OTHER = "other"


class BalanceSource(str, enum.Enum):
    MANUAL = "manual"
    OPEN_BANKING = "open_banking"
    IMPORT = "import"
    CALCULATED = "calculated"


class AccessLevel(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class NotificationType(str, enum.Enum):
    LOW_BALANCE = "low_balance"
    CRITICAL_BALANCE = "critical_balance"
    SYNC_COMPLETE = "sync_complete"
    SYNC_ERROR = "sync_error"
    RECONCILIATION_COMPLETE = "reconciliation_complete"
    PAYMENT_DUE = "payment_due"
    USER_INVITED = "user_invited"
    ROLE_CHANGED = "role_changed"


class FlowDirection(str, enum.Enum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    BOOKED = "booked"
    REJECTED = "rejected"


class TransactionType(str, enum.Enum):
    CREDIT_TRANSFER = "credit_transfer"
    DIRECT_DEBIT = "direct_debit"
    CARD_PAYMENT = "card_payment"
    CASH = "cash"
    FEE = "fee"
    INTEREST = "interest"
    TAX = "tax"
    OTHER = "other"


class CategorizationSource(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    RULE = "rule"
    IMPORT = "import"


class RuleActionType(str, enum.Enum):
    SET_CATEGORY = "set_category"


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


# --- Module 6: Reconciliation ---

class ReconciliationStatus(str, enum.Enum):
    UNRECONCILED = "unreconciled"
    PARTIALLY_RECONCILED = "partially_reconciled"
    RECONCILED = "reconciled"


class ExpectedTransactionType(str, enum.Enum):
    EXPECTED_INFLOW = "expected_inflow"
    EXPECTED_OUTFLOW = "expected_outflow"


class ExpectedDocumentType(str, enum.Enum):
    SALES_INVOICE = "sales_invoice"
    PURCHASE_INVOICE = "purchase_invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    SALARY = "salary"
    TAX = "tax"
    OTHER = "other"


class ExpectedTransactionStatus(str, enum.Enum):
    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    MATCHED = "matched"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ExpectedTransactionSource(str, enum.Enum):
    MANUAL = "manual"
    INVOICE_IMPORT = "invoice_import"
    SCHEDULE = "schedule"
    SDI_SYNC = "sdi_sync"


class ReconciliationType(str, enum.Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SUGGESTED = "suggested"


class ReconciliationLineType(str, enum.Enum):
    TRANSACTION_MATCH = "transaction_match"
    EXPECTED_MATCH = "expected_match"
    ADJUSTMENT = "adjustment"


class ReconciliationRuleMatchType(str, enum.Enum):
    EXACT_AMOUNT = "exact_amount"
    AMOUNT_TOLERANCE = "amount_tolerance"
    REFERENCE = "reference"
    COUNTERPART = "counterpart"
    COMBINED = "combined"


class ReconciliationRuleAction(str, enum.Enum):
    AUTO_RECONCILE = "auto_reconcile"
    SUGGEST = "suggest"


# --- Module 7: Schedule Management ---

class ScheduleType(str, enum.Enum):
    ATTIVA = "attiva"      # da incassare
    PASSIVA = "passiva"    # da pagare


class ScheduleStatus(str, enum.Enum):
    APERTA = "aperta"
    PARZIALMENTE_PAGATA = "parzialmente_pagata"
    PAGATA = "pagata"
    SCADUTA = "scaduta"
    ANNULLATA = "annullata"


class DocumentType(str, enum.Enum):
    FATTURA_VENDITA = "fattura_vendita"
    FATTURA_ACQUISTO = "fattura_acquisto"
    NOTA_CREDITO = "nota_credito"
    NOTA_DEBITO = "nota_debito"
    STIPENDIO = "stipendio"
    TASSA_F24 = "tassa_f24"
    CONTRIBUTO = "contributo"
    AFFITTO = "affitto"
    UTENZA = "utenza"
    RATA_PRESTITO = "rata_prestito"
    ALTRO = "altro"


class SchedulePriority(str, enum.Enum):
    BASSA = "bassa"
    NORMALE = "normale"
    ALTA = "alta"
    URGENTE = "urgente"


class RecurrenceType(str, enum.Enum):
    SETTIMANALE = "settimanale"
    MENSILE = "mensile"
    BIMESTRALE = "bimestrale"
    TRIMESTRALE = "trimestrale"
    SEMESTRALE = "semestrale"
    ANNUALE = "annuale"


class ScheduleSource(str, enum.Enum):
    MANUALE = "manuale"
    IMPORT_CSV = "import_csv"
    IMPORT_FATTURE_SDI = "import_fatture_sdi"
    RICORRENZA_AUTO = "ricorrenza_auto"


class PaymentMethod(str, enum.Enum):
    BONIFICO = "bonifico"
    RI_BA = "ri_ba"
    SDD = "sdd"
    CARTA = "carta"
    CONTANTI = "contanti"
    F24 = "f24"
    ALTRO = "altro"


class ReminderType(str, enum.Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    ENTRAMBI = "entrambi"


# --- Module 8: Payments ---

class PaymentOrderType(str, enum.Enum):
    SEPA_CREDIT_TRANSFER = "sepa_credit_transfer"
    RIBA = "riba"
    SDD = "sdd"
    F24 = "f24"
    BONIFICO_ESTERO = "bonifico_estero"


class PaymentOrderStatus(str, enum.Enum):
    BOZZA = "bozza"
    DA_APPROVARE = "da_approvare"
    APPROVATA = "approvata"
    FILE_GENERATO = "file_generato"
    INVIATA_BANCA = "inviata_banca"
    ESEGUITA = "eseguita"
    RIFIUTATA = "rifiutata"
    ANNULLATA = "annullata"


class PaymentPriority(str, enum.Enum):
    NORMALE = "normale"
    ALTA = "alta"
    URGENTE = "urgente"


class PaymentLineStatus(str, enum.Enum):
    INCLUSA = "inclusa"
    ESEGUITA = "eseguita"
    RIFIUTATA = "rifiutata"
    ESCLUSA = "esclusa"


class ApprovalAction(str, enum.Enum):
    APPROVATA = "approvata"
    RIFIUTATA = "rifiutata"
    RICHIESTA_MODIFICA = "richiesta_modifica"


class SDDMandateType(str, enum.Enum):
    CORE = "core"
    B2B = "b2b"


class SDDSequenceType(str, enum.Enum):
    FRST = "frst"
    RCUR = "rcur"
    FNAL = "fnal"
    OOFF = "ooff"


class F24SectionType(str, enum.Enum):
    ERARIO = "erario"
    INPS = "inps"
    REGIONI = "regioni"
    IMU_ALTRI_ENTI = "imu_altri_enti"


# --- Module 9: Cash Flow ---

class ForecastStatus(str, enum.Enum):
    BOZZA = "bozza"
    ATTIVA = "attiva"
    ARCHIVIATA = "archiviata"


class ForecastType(str, enum.Enum):
    BASE = "base"
    OTTIMISTICO = "ottimistico"
    PESSIMISTICO = "pessimistico"
    PERSONALIZZATO = "personalizzato"


class CashFlowLineType(str, enum.Enum):
    ENTRATA = "entrata"
    USCITA = "uscita"


class CashFlowSource(str, enum.Enum):
    MOVIMENTO_REALE = "movimento_reale"
    SCADENZA = "scadenza"
    PAGAMENTO_PIANIFICATO = "pagamento_pianificato"
    RICORRENZA = "ricorrenza"
    MANUALE = "manuale"
    STIMA_STORICA = "stima_storica"


class ConfidenceLevel(str, enum.Enum):
    CERTA = "certa"
    ALTA = "alta"
    MEDIA = "media"
    BASSA = "bassa"


class ScenarioAdjustmentType(str, enum.Enum):
    AGGIUNTA = "aggiunta"
    RIMOZIONE = "rimozione"
    MODIFICA_IMPORTO = "modifica_importo"
    SPOSTAMENTO_DATA = "spostamento_data"


class CashFlowAlertType(str, enum.Enum):
    SOTTO_SOGLIA_MINIMA = "sotto_soglia_minima"
    SOPRA_SOGLIA_MASSIMA = "sopra_soglia_massima"
    SALDO_NEGATIVO = "saldo_negativo"
    VARIANZA_ALTA = "varianza_alta"


class AlertStatus(str, enum.Enum):
    ATTIVO = "attivo"
    RISOLTO = "risolto"
    IGNORATO = "ignorato"


# --- Module 10: Dashboard ---

class WidgetType(str, enum.Enum):
    SALDO_TOTALE = "saldo_totale"
    CASH_FLOW_MINI = "cash_flow_mini"
    ENTRATE_USCITE = "entrate_uscite"
    SCADENZE = "scadenze"
    RICONCILIAZIONE = "riconciliazione"
    PAGAMENTI_PENDENTI = "pagamenti_pendenti"
    ALERT = "alert"
    ATTIVITA_RECENTI = "attivita_recenti"
    AZIONI_RAPIDE = "azioni_rapide"
    SALDI_PER_CONTO = "saldi_per_conto"


class WidgetSize(str, enum.Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


# --- Module 11: Reporting ---

class ReportType(str, enum.Enum):
    SALDI_CONTI = "saldi_conti"
    MOVIMENTI = "movimenti"
    ENTRATE_USCITE = "entrate_uscite"
    RICONCILIAZIONE = "riconciliazione"
    SCADENZARIO = "scadenzario"
    AGING = "aging"
    CASH_FLOW = "cash_flow"
    PAGAMENTI = "pagamenti"
    CONTROPARTE = "controparte"
    PERSONALIZZATO = "personalizzato"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"


class ReportExecutionStatus(str, enum.Enum):
    IN_CODA = "in_coda"
    IN_GENERAZIONE = "in_generazione"
    COMPLETATO = "completato"
    ERRORE = "errore"


class ReportFrequency(str, enum.Enum):
    GIORNALIERO = "giornaliero"
    SETTIMANALE = "settimanale"
    MENSILE = "mensile"
    TRIMESTRALE = "trimestrale"


# --- Module 12: Integrations ---

class OpenBankingProvider(str, enum.Enum):
    NORDIGEN_GOCARDLESS = "nordigen_gocardless"
    TINK = "tink"
    SALT_EDGE = "salt_edge"
    CBI_GLOBE = "cbi_globe"
    FABRICK = "fabrick"
    GENERICO = "generico"


class OpenBankingConnectionStatus(str, enum.Enum):
    IN_ATTESA_CONSENSO = "in_attesa_consenso"
    ATTIVA = "attiva"
    SCADUTA = "scaduta"
    REVOCATA = "revocata"
    ERRORE = "errore"


class SyncFrequency(str, enum.Enum):
    OGNI_ORA = "ogni_ora"
    OGNI_6_ORE = "ogni_6_ore"
    GIORNALIERO = "giornaliero"
    MANUALE = "manuale"


class SyncLogStatus(str, enum.Enum):
    SUCCESSO = "successo"
    PARZIALE = "parziale"
    ERRORE = "errore"


class InvoiceSource(str, enum.Enum):
    CASSETTO_FISCALE = "cassetto_fiscale"
    UPLOAD_XML = "upload_xml"
    SDI_API = "sdi_api"
    ALTRO = "altro"


class InvoiceDocumentType(str, enum.Enum):
    FATTURA_VENDITA = "fattura_vendita"
    FATTURA_ACQUISTO = "fattura_acquisto"
    NOTA_CREDITO_VENDITA = "nota_credito_vendita"
    NOTA_CREDITO_ACQUISTO = "nota_credito_acquisto"
    AUTOFATTURA = "autofattura"


class InvoiceStatus(str, enum.Enum):
    IMPORTATA = "importata"
    ELABORATA = "elaborata"
    SCADENZA_CREATA = "scadenza_creata"
    ERRORE = "errore"
    IGNORATA = "ignorata"


class InvoiceBatchSource(str, enum.Enum):
    CASSETTO_FISCALE = "cassetto_fiscale"
    UPLOAD_MULTIPLO = "upload_multiplo"
    SDI_API = "sdi_api"


class InvoiceBatchStatus(str, enum.Enum):
    IN_CORSO = "in_corso"
    COMPLETATO = "completato"
    COMPLETATO_CON_ERRORI = "completato_con_errori"
    FALLITO = "fallito"


class IntegrationType(str, enum.Enum):
    OPEN_BANKING = "open_banking"
    FATTURE_ELETTRONICHE = "fatture_elettroniche"
    CBI_CORPORATE_BANKING = "cbi_corporate_banking"


class IntegrationConnectionStatus(str, enum.Enum):
    NON_CONFIGURATA = "non_configurata"
    CONFIGURATA = "configurata"
    CONNESSA = "connessa"
    ERRORE = "errore"


class WebhookType(str, enum.Enum):
    OPEN_BANKING_SYNC = "open_banking_sync"
    SDI_NOTIFICA = "sdi_notifica"
    PAGAMENTO_ESITO = "pagamento_esito"
    GENERICO = "generico"
