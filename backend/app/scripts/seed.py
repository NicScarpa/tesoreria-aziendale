"""Seed script: crea dati di test per sviluppo locale."""

from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import (
    User, Company, UserCompany, UserRole, UserCompanyStatus,
    Institution, ReconciliationRule,
    BankAccount, AccountStatus, AccountType,
    BankAccountBalance, BalanceSource,
    Category, Subcategory, Transaction, FlowDirection,
    TransactionStatus, TransactionType, CategorizationSource,
    CategorizationRule, RuleActionType,
    CashFlowForecast, CashFlowForecastLine, CashFlowScenario, CashFlowAlert,
    ForecastStatus, ForecastType, CashFlowLineType, CashFlowSource,
    ConfidenceLevel, ScenarioAdjustmentType, CashFlowAlertType, AlertStatus,
    DashboardWidget, DashboardSnapshot, WidgetType, WidgetSize,
    ReportDefinition, ReportExecution, ReportType, ReportFormat,
    ReportExecutionStatus,
    IntegrationConfig, IntegrationType, IntegrationConnectionStatus,
    OpenBankingConnection, OpenBankingProvider, OpenBankingConnectionStatus,
    SyncFrequency, OpenBankingSyncLog, SyncLogStatus,
    InvoiceImport, InvoiceSource, InvoiceDocumentType, InvoiceStatus,
    InvoiceImportBatch, InvoiceBatchSource, InvoiceBatchStatus,
    WebhookEndpoint, WebhookType,
)


