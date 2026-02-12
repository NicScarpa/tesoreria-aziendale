export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type {
  Schedule,
  SchedulePayment,
  ScheduleReminder,
  ScheduleAttachment,
  ScheduleListResponse,
  ScheduleCalendarDay,
  ScheduleAgingResponse,
  ScheduleAgingBand,
  ScheduleSummary,
  ScheduleSummaryTotals,
} from "./schedule";

export type {
  DashboardData,
  DashboardWidget,
  DashboardSnapshot,
  DashboardTrendResponse,
  SaldiSection,
  CashFlowPreviewSection,
  EntrateUsciteSection,
  ScadenzeSection,
  RiconciliazioneSection,
  PagamentiSection,
  AlertSection,
  AlertItem,
  AttivitaRecenteItem,
  QuickActionItem,
  ContoSaldoItem,
  WidgetType,
} from "./dashboard";

export type {
  ReportDefinition,
  ReportExecution,
  ReportSchedule,
  ReportDefinitionListResponse,
  ReportExecutionListResponse,
  ReportScheduleListResponse,
  ReportType,
  ReportFormat,
  ReportExecutionStatus,
  ReportFrequency,
} from "./report";

export type {
  IntegrationStatusItem,
  IntegrationOverview,
  IntegrationConfig,
  InstitutionInfo,
  OpenBankingConnection,
  OpenBankingConnectionListResponse,
  OpenBankingSyncLog,
  SyncLogListResponse,
  InvoiceImport,
  InvoiceImportListResponse,
  InvoiceElaborateResult,
  InvoiceImportBatch,
  InvoiceBatchListResponse,
  SEPAValidationResult,
  CBIParseResult,
  CAMT053ImportResult,
  WebhookEndpoint,
  WebhookListResponse,
  IntegrationAlertsCount,
  IntegrationType,
  IntegrationConnectionStatus,
  OpenBankingProvider,
  OpenBankingConnectionStatus,
  SyncFrequency,
  SyncLogStatus,
  InvoiceSource,
  InvoiceDocumentType,
  InvoiceStatus,
  InvoiceBatchSource,
  InvoiceBatchStatus,
  WebhookType,
} from "./integration";
