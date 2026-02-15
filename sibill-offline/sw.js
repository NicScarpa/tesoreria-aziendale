// Sibill Offline Service Worker
// Generated: 2026-02-11T23:44:50.344941
// API endpoints cached: 116

const CACHE_NAME = 'sibill-offline-v1';
const API_MAP = {
  "/v1/projects/BV5jDAqT69LktXst1HxsNlqVEFs9lBck/settings": [
    {
      "key": "GET:/v1/projects/BV5jDAqT69LktXst1HxsNlqVEFs9lBck/settings",
      "method": "GET",
      "fullUrl": "/v1/projects/BV5jDAqT69LktXst1HxsNlqVEFs9lBck/settings",
      "file": "6dd8915cd2149f7eb95c9e111c0b4d4d.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/v1/p": [
    {
      "key": "POST:/v1/p",
      "method": "POST",
      "fullUrl": "/v1/p",
      "file": "7e2d3d6730b042b474322130cbeaadf4.json",
      "contentType": "application/json"
    }
  ],
  "/api/auth/login": [
    {
      "key": "POST:/api/auth/login",
      "method": "POST",
      "fullUrl": "/api/auth/login",
      "file": "3a09fdebadec19d5ae8d9bbeb88a3efc.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/users/me": [
    {
      "key": "GET:/api/v1/users/me?include=companies%2Ccompanies.companyIdentity%2Ccompanies.companySettings",
      "method": "GET",
      "fullUrl": "/api/v1/users/me?include=companies%2Ccompanies.companyIdentity%2Ccompanies.companySettings",
      "file": "689e6c5c70e15e52073e2f35a9fd5aa7.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/users/me?include=companies%2Ccompanies.companyIdentity%2Ccompanies.companySettings%2Ccompanies.subscriptions",
      "method": "GET",
      "fullUrl": "/api/v1/users/me?include=companies%2Ccompanies.companyIdentity%2Ccompanies.companySettings%2Ccompanies.subscriptions",
      "file": "b56fe260d7317d028c4e7e3488f531b8.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/users/chat-token": [
    {
      "key": "GET:/api/v1/users/chat-token",
      "method": "GET",
      "fullUrl": "/api/v1/users/chat-token",
      "file": "185871f24889e06730c62bfd43822c41.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/companies/": [
    {
      "key": "GET:/api/v1/companies/?filter%5Bid__eq%5D=&include=companyIdentity%2CcompanySettings",
      "method": "GET",
      "fullUrl": "/api/v1/companies/?filter%5Bid__eq%5D=&include=companyIdentity%2CcompanySettings",
      "file": "f58b1d4e6ddf0b3ad955086117a16c3e.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/companies/14196c00-6ac1-4bab-9874-9b01c2fe17a7": [
    {
      "key": "GET:/api/v1/companies/14196c00-6ac1-4bab-9874-9b01c2fe17a7?filter%5Bid__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=companyIdentity%2CcompanySettings",
      "method": "GET",
      "fullUrl": "/api/v1/companies/14196c00-6ac1-4bab-9874-9b01c2fe17a7?filter%5Bid__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=companyIdentity%2CcompanySettings",
      "file": "254d5ef07dc8a5aba342476a0efb2512.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/companies/14196c00-6ac1-4bab-9874-9b01c2fe17a7?include=companyIdentity",
      "method": "GET",
      "fullUrl": "/api/v1/companies/14196c00-6ac1-4bab-9874-9b01c2fe17a7?include=companyIdentity",
      "file": "5df28d5151d7c36a15280bacef1b58a4.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/consents": [
    {
      "key": "GET:/api/v1/consents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bfor_consent.id__empty%5D=true&filter%5Bstatus__notIn%5D=AUTHORIZED%2CDISABLED&include=accounts",
      "method": "GET",
      "fullUrl": "/api/v1/consents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bfor_consent.id__empty%5D=true&filter%5Bstatus__notIn%5D=AUTHORIZED%2CDISABLED&include=accounts",
      "file": "a6c6dedd03d6b0805a7b2fd79b13a95f.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/consents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Binstitution.types__contains%5D=ACCOUNTING&filter%5Bpurpose__eq%5D=SYNC&include=institution%2Caccounts%2Cuser&page%5Bsize%5D=100",
      "method": "GET",
      "fullUrl": "/api/v1/consents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Binstitution.types__contains%5D=ACCOUNTING&filter%5Bpurpose__eq%5D=SYNC&include=institution%2Caccounts%2Cuser&page%5Bsize%5D=100",
      "file": "ed54b35cd4735728de7663bbf5caa09d.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/consents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Binstitution.types__contains%5D=BANKING&filter%5Bpurpose__eq%5D=SYNC&include=institution%2Caccounts%2Cuser&page%5Bsize%5D=100",
      "method": "GET",
      "fullUrl": "/api/v1/consents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Binstitution.types__contains%5D=BANKING&filter%5Bpurpose__eq%5D=SYNC&include=institution%2Caccounts%2Cuser&page%5Bsize%5D=100",
      "file": "93ef742476664e894074d2d0072275c8.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/consents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Binstitution.id__empty%5D=true&filter%5Bpurpose__eq%5D=SYNC&include=institution%2Caccounts%2Cuser&page%5Bsize%5D=100",
      "method": "GET",
      "fullUrl": "/api/v1/consents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Binstitution.id__empty%5D=true&filter%5Bpurpose__eq%5D=SYNC&include=institution%2Caccounts%2Cuser&page%5Bsize%5D=100",
      "file": "8a71fdbf878d1f25eaec927e1d72cbb6.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/accounts": [
    {
      "key": "GET:/api/v1/accounts?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=consent.institution&page%5Bsize%5D=100",
      "method": "GET",
      "fullUrl": "/api/v1/accounts?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=consent.institution&page%5Bsize%5D=100",
      "file": "44224cd1ffd7827c60e7364585a9c9b0.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/user-bank-accounts": [
    {
      "key": "GET:/api/v1/user-bank-accounts?filter%5BbankAccount.company.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bsource__eq%5D=SWAN&filter%5Buser.id__eq%5D=9852007b-9c80-4335-91f7-26902e73e58f&include=user",
      "method": "GET",
      "fullUrl": "/api/v1/user-bank-accounts?filter%5BbankAccount.company.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bsource__eq%5D=SWAN&filter%5Buser.id__eq%5D=9852007b-9c80-4335-91f7-26902e73e58f&include=user",
      "file": "be78b4d4e1dd280b00406a62f3cb2e73.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/user-bank-accounts?filter%5BbankAccount.company.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bsource__eq%5D=SWAN&filter%5Bstatus__in%5D=INVITATION_SENT%2CBINDING_USER_ERROR&filter%5Buser.id__eq%5D=9852007b-9c80-4335-91f7-26902e73e58f&include=user",
      "method": "GET",
      "fullUrl": "/api/v1/user-bank-accounts?filter%5BbankAccount.company.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bsource__eq%5D=SWAN&filter%5Bstatus__in%5D=INVITATION_SENT%2CBINDING_USER_ERROR&filter%5Buser.id__eq%5D=9852007b-9c80-4335-91f7-26902e73e58f&include=user",
      "file": "7f4f7935eb766acd251bc56a44010389.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/payments/metadata": [
    {
      "key": "GET:/api/v1/payments/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bstatus__in%5D=TIMEOUT",
      "method": "GET",
      "fullUrl": "/api/v1/payments/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bstatus__in%5D=TIMEOUT",
      "file": "fe9e1c132e6cf8888875e7cef7ee707f.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/payments/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bstatus__in%5D=TIMEOUT%2CPENDING",
      "method": "GET",
      "fullUrl": "/api/v1/payments/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bstatus__in%5D=TIMEOUT%2CPENDING",
      "file": "8f53bf5708e807e40754b3ac2cd0150e.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/payments/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bstatus__in%5D=ACCEPTED%2CPENDING%2CFAILED%2CSUCCEEDED%2CTIMEOUT",
      "method": "GET",
      "fullUrl": "/api/v1/payments/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bstatus__in%5D=ACCEPTED%2CPENDING%2CFAILED%2CSUCCEEDED%2CTIMEOUT",
      "file": "008f7f7dcab0b6aef2b27e80830da4d5.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/subscriptions": [
    {
      "key": "GET:/api/v1/subscriptions?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&page%5Bsize%5D=25",
      "method": "GET",
      "fullUrl": "/api/v1/subscriptions?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&page%5Bsize%5D=25",
      "file": "9e25031eb591198315753d3078f247ff.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/v1/t": [
    {
      "key": "POST:/v1/t",
      "method": "POST",
      "fullUrl": "/v1/t",
      "file": "91a8516bc40ea93c4f8fe37d2579a40f.json",
      "contentType": "application/json"
    }
  ],
  "/api/v1/categories": [
    {
      "key": "GET:/api/v1/categories?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=subcategories&page%5Bsize%5D=100",
      "method": "GET",
      "fullUrl": "/api/v1/categories?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=subcategories&page%5Bsize%5D=100",
      "file": "e2cecf2a20ed43500aef6920217f02df.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/cashflow/table": [
    {
      "key": "GET:/api/v1/cashflow/table?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2025-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=false&includePastdue=false&timezone=Europe%2FRome",
      "method": "GET",
      "fullUrl": "/api/v1/cashflow/table?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2025-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=false&includePastdue=false&timezone=Europe%2FRome",
      "file": "37eb8ff1d5b54f34463e185a5d93d064.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/cashflow/table?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2024-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=false&includePastdue=false&timezone=Europe%2FRome",
      "method": "GET",
      "fullUrl": "/api/v1/cashflow/table?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2024-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=false&includePastdue=false&timezone=Europe%2FRome",
      "file": "1960425783335c152114b8c934a20c73.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/cashflow/table?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2025-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=true&includePastdue=false&timezone=Europe%2FRome",
      "method": "GET",
      "fullUrl": "/api/v1/cashflow/table?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2025-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=true&includePastdue=false&timezone=Europe%2FRome",
      "file": "6323e8681d94447bccff670452b1dd7d.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/cashflow/table?filter%5Baccount.id__in%5D=fd828a13-c337-4523-9dab-f0acc3f895b6&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2024-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=false&includePastdue=false&timezone=Europe%2FRome",
      "method": "GET",
      "fullUrl": "/api/v1/cashflow/table?filter%5Baccount.id__in%5D=fd828a13-c337-4523-9dab-f0acc3f895b6&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2024-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=false&includePastdue=false&timezone=Europe%2FRome",
      "file": "779c468a12786bac0456452255f5b9b7.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/cashflow/table?filter%5Baccount.id__in%5D=fd828a13-c337-4523-9dab-f0acc3f895b6&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2025-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=true&includePastdue=false&timezone=Europe%2FRome",
      "method": "GET",
      "fullUrl": "/api/v1/cashflow/table?filter%5Baccount.id__in%5D=fd828a13-c337-4523-9dab-f0acc3f895b6&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdate__gte%5D=2025-08-31T22%3A00%3A00.000Z&filter%5Bdate__lte%5D=2026-08-31T21%3A59%3A59.999Z&filter%5BhiddenAt__empty%5D=true&includeBudgets=false&includeOverdue=true&includePastdue=false&timezone=Europe%2FRome",
      "file": "6d0163c0920c9fc141a87a8b45fec66b.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/cashflow/chart": [
    {
      "key": "GET:/api/v1/cashflow/chart?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&from=2025-08-31T22%3A00%3A00.000Z&includeBudgets=false&includeOverdue=false&includePastdue=false&timezone=Europe%2FRome&to=2026-08-31T21%3A59%3A59.999Z",
      "method": "GET",
      "fullUrl": "/api/v1/cashflow/chart?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&from=2025-08-31T22%3A00%3A00.000Z&includeBudgets=false&includeOverdue=false&includePastdue=false&timezone=Europe%2FRome&to=2026-08-31T21%3A59%3A59.999Z",
      "file": "09c6d973387534f99c19de2189045166.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/cashflow/chart?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&from=2025-08-31T22%3A00%3A00.000Z&includeBudgets=false&includeOverdue=true&includePastdue=false&timezone=Europe%2FRome&to=2026-08-31T21%3A59%3A59.999Z",
      "method": "GET",
      "fullUrl": "/api/v1/cashflow/chart?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&from=2025-08-31T22%3A00%3A00.000Z&includeBudgets=false&includeOverdue=true&includePastdue=false&timezone=Europe%2FRome&to=2026-08-31T21%3A59%3A59.999Z",
      "file": "86d31e75d8371be3d588ed4b09ceb19c.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/cashflow/chart?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bid__in%5D=fd828a13-c337-4523-9dab-f0acc3f895b6&from=2025-08-31T22%3A00%3A00.000Z&includeBudgets=false&includeOverdue=true&includePastdue=false&timezone=Europe%2FRome&to=2026-08-31T21%3A59%3A59.999Z",
      "method": "GET",
      "fullUrl": "/api/v1/cashflow/chart?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bid__in%5D=fd828a13-c337-4523-9dab-f0acc3f895b6&from=2025-08-31T22%3A00%3A00.000Z&includeBudgets=false&includeOverdue=true&includePastdue=false&timezone=Europe%2FRome&to=2026-08-31T21%3A59%3A59.999Z",
      "file": "e6a7779c1cbaa88048969d4b63f2a7cc.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/v1/i": [
    {
      "key": "POST:/v1/i",
      "method": "POST",
      "fullUrl": "/v1/i",
      "file": "ce02314030ac58876be171d68c8c10b0.json",
      "contentType": "application/json"
    }
  ],
  "/api/v1/accounts/metadata": [
    {
      "key": "GET:/api/v1/accounts/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bconsent.status__neq%5D=DISABLED&filter%5BignoreBalance__eq%5D=false",
      "method": "GET",
      "fullUrl": "/api/v1/accounts/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bconsent.status__neq%5D=DISABLED&filter%5BignoreBalance__eq%5D=false",
      "file": "9273c5692612f085ce7b88af90786d46.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/accounts/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bconsent.status__neq%5D=DISABLED&filter%5Bid__in%5D=fd828a13-c337-4523-9dab-f0acc3f895b6&filter%5BignoreBalance__eq%5D=false",
      "method": "GET",
      "fullUrl": "/api/v1/accounts/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bconsent.status__neq%5D=DISABLED&filter%5Bid__in%5D=fd828a13-c337-4523-9dab-f0acc3f895b6&filter%5BignoreBalance__eq%5D=false",
      "file": "22fe06d110900842f84fe3ee8962b3fa.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/v1/g": [
    {
      "key": "POST:/v1/g",
      "method": "POST",
      "fullUrl": "/v1/g",
      "file": "8e02a4d47a6697f18e0f02782f0b3952.json",
      "contentType": "application/json"
    }
  ],
  "/api/v1/users/token": [
    {
      "key": "GET:/api/v1/users/token",
      "method": "GET",
      "fullUrl": "/api/v1/users/token",
      "file": "1a722f59ebad786c0fcd1c50d9f33782.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/v1/m": [
    {
      "key": "POST:/v1/m",
      "method": "POST",
      "fullUrl": "/v1/m",
      "file": "82285fa835a8c818f0abc4563cbfd18e.json",
      "contentType": "application/json"
    }
  ],
  "/api/v1/cards": [
    {
      "key": "GET:/api/v1/cards?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=company&page%5Bsize%5D=100",
      "method": "GET",
      "fullUrl": "/api/v1/cards?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=company&page%5Bsize%5D=100",
      "file": "2eacbb5555d14f0b0528a3beb164e754.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/transactions": [
    {
      "key": "GET:/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=-date%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=-date%2C-createdAt%2C-id",
      "file": "48a395d8d444f7aa33d6f17c7f8a82f0.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=-date%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=-date%2C-createdAt%2C-id",
      "file": "cbd3648d7baa6245ffc176e30d1e6096.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0%2Cda25fc87-17fc-4caf-b2ea-477ee1930923&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=-date%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0%2Cda25fc87-17fc-4caf-b2ea-477ee1930923&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=-date%2C-createdAt%2C-id",
      "file": "3c8468da31f14d7b867e84b20a519207.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=da25fc87-17fc-4caf-b2ea-477ee1930923&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=-date%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=da25fc87-17fc-4caf-b2ea-477ee1930923&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=-date%2C-createdAt%2C-id",
      "file": "7c6d388fb00bf8ea0f6b050676b3046b.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=date%2CcreatedAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/transactions?fields%5Breconciliation%5D=&filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=50&sort=date%2CcreatedAt%2C-id",
      "file": "07493f885d711d41fb2a400b30010e5f.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions?filter%5Baccount.hiddenAt__empty%5D=true&filter%5BamountAmount__gt%5D=0&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=20&sort=-date%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/transactions?filter%5Baccount.hiddenAt__empty%5D=true&filter%5BamountAmount__gt%5D=0&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=account%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments&page%5Bcursor%5D=&page%5Bsize%5D=20&sort=-date%2C-createdAt%2C-id",
      "file": "a70186b2f733bf4ff2dfcc95a10f39a7.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/reconciliations/": [
    {
      "key": "GET:/api/v1/reconciliations/?filter%5Bid__in%5D=ce7d0359-70ed-43f3-a838-bec0d4d15b5a%2C1bb4ae85-dcbe-440c-8a5c-d72abb25c375%2Cfc289614-7e1e-4798-ab66-6e059c49641d%2C2e785fd0-3ee2-487f-8f90-0457e1c071c3%2Cd051fa2e-2aeb-4706-963d-d2df1bbaaffc%2Cfbe0c166-5c83-44cd-b24b-64adec905547%2Cc200e9b4-dffb-4c4a-81d3-8d72366e3152%2Cd5e7a653-1951-4c60-8027-f96c7f3bd889%2C17b114f2-1b98-4831-a447-9390bc4d053d%2C259058a6-7a02-4674-a225-77e53f6ce979%2Ca5d4c0a9-d23c-4368-9de1-ed37ed78a25a%2Cd3bb90a7-83b8-4cea-ba67-9f8ac9ee3842%2C16c33ac7-e751-4980-aa23-dbd655c1e390&include=transaction",
      "method": "GET",
      "fullUrl": "/api/v1/reconciliations/?filter%5Bid__in%5D=ce7d0359-70ed-43f3-a838-bec0d4d15b5a%2C1bb4ae85-dcbe-440c-8a5c-d72abb25c375%2Cfc289614-7e1e-4798-ab66-6e059c49641d%2C2e785fd0-3ee2-487f-8f90-0457e1c071c3%2Cd051fa2e-2aeb-4706-963d-d2df1bbaaffc%2Cfbe0c166-5c83-44cd-b24b-64adec905547%2Cc200e9b4-dffb-4c4a-81d3-8d72366e3152%2Cd5e7a653-1951-4c60-8027-f96c7f3bd889%2C17b114f2-1b98-4831-a447-9390bc4d053d%2C259058a6-7a02-4674-a225-77e53f6ce979%2Ca5d4c0a9-d23c-4368-9de1-ed37ed78a25a%2Cd3bb90a7-83b8-4cea-ba67-9f8ac9ee3842%2C16c33ac7-e751-4980-aa23-dbd655c1e390&include=transaction",
      "file": "6cfea9f6ccdd299767906d5d2460e4e7.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/reconciliations/?filter%5Bid__in%5D=16f41e4e-8d35-4602-a58f-4fc91da60f07&include=transaction",
      "method": "GET",
      "fullUrl": "/api/v1/reconciliations/?filter%5Bid__in%5D=16f41e4e-8d35-4602-a58f-4fc91da60f07&include=transaction",
      "file": "4091ec8c1c9cf68bfa905a01e80ddaf5.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/reconciliations/?filter%5Bid__in%5D=1bb4ae85-dcbe-440c-8a5c-d72abb25c375%2C2e785fd0-3ee2-487f-8f90-0457e1c071c3%2Cd051fa2e-2aeb-4706-963d-d2df1bbaaffc%2Cc200e9b4-dffb-4c4a-81d3-8d72366e3152%2C0637a06e-78d6-4c48-b718-e4fd5fab5b6e%2C0d8130c7-a77a-4150-b163-c0dbbc007e82&include=transaction",
      "method": "GET",
      "fullUrl": "/api/v1/reconciliations/?filter%5Bid__in%5D=1bb4ae85-dcbe-440c-8a5c-d72abb25c375%2C2e785fd0-3ee2-487f-8f90-0457e1c071c3%2Cd051fa2e-2aeb-4706-963d-d2df1bbaaffc%2Cc200e9b4-dffb-4c4a-81d3-8d72366e3152%2C0637a06e-78d6-4c48-b718-e4fd5fab5b6e%2C0d8130c7-a77a-4150-b163-c0dbbc007e82&include=transaction",
      "file": "69f275358c11b0073890fb669e3c85ec.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/reconciliations/?filter%5Bid__in%5D=1bb4ae85-dcbe-440c-8a5c-d72abb25c375&include=flow%2Cflow.document%2Cflow.document.counterpart",
      "method": "GET",
      "fullUrl": "/api/v1/reconciliations/?filter%5Bid__in%5D=1bb4ae85-dcbe-440c-8a5c-d72abb25c375&include=flow%2Cflow.document%2Cflow.document.counterpart",
      "file": "4952f59b6982534d380c513ee5dc1ba6.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/reconciliations/?filter%5Bid__in%5D=1bb4ae85-dcbe-440c-8a5c-d72abb25c375&include=transaction",
      "method": "GET",
      "fullUrl": "/api/v1/reconciliations/?filter%5Bid__in%5D=1bb4ae85-dcbe-440c-8a5c-d72abb25c375&include=transaction",
      "file": "a93ccf4d1872075252b9f61ccfe9c02a.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/transactions/reconciliations": [
    {
      "key": "GET:/api/v1/transactions/reconciliations?filter%5Bid__in%5D=cb598e1c-7151-4558-9e23-0bec7df5b334%2C68efb235-a971-4f16-93f9-d48c762587a5%2C3cfff2f9-b3d6-4896-a692-caa37ae853c3%2Ce0ca4d4b-4bda-49a3-8a1f-9344e4d6d403%2C976473d1-713f-4716-8f39-58b484fe7506%2C3708a79a-13a8-4527-9cb0-3809e0299282%2Cf60910f0-35e5-4225-8fee-c5c41b191224%2C88be70e4-e0f3-4f60-97c1-064ca66525b5%2C44091c7a-28f4-4bca-aade-571b5d86b485%2C16093570-8d09-49cf-afe4-0227a7b8a36f%2Cf445ebb1-3bf4-416c-8266-c326277a1f2f%2Cf09b0fb0-3815-4ced-a6f9-f154222836ba%2Cbe2a7ca1-7ebd-430e-862f-11a4a466f93d%2Cbc7a77ca-b138-4585-bc2c-967b22deea99%2C98a32f99-bd6d-4918-8d3b-daf05bee42ef%2C906414c5-27f4-4d3c-8f84-3a25a6ffabff%2C71b79ef2-d278-46c1-a0c7-ee3a31172d40%2C5bb19c3f-97f5-423f-a5e1-5dafe94e0dfc%2C357d454a-2d14-4084-83a2-14d9795f8b23%2C1b5cfab8-934f-491f-bc80-d5cf7cdab346%2C16872ad8-dc20-4f1d-9d9f-d85460b0c108%2C8aefeb6d-4f0f-49fd-a859-cf0d0f1af65f%2C43312e17-8bab-4c22-99dc-8d5d6306ee96&filter%5BverificationStatus__eq%5D=TO_VERIFY",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/reconciliations?filter%5Bid__in%5D=cb598e1c-7151-4558-9e23-0bec7df5b334%2C68efb235-a971-4f16-93f9-d48c762587a5%2C3cfff2f9-b3d6-4896-a692-caa37ae853c3%2Ce0ca4d4b-4bda-49a3-8a1f-9344e4d6d403%2C976473d1-713f-4716-8f39-58b484fe7506%2C3708a79a-13a8-4527-9cb0-3809e0299282%2Cf60910f0-35e5-4225-8fee-c5c41b191224%2C88be70e4-e0f3-4f60-97c1-064ca66525b5%2C44091c7a-28f4-4bca-aade-571b5d86b485%2C16093570-8d09-49cf-afe4-0227a7b8a36f%2Cf445ebb1-3bf4-416c-8266-c326277a1f2f%2Cf09b0fb0-3815-4ced-a6f9-f154222836ba%2Cbe2a7ca1-7ebd-430e-862f-11a4a466f93d%2Cbc7a77ca-b138-4585-bc2c-967b22deea99%2C98a32f99-bd6d-4918-8d3b-daf05bee42ef%2C906414c5-27f4-4d3c-8f84-3a25a6ffabff%2C71b79ef2-d278-46c1-a0c7-ee3a31172d40%2C5bb19c3f-97f5-423f-a5e1-5dafe94e0dfc%2C357d454a-2d14-4084-83a2-14d9795f8b23%2C1b5cfab8-934f-491f-bc80-d5cf7cdab346%2C16872ad8-dc20-4f1d-9d9f-d85460b0c108%2C8aefeb6d-4f0f-49fd-a859-cf0d0f1af65f%2C43312e17-8bab-4c22-99dc-8d5d6306ee96&filter%5BverificationStatus__eq%5D=TO_VERIFY",
      "file": "c0e7f900da6609fa9840fb36fcfc7d62.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions/reconciliations?filter%5Bid__in%5D=c690f9b3-0a4c-49c8-8749-4e6cea03990a%2Cda05ecbc-a0c2-4d4a-850c-5c4c6cc90a85%2C7eb7ba91-5b27-441a-9409-a62260c1624a%2C6d196c44-b07e-4414-8502-92b06c582505%2C6c3530d9-4cfc-4200-8129-562890d7baed%2C26da24ea-8641-42a4-a958-b53dfd55a1b1%2Cba094e9d-634b-4256-8ba1-a0d4e71525e4%2C821bb499-edd1-45bd-b396-b34d591d0c69%2C495c7d0a-5097-409b-89a8-149c15f53042%2C2ea9a7a0-6f33-44ca-9ad7-0c969dca6095%2Cf971bffd-5f91-4f9d-b49e-744628ad1b1c&filter%5BverificationStatus__eq%5D=TO_VERIFY",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/reconciliations?filter%5Bid__in%5D=c690f9b3-0a4c-49c8-8749-4e6cea03990a%2Cda05ecbc-a0c2-4d4a-850c-5c4c6cc90a85%2C7eb7ba91-5b27-441a-9409-a62260c1624a%2C6d196c44-b07e-4414-8502-92b06c582505%2C6c3530d9-4cfc-4200-8129-562890d7baed%2C26da24ea-8641-42a4-a958-b53dfd55a1b1%2Cba094e9d-634b-4256-8ba1-a0d4e71525e4%2C821bb499-edd1-45bd-b396-b34d591d0c69%2C495c7d0a-5097-409b-89a8-149c15f53042%2C2ea9a7a0-6f33-44ca-9ad7-0c969dca6095%2Cf971bffd-5f91-4f9d-b49e-744628ad1b1c&filter%5BverificationStatus__eq%5D=TO_VERIFY",
      "file": "9249bac48b44e4f1541ced9d579c7ffb.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions/reconciliations?filter%5Bid__in%5D=b9c3442b-1298-4684-9ea9-9e3f86fb5d06%2Cf1d1c827-d74e-45d2-aec3-677a140404d6%2Cc8ca963d-0478-43b5-b37f-d89b1dd75653%2Ce25bc8d6-6040-4744-bb64-e864ffe5cb14%2C04551fd5-2513-485d-94f7-bacc1f612200%2Cdce07856-6a54-410d-a889-3e711f2e6565%2Cca18f00b-0d3c-4fce-9026-d6239dc43643%2Cd8455731-a893-4e52-ba9c-e6ba77cb7619%2Cd62da16c-bdad-425f-8423-f686d5f3b9cc&filter%5BverificationStatus__eq%5D=TO_VERIFY",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/reconciliations?filter%5Bid__in%5D=b9c3442b-1298-4684-9ea9-9e3f86fb5d06%2Cf1d1c827-d74e-45d2-aec3-677a140404d6%2Cc8ca963d-0478-43b5-b37f-d89b1dd75653%2Ce25bc8d6-6040-4744-bb64-e864ffe5cb14%2C04551fd5-2513-485d-94f7-bacc1f612200%2Cdce07856-6a54-410d-a889-3e711f2e6565%2Cca18f00b-0d3c-4fce-9026-d6239dc43643%2Cd8455731-a893-4e52-ba9c-e6ba77cb7619%2Cd62da16c-bdad-425f-8423-f686d5f3b9cc&filter%5BverificationStatus__eq%5D=TO_VERIFY",
      "file": "cbdf865a1c8850dd67d134d9106283d1.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions/reconciliations?filter%5Bid__in%5D=ba262dbe-ef7a-44a7-9c98-7d8a3d7368cb%2Ca2aa8e8b-97fe-445f-bf64-1d39ad725e1c%2C943f282a-50a3-4941-b280-91129d9f2b18%2C8f5f1711-5d00-4ee8-9226-4843bdcb05c9%2C103c9a0c-5c82-4175-b1c7-ab7fb271b5e2%2Cf238f402-e369-4a9b-91bd-f12e78a091ea%2Cf66d0245-b36d-40dc-80ec-e11fdde9694a%2Cb00b39a4-7b67-4642-a129-999862eee84d%2C9b645761-8ea5-4f8a-be44-0f96293d79cf%2Cb613e96c-3b47-45af-9bed-f37601a81dee%2C50e16915-2f32-4899-b9aa-6c8374b851c9%2Cdc6c810b-435a-4fb1-825a-cdd5482c87be%2C2efbd793-074c-4b59-a626-7a15a7ceaedc%2C5acab9d7-d1ef-4a19-a2f3-0417e482f6d4%2Cbc055129-3719-47cf-9b0e-e03083a84148%2C3f700d5f-437c-47e6-874b-6128e066e490%2Cb4ec60d6-ca4d-4582-bfd1-63e5a9b91dd6%2C3e90b5a4-3f2f-44e7-a4ce-0416de2352c7%2Ce72626dd-976a-439b-8c25-4b855a830af1%2Ca6a39112-0170-48c8-9124-de6b9661576c%2C8dededd5-5851-4492-907a-fd70745a52df%2C28f0181c-38fe-4cc8-b0e7-5e84dd2ed560%2Cd740a239-48e2-4a16-ae9a-46f4ca00fb3f&filter%5BverificationStatus__eq%5D=TO_VERIFY",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/reconciliations?filter%5Bid__in%5D=ba262dbe-ef7a-44a7-9c98-7d8a3d7368cb%2Ca2aa8e8b-97fe-445f-bf64-1d39ad725e1c%2C943f282a-50a3-4941-b280-91129d9f2b18%2C8f5f1711-5d00-4ee8-9226-4843bdcb05c9%2C103c9a0c-5c82-4175-b1c7-ab7fb271b5e2%2Cf238f402-e369-4a9b-91bd-f12e78a091ea%2Cf66d0245-b36d-40dc-80ec-e11fdde9694a%2Cb00b39a4-7b67-4642-a129-999862eee84d%2C9b645761-8ea5-4f8a-be44-0f96293d79cf%2Cb613e96c-3b47-45af-9bed-f37601a81dee%2C50e16915-2f32-4899-b9aa-6c8374b851c9%2Cdc6c810b-435a-4fb1-825a-cdd5482c87be%2C2efbd793-074c-4b59-a626-7a15a7ceaedc%2C5acab9d7-d1ef-4a19-a2f3-0417e482f6d4%2Cbc055129-3719-47cf-9b0e-e03083a84148%2C3f700d5f-437c-47e6-874b-6128e066e490%2Cb4ec60d6-ca4d-4582-bfd1-63e5a9b91dd6%2C3e90b5a4-3f2f-44e7-a4ce-0416de2352c7%2Ce72626dd-976a-439b-8c25-4b855a830af1%2Ca6a39112-0170-48c8-9124-de6b9661576c%2C8dededd5-5851-4492-907a-fd70745a52df%2C28f0181c-38fe-4cc8-b0e7-5e84dd2ed560%2Cd740a239-48e2-4a16-ae9a-46f4ca00fb3f&filter%5BverificationStatus__eq%5D=TO_VERIFY",
      "file": "35f521bc6a0ed4bcd30b1ab8c21fb6fe.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/payments": [
    {
      "key": "GET:/api/v1/payments?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bstatus__in%5D=ACCEPTED%2CPENDING%2CFAILED%2CSUCCEEDED%2CTIMEOUT&include=account%2Caccount.consent%2Caccount.consent.institution%2Ccounterpart%2Cattachments%2Ctransactions%2Cparent%2Cretry_attempts&page%5Bsize%5D=50&sort=-createdAt",
      "method": "GET",
      "fullUrl": "/api/v1/payments?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bstatus__in%5D=ACCEPTED%2CPENDING%2CFAILED%2CSUCCEEDED%2CTIMEOUT&include=account%2Caccount.consent%2Caccount.consent.institution%2Ccounterpart%2Cattachments%2Ctransactions%2Cparent%2Cretry_attempts&page%5Bsize%5D=50&sort=-createdAt",
      "file": "3ffef4585659fbff8bc77af124e44255.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/institutions": [
    {
      "key": "GET:/api/v1/institutions?filter%5Bsource__eq%5D=SWAN&filter%5Btypes__contains%5D=BANKING&page%5Bsize%5D=20",
      "method": "GET",
      "fullUrl": "/api/v1/institutions?filter%5Bsource__eq%5D=SWAN&filter%5Btypes__contains%5D=BANKING&page%5Bsize%5D=20",
      "file": "23d01172070a4e142b6e3b7e2fe992db.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/9/envelope/": [
    {
      "key": "POST:/api/9/envelope/?sentry_client=sentry.javascript.react%2F10.38.0&sentry_key=bbb036e01d75496b953d4a63de08885f&sentry_version=7",
      "method": "POST",
      "fullUrl": "/api/9/envelope/?sentry_client=sentry.javascript.react%2F10.38.0&sentry_key=bbb036e01d75496b953d4a63de08885f&sentry_version=7",
      "file": "62fbd60f58f07b7c1331b04322e7f67a.json",
      "contentType": "application/json"
    }
  ],
  "/api/v1/reconciliations": [
    {
      "key": "GET:/api/v1/reconciliations?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bsource__in%5D=AUTOMATIC&filter%5Bstatus__eq%5D=VERIFIED&include=flow%2Cflow.document%2Cflow.document.counterpart%2Ctransaction%2Ctransaction.account%2Ctransaction.account.consent%2Ctransaction.account.consent.institution&page%5Bsize%5D=50&sort=-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/reconciliations?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bsource__in%5D=AUTOMATIC&filter%5Bstatus__eq%5D=VERIFIED&include=flow%2Cflow.document%2Cflow.document.counterpart%2Ctransaction%2Ctransaction.account%2Ctransaction.account.consent%2Ctransaction.account.consent.institution&page%5Bsize%5D=50&sort=-createdAt%2C-id",
      "file": "7cea24269622a1769d22f0de7aaf00bf.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/outstanding/chart": [
    {
      "key": "GET:/api/v1/outstanding/chart?count=4&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2COTHER&filter%5Bdocument.hiddenAt__empty%5D=true&frequency=month",
      "method": "GET",
      "fullUrl": "/api/v1/outstanding/chart?count=4&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2COTHER&filter%5Bdocument.hiddenAt__empty%5D=true&frequency=month",
      "file": "5d9cb9e4b1257fc92d349205bd453310.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/flows/metadata": [
    {
      "key": "GET:/api/v1/flows/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY",
      "method": "GET",
      "fullUrl": "/api/v1/flows/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY",
      "file": "7278ef4b5af3bebf7f02f953c17d3b22.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/flows/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bdocument.isInflow__eq%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY",
      "method": "GET",
      "fullUrl": "/api/v1/flows/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bdocument.isInflow__eq%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY",
      "file": "b10f5f795d1a7563fb62c44caf42a753.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/flows": [
    {
      "key": "GET:/api/v1/flows?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY&include=company%2Cdocument%2Cdocument.flows%2Caccount%2Cdocument.category%2Cdocument.subcategory%2Cdocument.counterpart%2Cpayments&page%5Bcursor%5D=&page%5Bsize%5D=35&sort=expectedPaymentDate%2CpaymentDate%2CcreatedAt%2Cid",
      "method": "GET",
      "fullUrl": "/api/v1/flows?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY&include=company%2Cdocument%2Cdocument.flows%2Caccount%2Cdocument.category%2Cdocument.subcategory%2Cdocument.counterpart%2Cpayments&page%5Bcursor%5D=&page%5Bsize%5D=35&sort=expectedPaymentDate%2CpaymentDate%2CcreatedAt%2Cid",
      "file": "c4e49bb123225e78a76fadca4e10a2e3.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/flows?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bid__in%5D=&include=company%2Cdocument%2Cdocument.flows%2Caccount%2Cdocument.category%2Cdocument.subcategory%2Cdocument.counterpart%2Cpayments&page%5Bcursor%5D=&page%5Bsize%5D=35&sort=-expectedPaymentDate%2CpaymentDate%2CcreatedAt%2Cid",
      "method": "GET",
      "fullUrl": "/api/v1/flows?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bid__in%5D=&include=company%2Cdocument%2Cdocument.flows%2Caccount%2Cdocument.category%2Cdocument.subcategory%2Cdocument.counterpart%2Cpayments&page%5Bcursor%5D=&page%5Bsize%5D=35&sort=-expectedPaymentDate%2CpaymentDate%2CcreatedAt%2Cid",
      "file": "42fa55b51e43d3b48927e39f49a3c612.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/flows?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bdocument.isInflow__eq%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY&include=company%2Cdocument%2Cdocument.flows%2Caccount%2Cdocument.category%2Cdocument.subcategory%2Cdocument.counterpart%2Cpayments&page%5Bcursor%5D=&page%5Bsize%5D=35&sort=expectedPaymentDate%2CpaymentDate%2CcreatedAt%2Cid",
      "method": "GET",
      "fullUrl": "/api/v1/flows?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bdocument.isInflow__eq%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY&include=company%2Cdocument%2Cdocument.flows%2Caccount%2Cdocument.category%2Cdocument.subcategory%2Cdocument.counterpart%2Cpayments&page%5Bcursor%5D=&page%5Bsize%5D=35&sort=expectedPaymentDate%2CpaymentDate%2CcreatedAt%2Cid",
      "file": "dd55fb3d36a24aeeeadcdd60a3a1a6b2.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/flows?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bdocument.isInflow__eq%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY&include=company%2Cdocument%2Cdocument.flows%2Caccount%2Cdocument.category%2Cdocument.subcategory%2Cdocument.counterpart%2Cpayments&page%5Bcursor%5D=&page%5Bsize%5D=35&sort=amount%2CpaymentDate%2CcreatedAt%2Cid",
      "method": "GET",
      "fullUrl": "/api/v1/flows?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bdocument.isInflow__eq%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY&include=company%2Cdocument%2Cdocument.flows%2Caccount%2Cdocument.category%2Cdocument.subcategory%2Cdocument.counterpart%2Cpayments&page%5Bcursor%5D=&page%5Bsize%5D=35&sort=amount%2CpaymentDate%2CcreatedAt%2Cid",
      "file": "c011583d9d33e1de4f93278ff90f3747.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/flows/reconciliations": [
    {
      "key": "GET:/api/v1/flows/reconciliations?filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bid__in%5D=a02a5471-a6ea-4729-b4af-8dd0df14d8c8%2Ce0bc4d78-acd9-4ca1-b518-444a922455ec%2Cd3ac8999-7b8a-4f77-b029-97098191efa6%2Ca7de9345-d7a1-4ff7-ae36-14d7f1339bd7%2C97fa2601-82eb-4566-ae7c-d1e0ce394e50%2Cb365cdea-a625-48d3-a504-850f8880de4f%2C0b4b5f60-4e1d-4812-bfde-ee729afc592f%2Cd982f19d-14f1-4bc8-8975-38ed66dc39e8%2C5bd9d6a6-1097-40bf-b85f-24f33454e063%2C5bdffd7d-6a7f-4a3c-b46a-ebf86f4168f5%2C9d7b0ea3-68b8-4eb4-8f4e-1c9c29950afd%2C7faed611-18e1-4b16-9693-5f66c230ab27%2Ce406869c-ec65-49f4-a81b-fbc37b818bf1%2C96eb1146-8068-483a-bbe7-26ee1148f6b5%2C98d8d422-003a-4c07-b062-c87ecf8b184d%2C86f6c196-d295-4c65-92bf-37c97afdfdf2%2C6c5b9f21-7a63-49ff-b117-02ee4b66c777%2C05479e1c-a1e2-41f3-b65b-f9d179c6e69d%2C684cc284-ce0a-4f00-aed6-2ee645e31ae2%2C8cba9b39-d240-4956-9273-a57130e4de0c&filter%5BpaymentStatus__eq%5D=TO_PAY",
      "method": "GET",
      "fullUrl": "/api/v1/flows/reconciliations?filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bid__in%5D=a02a5471-a6ea-4729-b4af-8dd0df14d8c8%2Ce0bc4d78-acd9-4ca1-b518-444a922455ec%2Cd3ac8999-7b8a-4f77-b029-97098191efa6%2Ca7de9345-d7a1-4ff7-ae36-14d7f1339bd7%2C97fa2601-82eb-4566-ae7c-d1e0ce394e50%2Cb365cdea-a625-48d3-a504-850f8880de4f%2C0b4b5f60-4e1d-4812-bfde-ee729afc592f%2Cd982f19d-14f1-4bc8-8975-38ed66dc39e8%2C5bd9d6a6-1097-40bf-b85f-24f33454e063%2C5bdffd7d-6a7f-4a3c-b46a-ebf86f4168f5%2C9d7b0ea3-68b8-4eb4-8f4e-1c9c29950afd%2C7faed611-18e1-4b16-9693-5f66c230ab27%2Ce406869c-ec65-49f4-a81b-fbc37b818bf1%2C96eb1146-8068-483a-bbe7-26ee1148f6b5%2C98d8d422-003a-4c07-b062-c87ecf8b184d%2C86f6c196-d295-4c65-92bf-37c97afdfdf2%2C6c5b9f21-7a63-49ff-b117-02ee4b66c777%2C05479e1c-a1e2-41f3-b65b-f9d179c6e69d%2C684cc284-ce0a-4f00-aed6-2ee645e31ae2%2C8cba9b39-d240-4956-9273-a57130e4de0c&filter%5BpaymentStatus__eq%5D=TO_PAY",
      "file": "305de953420c61de64ed76fd96bc2ff8.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/documents-dashboard/summary": [
    {
      "key": "GET:/api/v1/documents-dashboard/summary?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BcreationDate__gte%5D=2026-01-01&filter%5BcreationDate__lte%5D=2026-12-31&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CBILL%2CSELF_INVOICE%2CPARCEL&filter%5BhiddenAt__empty%5D=true&filter%5Bstatus__notIn%5D=DRAFT%2CDISCARDED",
      "method": "GET",
      "fullUrl": "/api/v1/documents-dashboard/summary?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BcreationDate__gte%5D=2026-01-01&filter%5BcreationDate__lte%5D=2026-12-31&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CBILL%2CSELF_INVOICE%2CPARCEL&filter%5BhiddenAt__empty%5D=true&filter%5Bstatus__notIn%5D=DRAFT%2CDISCARDED",
      "file": "29d70c1bee0a4e0d14572f02e57a55ae.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/documents-dashboard/summary?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BcreationDate__gte%5D=2025-01-01&filter%5BcreationDate__lte%5D=2025-12-31&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CBILL%2CSELF_INVOICE%2CPARCEL&filter%5BhiddenAt__empty%5D=true&filter%5Bstatus__notIn%5D=DRAFT%2CDISCARDED",
      "method": "GET",
      "fullUrl": "/api/v1/documents-dashboard/summary?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BcreationDate__gte%5D=2025-01-01&filter%5BcreationDate__lte%5D=2025-12-31&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CBILL%2CSELF_INVOICE%2CPARCEL&filter%5BhiddenAt__empty%5D=true&filter%5Bstatus__notIn%5D=DRAFT%2CDISCARDED",
      "file": "7b56e697a8ffcee8bb9cc1348bc07cba.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/documents": [
    {
      "key": "GET:/api/v1/documents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentDirection__eq%5D=RECEIVED&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE&filter%5Bstatus__in%5D=CREATED%2CDELIVERED%2CDISCARDED%2CNOT_DELIVERED%2CSENT&include=flows%2Ccategory%2Csubcategory%2Ccounterpart&page%5Bsize%5D=50&sort=-searchDate%2C-creationDate%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/documents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentDirection__eq%5D=RECEIVED&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE&filter%5Bstatus__in%5D=CREATED%2CDELIVERED%2CDISCARDED%2CNOT_DELIVERED%2CSENT&include=flows%2Ccategory%2Csubcategory%2Ccounterpart&page%5Bsize%5D=50&sort=-searchDate%2C-creationDate%2C-createdAt%2C-id",
      "file": "f72b620d6fb92a5d1b0280f0b8ea95ef.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/documents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentDirection__eq%5D=RECEIVED&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE&filter%5BpaymentStatus__eq%5D=PAID&filter%5Bstatus__in%5D=CREATED%2CDELIVERED%2CDISCARDED%2CNOT_DELIVERED%2CSENT&include=flows%2Ccategory%2Csubcategory%2Ccounterpart&page%5Bsize%5D=50&sort=-searchDate%2C-creationDate%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/documents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentDirection__eq%5D=RECEIVED&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE&filter%5BpaymentStatus__eq%5D=PAID&filter%5Bstatus__in%5D=CREATED%2CDELIVERED%2CDISCARDED%2CNOT_DELIVERED%2CSENT&include=flows%2Ccategory%2Csubcategory%2Ccounterpart&page%5Bsize%5D=50&sort=-searchDate%2C-creationDate%2C-createdAt%2C-id",
      "file": "b75d5d5b9bef473070a9fc5e52b41707.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/documents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentDirection__eq%5D=ISSUED&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE&filter%5Bstatus__in%5D=CREATED%2CSENT%2CDELIVERED%2CNOT_DELIVERED&include=flows%2Ccategory%2Csubcategory%2Ccounterpart&page%5Bsize%5D=50&sort=-searchDate%2C-creationDate%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/documents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentDirection__eq%5D=ISSUED&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE&filter%5Bstatus__in%5D=CREATED%2CSENT%2CDELIVERED%2CNOT_DELIVERED&include=flows%2Ccategory%2Csubcategory%2Ccounterpart&page%5Bsize%5D=50&sort=-searchDate%2C-creationDate%2C-createdAt%2C-id",
      "file": "599650c51344a8a7c9ffe90202b807eb.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/documents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentType__in%5D=BILL&include=flows%2Ccategory%2Csubcategory%2Ccounterpart&page%5Bsize%5D=50&sort=-creationDate%2C-createdAt%2C-id",
      "method": "GET",
      "fullUrl": "/api/v1/documents?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentType__in%5D=BILL&include=flows%2Ccategory%2Csubcategory%2Ccounterpart&page%5Bsize%5D=50&sort=-creationDate%2C-createdAt%2C-id",
      "file": "336870f14e5a07bd575d9a014ccebad5.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/documents/metadata": [
    {
      "key": "GET:/api/v1/documents/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentDirection__eq%5D=RECEIVED&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE&filter%5BpaymentStatus__eq%5D=PAID&filter%5Bstatus__in%5D=CREATED%2CDELIVERED%2CDISCARDED%2CNOT_DELIVERED%2CSENT",
      "method": "GET",
      "fullUrl": "/api/v1/documents/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentDirection__eq%5D=RECEIVED&filter%5BdocumentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE&filter%5BpaymentStatus__eq%5D=PAID&filter%5Bstatus__in%5D=CREATED%2CDELIVERED%2CDISCARDED%2CNOT_DELIVERED%2CSENT",
      "file": "7fd7f7e82860ac228ed6d4e5df27193e.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/documents/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentType__in%5D=BILL",
      "method": "GET",
      "fullUrl": "/api/v1/documents/metadata?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BdocumentType__in%5D=BILL",
      "file": "a0152d5f28052c8f7078f67d211c4cba.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/documents/e513d657-7cdf-401d-9a24-ae47d87ac24d": [
    {
      "key": "GET:/api/v1/documents/e513d657-7cdf-401d-9a24-ae47d87ac24d?include=attachments%2Ccategory%2Ccompany%2Ccompany.companyIdentity%2Ccounterpart%2Cflows%2Cflows.account%2Cflows.reconciliations%2Cflows.payments%2Csubcategory%2Crelated%2CreferencedBy",
      "method": "GET",
      "fullUrl": "/api/v1/documents/e513d657-7cdf-401d-9a24-ae47d87ac24d?include=attachments%2Ccategory%2Ccompany%2Ccompany.companyIdentity%2Ccounterpart%2Cflows%2Cflows.account%2Cflows.reconciliations%2Cflows.payments%2Csubcategory%2Crelated%2CreferencedBy",
      "file": "e0c1912bc8902249d55fc076361fe25d.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/counterparts": [
    {
      "key": "GET:/api/v1/counterparts?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bkind__neq%5D=VIRTUAL&filter%5Bparent.id__empty%5D=true&include=account%2Cchildren%2CissuedCategory%2CissuedSubcategory%2CreceivedCategory%2CreceivedSubcategory&page%5Bsize%5D=50&sort=company_name%2Cid",
      "method": "GET",
      "fullUrl": "/api/v1/counterparts?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bkind__neq%5D=VIRTUAL&filter%5Bparent.id__empty%5D=true&include=account%2Cchildren%2CissuedCategory%2CissuedSubcategory%2CreceivedCategory%2CreceivedSubcategory&page%5Bsize%5D=50&sort=company_name%2Cid",
      "file": "cc5d8b62321880746f97f834f8e29192.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/counterparts?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bkind__neq%5D=VIRTUAL&filter%5Bparent.id__empty%5D=true&sort=company_name%2Cid",
      "method": "GET",
      "fullUrl": "/api/v1/counterparts?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bkind__neq%5D=VIRTUAL&filter%5Bparent.id__empty%5D=true&sort=company_name%2Cid",
      "file": "67ce86d602af6f7f209294c6c1888a05.json",
      "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-16"
    },
    {
      "key": "GET:/api/v1/counterparts?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bkind__eq%5D=VIRTUAL&include=receivedCategory%2CreceivedSubcategory&page%5Bsize%5D=50",
      "method": "GET",
      "fullUrl": "/api/v1/counterparts?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bkind__eq%5D=VIRTUAL&include=receivedCategory%2CreceivedSubcategory&page%5Bsize%5D=50",
      "file": "3d176b13b47c43ee70410e858e0b5fd4.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/rules": [
    {
      "key": "GET:/api/v1/rules?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdirection__eq%5D=INFLOW&filter%5BruleType__eq%5D=TRANSACTION&include=updatedBy%2CcreatedBy&page%5Bsize%5D=20&sort=-priority",
      "method": "GET",
      "fullUrl": "/api/v1/rules?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdirection__eq%5D=INFLOW&filter%5BruleType__eq%5D=TRANSACTION&include=updatedBy%2CcreatedBy&page%5Bsize%5D=20&sort=-priority",
      "file": "ab35e1e79dacf2451734be83513cea27.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/rules?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BruleType__eq%5D=TRANSACTION&include=updatedBy%2CcreatedBy&page%5Bsize%5D=20&sort=-priority",
      "method": "GET",
      "fullUrl": "/api/v1/rules?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BruleType__eq%5D=TRANSACTION&include=updatedBy%2CcreatedBy&page%5Bsize%5D=20&sort=-priority",
      "file": "73647094982a33bdca5b7ae3ccb91f34.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/rules?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdirection__eq%5D=OUTFLOW&filter%5BruleType__eq%5D=TRANSACTION&include=updatedBy%2CcreatedBy&page%5Bsize%5D=20&sort=-priority",
      "method": "GET",
      "fullUrl": "/api/v1/rules?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdirection__eq%5D=OUTFLOW&filter%5BruleType__eq%5D=TRANSACTION&include=updatedBy%2CcreatedBy&page%5Bsize%5D=20&sort=-priority",
      "file": "babb7fa81bf8bf7a39990763327215e6.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/rules?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BruleType__eq%5D=DOCUMENT&include=updatedBy%2CcreatedBy&page%5Bsize%5D=20&sort=-priority",
      "method": "GET",
      "fullUrl": "/api/v1/rules?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5BruleType__eq%5D=DOCUMENT&include=updatedBy%2CcreatedBy&page%5Bsize%5D=20&sort=-priority",
      "file": "ae381079dfbaa20097b94ba59506d3c9.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/transactions/proposed-rules": [
    {
      "key": "GET:/api/v1/transactions/proposed-rules?filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/proposed-rules?filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7",
      "file": "efe4ac70ce82d24739872a1fedff35bf.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/transactions/metadata": [
    {
      "key": "GET:/api/v1/transactions/metadata?filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/metadata?filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0",
      "file": "a02c20a4288438e98913ac542904b97d.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions/metadata?filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0%2Cda25fc87-17fc-4caf-b2ea-477ee1930923",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/metadata?filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=6c3f56ee-0b4e-4a16-98f9-3ab2e2bf0cc0%2Cda25fc87-17fc-4caf-b2ea-477ee1930923",
      "file": "e7a01d3a474a676b8d8c7d6948b1c11d.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions/metadata?filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=da25fc87-17fc-4caf-b2ea-477ee1930923",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/metadata?filter%5Baccount.hiddenAt__empty%5D=true&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bhas_category_id__in%5D=da25fc87-17fc-4caf-b2ea-477ee1930923",
      "file": "8ce8b7d14f49363d67625f228c920735.json",
      "contentType": "application/json; charset=utf-8"
    },
    {
      "key": "GET:/api/v1/transactions/metadata?filter%5Baccount.hiddenAt__empty%5D=true&filter%5BamountAmount__gt%5D=0&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/metadata?filter%5Baccount.hiddenAt__empty%5D=true&filter%5BamountAmount__gt%5D=0&filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7",
      "file": "3f7e5d13dcf2c86de92689bae6885e83.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/company-users": [
    {
      "key": "GET:/api/v1/company-users?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=user",
      "method": "GET",
      "fullUrl": "/api/v1/company-users?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=user",
      "file": "e3fbc96a676832f472813d37f14ef116.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/transactions/cb598e1c-7151-4558-9e23-0bec7df5b334": [
    {
      "key": "GET:/api/v1/transactions/cb598e1c-7151-4558-9e23-0bec7df5b334?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/cb598e1c-7151-4558-9e23-0bec7df5b334?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "97fca7ae25d76e80e40c8fce661a63b3.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/68efb235-a971-4f16-93f9-d48c762587a5": [
    {
      "key": "GET:/api/v1/transactions/68efb235-a971-4f16-93f9-d48c762587a5?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/68efb235-a971-4f16-93f9-d48c762587a5?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "5bca3dca0c2c4ff349c2aef741745541.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/3cfff2f9-b3d6-4896-a692-caa37ae853c3": [
    {
      "key": "GET:/api/v1/transactions/3cfff2f9-b3d6-4896-a692-caa37ae853c3?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/3cfff2f9-b3d6-4896-a692-caa37ae853c3?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "dbe35868b56424403224971534191009.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/e0ca4d4b-4bda-49a3-8a1f-9344e4d6d403": [
    {
      "key": "GET:/api/v1/transactions/e0ca4d4b-4bda-49a3-8a1f-9344e4d6d403?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/e0ca4d4b-4bda-49a3-8a1f-9344e4d6d403?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "efd24a7433e06124487c5ae4feaef108.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/976473d1-713f-4716-8f39-58b484fe7506": [
    {
      "key": "GET:/api/v1/transactions/976473d1-713f-4716-8f39-58b484fe7506?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/976473d1-713f-4716-8f39-58b484fe7506?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "b3770321b4e8fb098a7d517418c915fe.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/3708a79a-13a8-4527-9cb0-3809e0299282": [
    {
      "key": "GET:/api/v1/transactions/3708a79a-13a8-4527-9cb0-3809e0299282?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/3708a79a-13a8-4527-9cb0-3809e0299282?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "fbc8057f3f2f0f53c0cbfd27e239e12c.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/f60910f0-35e5-4225-8fee-c5c41b191224": [
    {
      "key": "GET:/api/v1/transactions/f60910f0-35e5-4225-8fee-c5c41b191224?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/f60910f0-35e5-4225-8fee-c5c41b191224?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "87ec87031839ba52ceff7942814b1c99.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/88be70e4-e0f3-4f60-97c1-064ca66525b5": [
    {
      "key": "GET:/api/v1/transactions/88be70e4-e0f3-4f60-97c1-064ca66525b5?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/88be70e4-e0f3-4f60-97c1-064ca66525b5?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "1c7635ceffca29a03408e6eefe9962f4.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/44091c7a-28f4-4bca-aade-571b5d86b485": [
    {
      "key": "GET:/api/v1/transactions/44091c7a-28f4-4bca-aade-571b5d86b485?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/44091c7a-28f4-4bca-aade-571b5d86b485?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "eeea50a9269b403671c83daf18af6727.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/16093570-8d09-49cf-afe4-0227a7b8a36f": [
    {
      "key": "GET:/api/v1/transactions/16093570-8d09-49cf-afe4-0227a7b8a36f?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/16093570-8d09-49cf-afe4-0227a7b8a36f?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "c07b083ee022f23af3a9b63f94c46ad7.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/f445ebb1-3bf4-416c-8266-c326277a1f2f": [
    {
      "key": "GET:/api/v1/transactions/f445ebb1-3bf4-416c-8266-c326277a1f2f?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/f445ebb1-3bf4-416c-8266-c326277a1f2f?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "e6356ef41678d9873e024a0a0fa843d9.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/f09b0fb0-3815-4ced-a6f9-f154222836ba": [
    {
      "key": "GET:/api/v1/transactions/f09b0fb0-3815-4ced-a6f9-f154222836ba?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/f09b0fb0-3815-4ced-a6f9-f154222836ba?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "1ff01126c59cb7125bf429c3a871be76.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/be2a7ca1-7ebd-430e-862f-11a4a466f93d": [
    {
      "key": "GET:/api/v1/transactions/be2a7ca1-7ebd-430e-862f-11a4a466f93d?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/be2a7ca1-7ebd-430e-862f-11a4a466f93d?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "335e5edf9848ac9136a50ced28b6a007.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/bc7a77ca-b138-4585-bc2c-967b22deea99": [
    {
      "key": "GET:/api/v1/transactions/bc7a77ca-b138-4585-bc2c-967b22deea99?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/bc7a77ca-b138-4585-bc2c-967b22deea99?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "1b361ed7c58f2f8903e3c68e29044ec9.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/98a32f99-bd6d-4918-8d3b-daf05bee42ef": [
    {
      "key": "GET:/api/v1/transactions/98a32f99-bd6d-4918-8d3b-daf05bee42ef?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/98a32f99-bd6d-4918-8d3b-daf05bee42ef?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "967916b4e1615e1548a62aa21bd9d493.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/906414c5-27f4-4d3c-8f84-3a25a6ffabff": [
    {
      "key": "GET:/api/v1/transactions/906414c5-27f4-4d3c-8f84-3a25a6ffabff?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/906414c5-27f4-4d3c-8f84-3a25a6ffabff?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "9b60af5baa15834ee40ab80701f9eea3.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/71b79ef2-d278-46c1-a0c7-ee3a31172d40": [
    {
      "key": "GET:/api/v1/transactions/71b79ef2-d278-46c1-a0c7-ee3a31172d40?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/71b79ef2-d278-46c1-a0c7-ee3a31172d40?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "97a6e0cb46984a454b8ff7d0ab595bd0.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/5bb19c3f-97f5-423f-a5e1-5dafe94e0dfc": [
    {
      "key": "GET:/api/v1/transactions/5bb19c3f-97f5-423f-a5e1-5dafe94e0dfc?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/5bb19c3f-97f5-423f-a5e1-5dafe94e0dfc?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "3dd3d93f7844baae2a8a07ad2405e88c.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/357d454a-2d14-4084-83a2-14d9795f8b23": [
    {
      "key": "GET:/api/v1/transactions/357d454a-2d14-4084-83a2-14d9795f8b23?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/357d454a-2d14-4084-83a2-14d9795f8b23?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "34c6a1fdca47733443b2dc5395115377.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/1b5cfab8-934f-491f-bc80-d5cf7cdab346": [
    {
      "key": "GET:/api/v1/transactions/1b5cfab8-934f-491f-bc80-d5cf7cdab346?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/1b5cfab8-934f-491f-bc80-d5cf7cdab346?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "d7baeaee11fb1fbf66adff742449bb97.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/16872ad8-dc20-4f1d-9d9f-d85460b0c108": [
    {
      "key": "GET:/api/v1/transactions/16872ad8-dc20-4f1d-9d9f-d85460b0c108?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/16872ad8-dc20-4f1d-9d9f-d85460b0c108?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "1dab57d9e6bcae8ed50692ee9191a2bc.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/8aefeb6d-4f0f-49fd-a859-cf0d0f1af65f": [
    {
      "key": "GET:/api/v1/transactions/8aefeb6d-4f0f-49fd-a859-cf0d0f1af65f?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/8aefeb6d-4f0f-49fd-a859-cf0d0f1af65f?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "c00fe20eac5c5c870e687db42640e1f2.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/43312e17-8bab-4c22-99dc-8d5d6306ee96": [
    {
      "key": "GET:/api/v1/transactions/43312e17-8bab-4c22-99dc-8d5d6306ee96?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/43312e17-8bab-4c22-99dc-8d5d6306ee96?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "9bdbd273570bf09fdca8bcbaa8bc3ac9.json",
      "contentType": "application/vnd.api+json"
    }
  ],
  "/api/v1/transactions/ba262dbe-ef7a-44a7-9c98-7d8a3d7368cb": [
    {
      "key": "GET:/api/v1/transactions/ba262dbe-ef7a-44a7-9c98-7d8a3d7368cb?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/ba262dbe-ef7a-44a7-9c98-7d8a3d7368cb?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "49a4048cfb202c1e3fa39e013d617d4d.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/transactions/a2aa8e8b-97fe-445f-bf64-1d39ad725e1c": [
    {
      "key": "GET:/api/v1/transactions/a2aa8e8b-97fe-445f-bf64-1d39ad725e1c?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/a2aa8e8b-97fe-445f-bf64-1d39ad725e1c?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "7c8d1641d962c514c24452b0504d4fe4.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/transactions/943f282a-50a3-4941-b280-91129d9f2b18": [
    {
      "key": "GET:/api/v1/transactions/943f282a-50a3-4941-b280-91129d9f2b18?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "method": "GET",
      "fullUrl": "/api/v1/transactions/943f282a-50a3-4941-b280-91129d9f2b18?fields%5Breconciliation%5D=&include=account%2Caccount.bookkeepingAccount%2Caccount.consent.institution%2Callocations%2Callocations.category%2Callocations.subcategory%2Cattachments%2Ccard%2Ccategory%2Creconciliations%2Csubcategory%2Cpayment%2Cpayment.attachments",
      "file": "74d4b3d4a6ab95cca9c13813b1c0caeb.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/documents/1dba5028-15b3-4954-81f9-c8d36cba6c8b": [
    {
      "key": "GET:/api/v1/documents/1dba5028-15b3-4954-81f9-c8d36cba6c8b?include=attachments%2Ccategory%2Ccompany%2Ccompany.companyIdentity%2Ccounterpart%2Cflows%2Cflows.account%2Cflows.reconciliations%2Cflows.payments%2Csubcategory%2Crelated%2CreferencedBy",
      "method": "GET",
      "fullUrl": "/api/v1/documents/1dba5028-15b3-4954-81f9-c8d36cba6c8b?include=attachments%2Ccategory%2Ccompany%2Ccompany.companyIdentity%2Ccounterpart%2Cflows%2Cflows.account%2Cflows.reconciliations%2Cflows.payments%2Csubcategory%2Crelated%2CreferencedBy",
      "file": "3e01bd710e22b7878f39f4b04f4e0c59.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/recurrences": [
    {
      "key": "GET:/api/v1/recurrences?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=account%2Caccount.consent%2Caccount.consent.institution%2Ccategory%2Csubcategory&page%5Bsize%5D=100",
      "method": "GET",
      "fullUrl": "/api/v1/recurrences?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&include=account%2Caccount.consent%2Caccount.consent.institution%2Ccategory%2Csubcategory&page%5Bsize%5D=100",
      "file": "3ba1df981a8dcfefde2df7ae44950165.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/consents/d689324c-d4aa-4734-97ff-16d31e9b6807": [
    {
      "key": "GET:/api/v1/consents/d689324c-d4aa-4734-97ff-16d31e9b6807?include=institution",
      "method": "GET",
      "fullUrl": "/api/v1/consents/d689324c-d4aa-4734-97ff-16d31e9b6807?include=institution",
      "file": "e73d2d2cd04a31b371256cfc26c87320.json",
      "contentType": "application/json; charset=utf-8"
    }
  ],
  "/api/v1/outstanding/export": [
    {
      "key": "GET:/api/v1/outstanding/export?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bdocument.isInflow__eq%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY",
      "method": "GET",
      "fullUrl": "/api/v1/outstanding/export?filter%5Bcompany.id__eq%5D=14196c00-6ac1-4bab-9874-9b01c2fe17a7&filter%5Bdocument.documentType__in%5D=INVOICE%2CCREDIT_NOTE%2CDEBIT_NOTE%2CPARCEL%2CSELF_INVOICE%2CBILL&filter%5Bdocument.hiddenAt__empty%5D=true&filter%5Bdocument.isInflow__eq%5D=true&filter%5BpaymentStatus__eq%5D=TO_PAY",
      "file": "8221b7e6e006af10fe590a2425a956a9.json",
      "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-16"
    }
  ]
};

// Known static file extensions
const STATIC_EXTENSIONS = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.json', '.map'];

// Install: pre-cache all API responses
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Sibill Offline Service Worker');
  self.skipWaiting();
});

// Activate: take control immediately
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating - taking control');
  event.waitUntil(clients.claim());
});

// Normalize URL for matching
function normalizeUrl(url) {
  try {
    const parsed = new URL(url);
    const params = new URLSearchParams(parsed.search);
    const sorted = new URLSearchParams([...params.entries()].sort());
    return parsed.pathname + (sorted.toString() ? '?' + sorted.toString() : '');
  } catch(e) {
    return url;
  }
}

// Find matching API response
function findMatch(method, url) {
  const parsed = new URL(url);
  const path = parsed.pathname;
  const fullNorm = normalizeUrl(url);

  const candidates = API_MAP[path];
  if (!candidates) return null;

  // Try exact match first (method + path + params)
  const exactKey = method + ':' + fullNorm;
  for (const c of candidates) {
    if (c.key === exactKey) return c;
  }

  // Try method + path match (ignore params)
  for (const c of candidates) {
    if (c.method === method) return c;
  }

  return null;
}

// Check if path looks like a static file
function isStaticFile(pathname) {
  return STATIC_EXTENSIONS.some(ext => pathname.endsWith(ext));
}

// Fetch interceptor
self.addEventListener('fetch', (event) => {
  const url = event.request.url;
  const method = event.request.method;

  // Block tracking/analytics domains
  const trackingDomains = ['google', 'facebook', 'segment', 'hotjar', 'sentry', 'intercom', 'crisp', 'mixpanel', 'analytics', 'customer.io', 'customerioforms', 'gist.build', 'hubapi.com', 'hscollectedforms.net', 'hs-banner.com', 'satismeter.com', 'exceptions.sibill.com', 'realtime.cloud.gist.build'];
  try {
    const hostname = new URL(url).hostname;
    if (trackingDomains.some(d => hostname.includes(d))) {
      event.respondWith(new Response('', { status: 204 }));
      return;
    }
  } catch(e) {}

  // Try to match API call
  const match = findMatch(method, url);

  if (match) {
    event.respondWith(
      fetch('/api-responses/' + match.file)
        .then(r => r.text())
        .then(body => {
          return new Response(body, {
            status: 200,
            headers: {
              'Content-Type': match.contentType || 'application/json',
              'Access-Control-Allow-Origin': '*',
              'X-Sibill-Offline': 'cached',
            }
          });
        })
        .catch(err => {
          console.warn('[SW] [CACHE-ERROR]', method, url, err);
          return new Response(JSON.stringify({error: 'cache miss'}), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          });
        })
    );
    return;
  }

  // Try to serve static assets locally
  try {
    const pathname = new URL(url).pathname;

    // Static file or known path prefix — try to serve directly
    if (isStaticFile(pathname) || pathname.startsWith('/assets/') || pathname.startsWith('/api-responses/') || pathname.startsWith('/favicon/')) {
      event.respondWith(
        fetch(pathname).then(r => {
          if (r.ok) return r;
          console.warn('[SW] [MISS]', method, url);
          return new Response('', { status: 200 });
        }).catch(() => {
          console.warn('[SW] [MISS]', method, url);
          return new Response('', { status: 200 });
        })
      );
      return;
    }

    // SPA fallback: for non-file routes, serve the app shell HTML
    // This is critical for React Router to work — all routes like
    // /cashflow, /counterparts, /invoices/dashboard etc. need the HTML shell
    if (method === 'GET' && pathname !== '/' && pathname !== '/index.html' && pathname !== '/sw.js') {
      event.respondWith(
        fetch('/app-shell.html').then(r => {
          if (r.ok) {
            return new Response(r.body, {
              status: 200,
              headers: { 'Content-Type': 'text/html; charset=utf-8' }
            });
          }
          return r;
        }).catch(() => {
          console.warn('[SW] [MISS] SPA fallback failed for', pathname);
          return new Response('', { status: 200 });
        })
      );
      return;
    }
  } catch(e) {}

  // Fallback: log miss and return empty
  console.warn('[SW] [MISS]', method, url);
  event.respondWith(new Response('', { status: 200 }));
});