def seed():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@test.com").first()
        if existing:
            print("Seed data already exists, skipping.")
            return

        # --- Utente admin (OWNER) ---
        user = User(
            email="admin@test.com",
            password_hash=get_password_hash("Admin123!"),
            first_name="Admin",
            last_name="Test",
            email_verified=True,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # --- Utente editor ---
        editor = User(
            email="editor@test.com",
            password_hash=get_password_hash("Editor123!"),
            first_name="Editor",
            last_name="Test",
            email_verified=True,
            is_active=True,
        )
        db.add(editor)
        db.flush()

        # --- Company con dati estesi ---
        company = Company(
            name="Azienda Test SRL",
            vat_number="01234567890",
            country="IT",
            fiscal_regime="RF01",
            city="Milano",
            postal_code="20100",
            province_code="MI",
            default_currency="EUR",
        )
        db.add(company)
        db.flush()

        # --- Associazioni user-company ---
        uc_owner = UserCompany(
            user_id=user.id,
            company_id=company.id,
            role=UserRole.OWNER,
            status=UserCompanyStatus.ACTIVE,
        )
        db.add(uc_owner)

        uc_editor = UserCompany(
            user_id=editor.id,
            company_id=company.id,
            role=UserRole.EDITOR,
            status=UserCompanyStatus.ACTIVE,
        )
        db.add(uc_editor)
        db.flush()

        # --- Institution di esempio ---
        inst_unicredit = Institution(
            name="UniCredit",
            full_name="UniCredit S.p.A.",
            source="SWAN",
            country="IT",
            bic="UNCRITMM",
        )
        db.add(inst_unicredit)

        inst_intesa = Institution(
            name="Intesa Sanpaolo",
            full_name="Intesa Sanpaolo S.p.A.",
            source="SWAN",
            country="IT",
            bic="BCITITMM",
        )
        db.add(inst_intesa)
        db.flush()

        # --- ReconciliationRule default ---
        rule = ReconciliationRule(
            company_id=company.id,
            name="Regola standard",
            match_amount=True,
            amount_tolerance=Decimal("0.01"),
            match_date=True,
            date_tolerance_days=3,
            match_description=False,
            match_counterpart=True,
            auto_confirm=False,
            min_confidence=Decimal("0.80"),
            priority=0,
            is_active=True,
        )
        db.add(rule)
        db.flush()

        # --- Conti bancari manuali ---
        today = date.today()
        yesterday = today - timedelta(days=1)

        account_bpm = BankAccount(
            company_id=company.id,
            bank_connection_id=None,
            nickname="Conto Principale BPM",
            iban="IT60X0542811101000000123456",
            currency="EUR",
            current_balance=Decimal("150000.00"),
            available_balance=Decimal("148000.00"),
            balance_date=datetime.now(timezone.utc),
            status=AccountStatus.ACTIVE,
            account_type=AccountType.CHECKING,
            is_default=True,
            bank_name="Banco BPM",
            bank_abi="05428",
            bank_cab="11101",
            color="#2563eb",
        )
        db.add(account_bpm)
        db.flush()

        account_unicredit = BankAccount(
            company_id=company.id,
            bank_connection_id=None,
            nickname="Conto Secondario Unicredit",
            iban="IT40L0300203280578741892394",
            currency="EUR",
            current_balance=Decimal("25000.00"),
            available_balance=Decimal("25000.00"),
            balance_date=datetime.now(timezone.utc),
            status=AccountStatus.ACTIVE,
            account_type=AccountType.CHECKING,
            is_default=False,
            bank_name="UniCredit",
            bank_abi="03002",
            bank_cab="03280",
            color="#059669",
        )
        db.add(account_unicredit)
        db.flush()

        # --- Storico saldi (ultimi 2 giorni per ogni conto) ---
        for account, balances in [
            (account_bpm, [
                (yesterday, Decimal("147500.00"), Decimal("145500.00")),
                (today, Decimal("150000.00"), Decimal("148000.00")),
            ]),
            (account_unicredit, [
                (yesterday, Decimal("24000.00"), Decimal("24000.00")),
                (today, Decimal("25000.00"), Decimal("25000.00")),
            ]),
        ]:
            for bal_date, current, available in balances:
                balance_entry = BankAccountBalance(
                    bank_account_id=account.id,
                    company_id=company.id,
                    balance_date=bal_date,
                    current_balance=current,
                    available_balance=available,
                    source=BalanceSource.MANUAL,
                )
                db.add(balance_entry)

        # --- Categorie di default (is_system=True) ---
        category_data = [
            ("Stipendi", "#22c55e", 0),
            ("Fornitori", "#ef4444", 1),
            ("Utenze", "#f97316", 2),
            ("Tasse e Contributi", "#8b5cf6", 3),
            ("Incassi Clienti", "#06b6d4", 4),
            ("Commissioni Bancarie", "#64748b", 5),
            ("Affitti", "#ec4899", 6),
            ("Assicurazioni", "#14b8a6", 7),
            ("Rimborsi", "#84cc16", 8),
            ("Altro", "#6b7280", 9),
        ]
        categories = {}
        for name, color, sort_order in category_data:
            cat = Category(
                company_id=company.id,
                name=name,
                color=color,
                sort_order=sort_order,
                is_system=True,
            )
            db.add(cat)
            db.flush()
            categories[name] = cat

        # --- Sottocategorie ---
        subcategory_data = [
            ("Stipendi", ["Stipendi Dipendenti", "Collaboratori", "TFR"]),
            ("Fornitori", ["Materie Prime", "Servizi Professionali"]),
            ("Utenze", ["Energia Elettrica", "Gas", "Telecomunicazioni"]),
            ("Tasse e Contributi", ["IVA", "IRES/IRPEF", "INPS"]),
            ("Incassi Clienti", ["Fatture Emesse", "Acconti"]),
        ]
        for cat_name, subs in subcategory_data:
            cat = categories[cat_name]
            for i, sub_name in enumerate(subs):
                sub = Subcategory(
                    category_id=cat.id,
                    company_id=company.id,
                    name=sub_name,
                    sort_order=i,
                )
                db.add(sub)
        db.flush()

        # --- Movimenti di test (20 transazioni, ultimi 30 giorni) ---
        transactions_data = [
            # (account, days_ago, amount, direction, description, counterpart_name, tx_type, category_name)
            (account_bpm, 1, Decimal("15000.00"), FlowDirection.INFLOW,
             "Bonifico da Cliente ABC SRL", "ABC SRL", TransactionType.CREDIT_TRANSFER, "Incassi Clienti"),
            (account_bpm, 2, Decimal("-3500.00"), FlowDirection.OUTFLOW,
             "Stipendio Mario Rossi gennaio 2026", "Mario Rossi", TransactionType.CREDIT_TRANSFER, "Stipendi"),
            (account_bpm, 3, Decimal("-3200.00"), FlowDirection.OUTFLOW,
             "Stipendio Laura Bianchi gennaio 2026", "Laura Bianchi", TransactionType.CREDIT_TRANSFER, "Stipendi"),
            (account_bpm, 5, Decimal("-850.00"), FlowDirection.OUTFLOW,
             "Pagamento fattura Enel Energia", "Enel Energia", TransactionType.DIRECT_DEBIT, "Utenze"),
            (account_bpm, 7, Decimal("8500.00"), FlowDirection.INFLOW,
             "Bonifico da XYZ Trading", "XYZ Trading SPA", TransactionType.CREDIT_TRANSFER, "Incassi Clienti"),
            (account_bpm, 8, Decimal("-12000.00"), FlowDirection.OUTFLOW,
             "Pagamento fornitore Tecnoparts", "Tecnoparts SRL", TransactionType.CREDIT_TRANSFER, "Fornitori"),
            (account_bpm, 10, Decimal("-2500.00"), FlowDirection.OUTFLOW,
             "Affitto ufficio via Roma 15", "Immobiliare Centro", TransactionType.CREDIT_TRANSFER, "Affitti"),
            (account_bpm, 12, Decimal("-45.50"), FlowDirection.OUTFLOW,
             "Commissione bancaria trimestrale", None, TransactionType.FEE, "Commissioni Bancarie"),
            (account_bpm, 15, Decimal("22000.00"), FlowDirection.INFLOW,
             "Acconto progetto Delta", "Delta Consulting", TransactionType.CREDIT_TRANSFER, "Incassi Clienti"),
            (account_bpm, 20, Decimal("-5800.00"), FlowDirection.OUTFLOW,
             "F24 IVA trimestrale", None, TransactionType.TAX, "Tasse e Contributi"),
            # Conto Unicredit
            (account_unicredit, 1, Decimal("3200.00"), FlowDirection.INFLOW,
             "Bonifico da Omega SRL", "Omega SRL", TransactionType.CREDIT_TRANSFER, "Incassi Clienti"),
            (account_unicredit, 3, Decimal("-1200.00"), FlowDirection.OUTFLOW,
             "Pagamento consulenza Studio Verdi", "Studio Verdi", TransactionType.CREDIT_TRANSFER, "Fornitori"),
            (account_unicredit, 5, Decimal("-320.00"), FlowDirection.OUTFLOW,
             "Bolletta Telecom Italia", "Telecom Italia", TransactionType.DIRECT_DEBIT, "Utenze"),
            (account_unicredit, 7, Decimal("1800.00"), FlowDirection.INFLOW,
             "Rimborso assicurazione", "Generali", TransactionType.CREDIT_TRANSFER, "Rimborsi"),
            (account_unicredit, 10, Decimal("-650.00"), FlowDirection.OUTFLOW,
             "Premio assicurazione RC", "Allianz", TransactionType.DIRECT_DEBIT, "Assicurazioni"),
            (account_unicredit, 12, Decimal("-15.00"), FlowDirection.OUTFLOW,
             "Canone mensile conto", None, TransactionType.FEE, "Commissioni Bancarie"),
            (account_unicredit, 15, Decimal("5500.00"), FlowDirection.INFLOW,
             "Bonifico da Beta Industries", "Beta Industries", TransactionType.CREDIT_TRANSFER, "Incassi Clienti"),
            (account_unicredit, 18, Decimal("-2100.00"), FlowDirection.OUTFLOW,
             "INPS contributi dipendenti", None, TransactionType.TAX, "Tasse e Contributi"),
            (account_unicredit, 22, Decimal("-780.00"), FlowDirection.OUTFLOW,
             "Pagamento carta di credito", None, TransactionType.CARD_PAYMENT, None),
            (account_unicredit, 25, Decimal("950.00"), FlowDirection.INFLOW,
             "Nota di credito fornitore", "Tecnoparts SRL", TransactionType.CREDIT_TRANSFER, "Rimborsi"),
        ]

        for acct, days_ago, amount, direction, desc, counterpart, tx_type, cat_name in transactions_data:
            tx = Transaction(
                company_id=company.id,
                bank_account_id=acct.id,
                amount=amount,
                currency="EUR",
                direction=direction,
                transaction_date=today - timedelta(days=days_ago),
                description=desc,
                transaction_type=tx_type,
                category_id=categories[cat_name].id if cat_name else None,
                categorization_source=CategorizationSource.MANUAL if cat_name else None,
                counterpart_name=counterpart,
                status=TransactionStatus.BOOKED,
                verified=days_ago <= 5,
            )
            db.add(tx)

        # --- Regole di categorizzazione ---
        cat_rule_stipendi = CategorizationRule(
            company_id=company.id,
            name="Stipendi dipendenti",
            direction=FlowDirection.OUTFLOW,
            action_type=RuleActionType.SET_CATEGORY,
            category_id=categories["Stipendi"].id,
            conditions=[{"type": "KEYWORDS", "value": ["stipendio", "stipendi"]}],
            priority=10,
            is_active=True,
        )
        db.add(cat_rule_stipendi)

        cat_rule_enel = CategorizationRule(
            company_id=company.id,
            name="Utenze Enel",
            direction=FlowDirection.OUTFLOW,
            action_type=RuleActionType.SET_CATEGORY,
            category_id=categories["Utenze"].id,
            conditions=[{"type": "KEYWORDS", "value": ["enel"]}],
            priority=5,
            is_active=True,
        )
        db.add(cat_rule_enel)

        # --- Module 9: Cash Flow Forecast ---
        forecast = CashFlowForecast(
            company_id=company.id,
            creato_da_user_id=user.id,
            nome="Previsione Q1 2026",
            descrizione="Previsione cash flow primo trimestre 2026",
            data_inizio=today - timedelta(days=30),
            data_fine=today + timedelta(days=30),
            saldo_iniziale=Decimal("175000.00"),
            saldo_finale_previsto=Decimal("168500.00"),
            totale_entrate_previste=Decimal("55000.00"),
            totale_uscite_previste=Decimal("61500.00"),
            stato=ForecastStatus.ATTIVA,
            tipo=ForecastType.BASE,
            parametri={"conti_inclusi": "tutti", "includi_ricorrenze": True},
            is_auto=False,
        )
        db.add(forecast)
        db.flush()

        # 60 CashFlowForecastLine: 30 passati (movimenti reali), 30 futuri (previsioni)
        cf_lines = []
        running_balance = Decimal("175000.00")
        for day_offset in range(-30, 31):
            line_date = today + timedelta(days=day_offset)
            is_past = day_offset < 0

            if day_offset % 3 == 0:
                # Entrata
                importo = Decimal("2500.00") if is_past else Decimal("1800.00")
                running_balance += importo
                cf_lines.append(CashFlowForecastLine(
                    forecast_id=forecast.id,
                    data=line_date,
                    tipo=CashFlowLineType.ENTRATA,
                    importo=importo,
                    categoria="Incassi Clienti",
                    descrizione=f"Incasso cliente {'reale' if is_past else 'previsto'}",
                    fonte=CashFlowSource.MOVIMENTO_REALE if is_past else CashFlowSource.SCADENZA,
                    confidenza=ConfidenceLevel.CERTA if is_past else ConfidenceLevel.ALTA,
                    saldo_progressivo=running_balance,
                    is_realizzata=is_past,
                ))
            if day_offset % 5 == 0:
                # Uscita
                importo = Decimal("3200.00") if is_past else Decimal("2800.00")
                running_balance -= importo
                cf_lines.append(CashFlowForecastLine(
                    forecast_id=forecast.id,
                    data=line_date,
                    tipo=CashFlowLineType.USCITA,
                    importo=importo,
                    categoria="Fornitori",
                    descrizione=f"Pagamento fornitore {'reale' if is_past else 'previsto'}",
                    fonte=CashFlowSource.MOVIMENTO_REALE if is_past else CashFlowSource.SCADENZA,
                    confidenza=ConfidenceLevel.CERTA if is_past else CashFlowSource.SCADENZA and ConfidenceLevel.MEDIA,
                    saldo_progressivo=running_balance,
                    is_realizzata=is_past,
                ))

        db.add_all(cf_lines)
        db.flush()

        # 2 CashFlowScenario
        scenario_1 = CashFlowScenario(
            forecast_id=forecast.id,
            nome="Nuovo cliente grande",
            descrizione="Acquisizione nuovo cliente con fatturato 50k/mese",
            tipo_aggiustamento=ScenarioAdjustmentType.AGGIUNTA,
            importo_modificato=Decimal("50000.00"),
            tipo_movimento=CashFlowLineType.ENTRATA,
            categoria="Incassi Clienti",
            data_modificata=today + timedelta(days=15),
            attivo=True,
        )
        scenario_2 = CashFlowScenario(
            forecast_id=forecast.id,
            nome="Ritardo fornitore",
            descrizione="Pagamento fornitore principale ritardato di 30gg",
            tipo_aggiustamento=ScenarioAdjustmentType.SPOSTAMENTO_DATA,
            data_originale=today + timedelta(days=10),
            data_modificata=today + timedelta(days=40),
            importo_originale=Decimal("12000.00"),
            tipo_movimento=CashFlowLineType.USCITA,
            categoria="Fornitori",
            attivo=True,
        )
        db.add_all([scenario_1, scenario_2])
        db.flush()

        # 3 CashFlowAlert
        alert_1 = CashFlowAlert(
            company_id=company.id,
            forecast_id=forecast.id,
            tipo=CashFlowAlertType.SOTTO_SOGLIA_MINIMA,
            data_prevista=today + timedelta(days=20),
            saldo_previsto=Decimal("8500.00"),
            soglia=Decimal("10000.00"),
            messaggio="Saldo previsto sotto la soglia minima di 10.000 EUR il " + (today + timedelta(days=20)).isoformat(),
            stato=AlertStatus.ATTIVO,
        )
        alert_2 = CashFlowAlert(
            company_id=company.id,
            forecast_id=forecast.id,
            tipo=CashFlowAlertType.SALDO_NEGATIVO,
            data_prevista=today + timedelta(days=25),
            saldo_previsto=Decimal("-2300.00"),
            soglia=Decimal("0"),
            messaggio="Saldo previsto negativo il " + (today + timedelta(days=25)).isoformat(),
            stato=AlertStatus.ATTIVO,
        )
        alert_3 = CashFlowAlert(
            company_id=company.id,
            forecast_id=forecast.id,
            tipo=CashFlowAlertType.SOTTO_SOGLIA_MINIMA,
            data_prevista=today - timedelta(days=5),
            saldo_previsto=Decimal("9200.00"),
            soglia=Decimal("10000.00"),
            messaggio="Saldo sotto soglia minima risolto",
            stato=AlertStatus.RISOLTO,
        )
        db.add_all([alert_1, alert_2, alert_3])
        db.flush()

        # --- Module 10: Dashboard Widgets & Snapshots ---
        import random
        random.seed(42)

        # Widget layout default per admin user
        default_widgets = [
            (WidgetType.SALDO_TOTALE, 0, 0, WidgetSize.LARGE),
            (WidgetType.CASH_FLOW_MINI, 1, 0, WidgetSize.LARGE),
            (WidgetType.ENTRATE_USCITE, 2, 0, WidgetSize.MEDIUM),
            (WidgetType.SCADENZE, 2, 1, WidgetSize.MEDIUM),
            (WidgetType.RICONCILIAZIONE, 3, 0, WidgetSize.SMALL),
            (WidgetType.PAGAMENTI_PENDENTI, 3, 1, WidgetSize.SMALL),
            (WidgetType.ALERT, 4, 0, WidgetSize.MEDIUM),
            (WidgetType.ATTIVITA_RECENTI, 4, 1, WidgetSize.MEDIUM),
            (WidgetType.AZIONI_RAPIDE, 5, 0, WidgetSize.SMALL),
            (WidgetType.SALDI_PER_CONTO, 5, 1, WidgetSize.SMALL),
        ]
        for wtype, pos, col, size in default_widgets:
            widget = DashboardWidget(
                user_id=user.id,
                company_id=company.id,
                widget_type=wtype,
                posizione=pos,
                colonna=col,
                dimensione=size,
                visibile=True,
            )
            db.add(widget)
        db.flush()

        # 30 giorni di DashboardSnapshot
        base_saldo = Decimal("155000.00")
        for day_offset in range(30, 0, -1):
            snap_date = today - timedelta(days=day_offset)
            variation = Decimal(str(random.uniform(-5000, 5000))).quantize(Decimal("0.01"))
            base_saldo += variation
            snap_entrate = Decimal(str(random.uniform(1000, 8000))).quantize(Decimal("0.01"))
            snap_uscite = Decimal(str(random.uniform(1000, 8000))).quantize(Decimal("0.01"))

            snapshot = DashboardSnapshot(
                company_id=company.id,
                data=snap_date,
                saldo_totale=base_saldo,
                entrate_giorno=snap_entrate,
                uscite_giorno=snap_uscite,
                movimenti_non_riconciliati=random.randint(2, 15),
                scadenze_scadute_importo=Decimal(str(random.uniform(0, 25000))).quantize(Decimal("0.01")),
                scadenze_scadute_conteggio=random.randint(0, 5),
                pagamenti_da_approvare=random.randint(0, 3),
                previsione_30gg=base_saldo + Decimal(str(random.uniform(-10000, 15000))).quantize(Decimal("0.01")),
                alert_attivi=random.randint(0, 4),
            )
            db.add(snapshot)

        # --- Module 11: Report Definitions di sistema ---
        system_reports = [
            ReportDefinition(
                company_id=None, nome="Situazione Saldi",
                descrizione="Panoramica saldi di tutti i conti bancari con dettaglio disponibilità",
                tipo=ReportType.SALDI_CONTI, formato_default=ReportFormat.PDF,
                is_system=True, sort_order=0,
                parametri_default={"includi_conti_chiusi": False, "mostra_trend": True},
                layout={"orientamento": "landscape", "colonne": ["conto", "iban", "saldo_contabile", "saldo_disponibile", "data_aggiornamento"]},
            ),
            ReportDefinition(
                company_id=None, nome="Estratto Conto",
                descrizione="Elenco movimenti per conto bancario con saldo progressivo",
                tipo=ReportType.MOVIMENTI, formato_default=ReportFormat.XLSX,
                is_system=True, sort_order=1,
                parametri_default={"periodo_default_giorni": 30, "includi_saldo_progressivo": True},
                layout={"orientamento": "portrait", "colonne": ["data", "descrizione", "dare", "avere", "saldo"]},
            ),
            ReportDefinition(
                company_id=None, nome="Entrate e Uscite per Categoria",
                descrizione="Riepilogo entrate e uscite raggruppate per categoria",
                tipo=ReportType.ENTRATE_USCITE, formato_default=ReportFormat.PDF,
                is_system=True, sort_order=2,
                parametri_default={"periodo_default_giorni": 30, "raggruppamento": "categoria"},
                layout={"orientamento": "portrait", "colonne": ["categoria", "entrate", "uscite", "saldo_netto"]},
            ),
            ReportDefinition(
                company_id=None, nome="Stato Riconciliazione",
                descrizione="Report sullo stato di riconciliazione dei movimenti bancari",
                tipo=ReportType.RICONCILIAZIONE, formato_default=ReportFormat.PDF,
                is_system=True, sort_order=3,
                parametri_default={"periodo_default_giorni": 30, "solo_non_riconciliati": False},
                layout={"orientamento": "landscape", "colonne": ["conto", "totale_movimenti", "riconciliati", "non_riconciliati", "percentuale"]},
            ),
            ReportDefinition(
                company_id=None, nome="Scadenzario Attivo",
                descrizione="Elenco scadenze attive (crediti da incassare)",
                tipo=ReportType.SCADENZARIO, formato_default=ReportFormat.XLSX,
                is_system=True, sort_order=4,
                parametri_default={"tipo_scadenzario": "attiva", "includi_scadute": True},
                layout={"orientamento": "portrait", "colonne": ["controparte", "descrizione", "scadenza", "importo", "stato"]},
            ),
            ReportDefinition(
                company_id=None, nome="Scadenzario Passivo",
                descrizione="Elenco scadenze passive (debiti da pagare)",
                tipo=ReportType.SCADENZARIO, formato_default=ReportFormat.XLSX,
                is_system=True, sort_order=5,
                parametri_default={"tipo_scadenzario": "passiva", "includi_scadute": True},
                layout={"orientamento": "portrait", "colonne": ["controparte", "descrizione", "scadenza", "importo", "stato"]},
            ),
            ReportDefinition(
                company_id=None, nome="Aging Crediti/Debiti",
                descrizione="Analisi aging delle scadenze per fasce temporali",
                tipo=ReportType.AGING, formato_default=ReportFormat.PDF,
                is_system=True, sort_order=6,
                parametri_default={"fasce_giorni": [0, 30, 60, 90, 120], "tipo": "entrambi"},
                layout={"orientamento": "landscape", "colonne": ["controparte", "corrente", "30gg", "60gg", "90gg", "oltre_90gg", "totale"]},
            ),
            ReportDefinition(
                company_id=None, nome="Previsione Cash Flow",
                descrizione="Proiezione del cash flow futuro basata su scadenze e movimenti ricorrenti",
                tipo=ReportType.CASH_FLOW, formato_default=ReportFormat.PDF,
                is_system=True, sort_order=7,
                parametri_default={"periodo_default_giorni": 90, "includi_scadenze": True, "includi_ricorrenze": True},
                layout={"orientamento": "landscape", "colonne": ["periodo", "entrate", "uscite", "saldo_netto", "saldo_progressivo"]},
            ),
            ReportDefinition(
                company_id=None, nome="Riepilogo Pagamenti",
                descrizione="Riepilogo degli ordini di pagamento con stato e dettagli",
                tipo=ReportType.PAGAMENTI, formato_default=ReportFormat.XLSX,
                is_system=True, sort_order=8,
                parametri_default={"periodo_default_giorni": 30, "includi_bozze": False},
                layout={"orientamento": "landscape", "colonne": ["data", "tipo", "beneficiario", "importo", "stato", "banca"]},
            ),
            ReportDefinition(
                company_id=None, nome="Scheda Controparte",
                descrizione="Scheda dettagliata di una controparte con movimenti, scadenze e pagamenti",
                tipo=ReportType.CONTROPARTE, formato_default=ReportFormat.PDF,
                is_system=True, sort_order=9,
                parametri_default={"periodo_default_giorni": 365},
                layout={"orientamento": "portrait", "colonne": ["data", "tipo", "descrizione", "dare", "avere", "saldo"]},
            ),
        ]
        db.add_all(system_reports)
        db.flush()

        # --- Esecuzioni di esempio ---
        exec_1 = ReportExecution(
            company_id=company.id,
            report_definition_id=system_reports[0].id,
            generato_da_user_id=user.id,
            nome="Situazione Saldi - febbraio 2026",
            tipo=ReportType.SALDI_CONTI.value,
            formato=ReportFormat.PDF,
            stato=ReportExecutionStatus.COMPLETATO,
            parametri={"data_riferimento": today.isoformat()},
            righe_totali=2,
            data_completamento=datetime.now(timezone.utc),
            data_scadenza_file=datetime.now(timezone.utc) + timedelta(days=30),
        )
        exec_2 = ReportExecution(
            company_id=company.id,
            report_definition_id=system_reports[1].id,
            generato_da_user_id=user.id,
            nome="Estratto Conto BPM - gennaio 2026",
            tipo=ReportType.MOVIMENTI.value,
            formato=ReportFormat.XLSX,
            stato=ReportExecutionStatus.COMPLETATO,
            parametri={"conto_id": str(account_bpm.id), "data_inizio": (today - timedelta(days=30)).isoformat(), "data_fine": today.isoformat()},
            righe_totali=10,
            data_completamento=datetime.now(timezone.utc) - timedelta(days=5),
            data_scadenza_file=datetime.now(timezone.utc) + timedelta(days=25),
        )
        exec_3 = ReportExecution(
            company_id=company.id,
            report_definition_id=system_reports[2].id,
            generato_da_user_id=user.id,
            nome="Entrate/Uscite - gennaio 2026",
            tipo=ReportType.ENTRATE_USCITE.value,
            formato=ReportFormat.PDF,
            stato=ReportExecutionStatus.COMPLETATO,
            parametri={"data_inizio": (today - timedelta(days=30)).isoformat(), "data_fine": today.isoformat()},
            righe_totali=8,
            data_completamento=datetime.now(timezone.utc) - timedelta(days=3),
            data_scadenza_file=datetime.now(timezone.utc) + timedelta(days=27),
        )
        db.add_all([exec_1, exec_2, exec_3])
        db.flush()

        # --- Module 12: Integration Configs ---
        ic_ob = IntegrationConfig(
            company_id=company.id,
            integration_type=IntegrationType.OPEN_BANKING,
            status=IntegrationConnectionStatus.CONNESSA,
            is_enabled=True,
            config={"provider_default": "nordigen_gocardless"},
        )
        ic_fe = IntegrationConfig(
            company_id=company.id,
            integration_type=IntegrationType.FATTURE_ELETTRONICHE,
            status=IntegrationConnectionStatus.NON_CONFIGURATA,
            is_enabled=False,
        )
        ic_cbi = IntegrationConfig(
            company_id=company.id,
            integration_type=IntegrationType.CBI_CORPORATE_BANKING,
            status=IntegrationConnectionStatus.NON_CONFIGURATA,
            is_enabled=False,
        )
        db.add_all([ic_ob, ic_fe, ic_cbi])
        db.flush()

        # --- Module 12: Open Banking Connection ---
        ob_conn = OpenBankingConnection(
            company_id=company.id,
            bank_account_id=account_unicredit.id,
            provider=OpenBankingProvider.NORDIGEN_GOCARDLESS,
            provider_connection_id="MOCK-CONN-001",
            provider_account_id="MOCK-ACCT-001",
            institution_id="UNICREDIT_UNCRITMM",
            institution_nome="UniCredit",
            institution_logo_url="https://cdn.nordigen.com/ais/UNICREDIT_UNCRITMM.png",
            stato=OpenBankingConnectionStatus.ATTIVA,
            consenso_id="MOCK-CONSENT-001",
            consenso_scadenza=datetime.now(timezone.utc) + timedelta(days=60),
            consenso_creato_at=datetime.now(timezone.utc) - timedelta(days=30),
            ultimo_sync=datetime.now(timezone.utc) - timedelta(hours=6),
            prossimo_sync=datetime.now(timezone.utc) + timedelta(hours=18),
            frequenza_sync=SyncFrequency.GIORNALIERO,
            sync_attivo=True,
            errore_conteggio=0,
        )
        db.add(ob_conn)
        db.flush()

        # --- Module 12: Sync Log ---
        sync_log = OpenBankingSyncLog(
            connection_id=ob_conn.id,
            stato=SyncLogStatus.SUCCESSO,
            movimenti_scaricati=15,
            movimenti_nuovi=3,
            movimenti_duplicati=12,
            saldo_aggiornato=True,
            periodo_da=datetime.now(timezone.utc) - timedelta(days=7),
            periodo_a=datetime.now(timezone.utc),
            durata_ms=2350,
            request_id="req-mock-001",
        )
        db.add(sync_log)
        db.flush()

        # --- Module 12: Invoice Import Batch ---
        inv_batch = InvoiceImportBatch(
            company_id=company.id,
            fonte=InvoiceBatchSource.UPLOAD_MULTIPLO,
            totale_fatture=5,
            fatture_importate=5,
            fatture_errore=0,
            fatture_duplicate=0,
            stato=InvoiceBatchStatus.COMPLETATO,
            importato_da_user_id=user.id,
        )
        db.add(inv_batch)
        db.flush()

        # --- Module 12: Invoice Imports ---
        invoices_data = [
            {
                "fonte": InvoiceSource.UPLOAD_XML,
                "tipo_documento": InvoiceDocumentType.FATTURA_ACQUISTO,
                "stato": InvoiceStatus.SCADENZA_CREATA,
                "numero_fattura": "FPA-2026-001",
                "data_fattura": today - timedelta(days=15),
                "cedente_denominazione": "Tecnoparts SRL",
                "cedente_piva": "02345678901",
                "cessionario_denominazione": "Azienda Test SRL",
                "cessionario_piva": "01234567890",
                "importo_totale": Decimal("12200.00"),
                "imponibile_totale": Decimal("10000.00"),
                "iva_totale": Decimal("2200.00"),
                "modalita_pagamento": "MP05",
                "data_scadenza_pagamento": today + timedelta(days=15),
                "xml_file_nome": "IT02345678901_FPA01.xml",
            },
            {
                "fonte": InvoiceSource.UPLOAD_XML,
                "tipo_documento": InvoiceDocumentType.FATTURA_VENDITA,
                "stato": InvoiceStatus.IMPORTATA,
                "numero_fattura": "FV-2026-042",
                "data_fattura": today - timedelta(days=5),
                "cedente_denominazione": "Azienda Test SRL",
                "cedente_piva": "01234567890",
                "cessionario_denominazione": "ABC SRL",
                "cessionario_piva": "03456789012",
                "importo_totale": Decimal("18300.00"),
                "imponibile_totale": Decimal("15000.00"),
                "iva_totale": Decimal("3300.00"),
                "modalita_pagamento": "MP05",
                "data_scadenza_pagamento": today + timedelta(days=25),
                "xml_file_nome": "IT01234567890_FV042.xml",
            },
            {
                "fonte": InvoiceSource.UPLOAD_XML,
                "tipo_documento": InvoiceDocumentType.NOTA_CREDITO_ACQUISTO,
                "stato": InvoiceStatus.IMPORTATA,
                "numero_fattura": "NC-2026-003",
                "data_fattura": today - timedelta(days=3),
                "cedente_denominazione": "Studio Verdi",
                "cedente_piva": "04567890123",
                "cessionario_denominazione": "Azienda Test SRL",
                "cessionario_piva": "01234567890",
                "importo_totale": Decimal("-1220.00"),
                "imponibile_totale": Decimal("-1000.00"),
                "iva_totale": Decimal("-220.00"),
                "xml_file_nome": "IT04567890123_NC003.xml",
            },
            {
                "fonte": InvoiceSource.UPLOAD_XML,
                "tipo_documento": InvoiceDocumentType.FATTURA_ACQUISTO,
                "stato": InvoiceStatus.IMPORTATA,
                "numero_fattura": "FPA-2026-088",
                "data_fattura": today - timedelta(days=2),
                "cedente_denominazione": "Enel Energia",
                "cedente_piva": "05678901234",
                "cessionario_denominazione": "Azienda Test SRL",
                "cessionario_piva": "01234567890",
                "importo_totale": Decimal("1037.00"),
                "imponibile_totale": Decimal("850.00"),
                "iva_totale": Decimal("187.00"),
                "modalita_pagamento": "MP02",
                "data_scadenza_pagamento": today + timedelta(days=28),
                "xml_file_nome": "IT05678901234_FPA088.xml",
            },
            {
                "fonte": InvoiceSource.UPLOAD_XML,
                "tipo_documento": InvoiceDocumentType.FATTURA_ACQUISTO,
                "stato": InvoiceStatus.IGNORATA,
                "numero_fattura": "FPA-2026-OLD",
                "data_fattura": today - timedelta(days=60),
                "cedente_denominazione": "Vecchio Fornitore SNC",
                "cedente_piva": "06789012345",
                "cessionario_denominazione": "Azienda Test SRL",
                "cessionario_piva": "01234567890",
                "importo_totale": Decimal("500.00"),
                "imponibile_totale": Decimal("409.84"),
                "iva_totale": Decimal("90.16"),
                "xml_file_nome": "IT06789012345_FPAOLD.xml",
            },
        ]
        for inv_data in invoices_data:
            inv = InvoiceImport(
                company_id=company.id,
                batch_id=inv_batch.id,
                **inv_data,
            )
            db.add(inv)
        db.flush()

        # --- Module 12: Webhook Endpoint ---
        wh = WebhookEndpoint(
            company_id=company.id,
            tipo=WebhookType.OPEN_BANKING_SYNC,
            is_active=True,
        )
        db.add(wh)
        db.flush()

        db.commit()
        print(
            f"Seed completed: users=[{user.email}, {editor.email}], "
            f"company={company.name}, institutions=2, rules=1, "
            f"bank_accounts=2, balance_entries=4, "
            f"categories=10, subcategories=13, transactions=20, "
            f"categorization_rules=2, "
            f"cash_flow_forecasts=1, forecast_lines={len(cf_lines)}, "
            f"scenarios=2, alerts=3, "
            f"dashboard_widgets=10, dashboard_snapshots=30, "
            f"report_definitions=10, report_executions=3, "
            f"integration_configs=3, ob_connections=1, sync_logs=1, "
            f"invoice_batches=1, invoices=5, webhooks=1"
        )
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
