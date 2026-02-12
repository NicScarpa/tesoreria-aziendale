export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  email_verified: boolean;
  created_at: string;
}

export interface UserCompany {
  id: string;
  company_id: string;
  company_name: string;
  role: "owner" | "admin" | "editor" | "viewer";
  status: "active" | "invited" | "suspended";
}

export interface Company {
  id: string;
  name: string;
  vat_number: string | null;
  tax_number: string | null;
  country: string;
  address: string | null;
  fiscal_regime: string | null;
  group_vat_number: string | null;
  city: string | null;
  postal_code: string | null;
  province_code: string | null;
  certified_email: string | null;
  destination_code: string | null;
  default_currency: string;
  logo_url: string | null;
  features: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface UserMeResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  email_verified: boolean;
  created_at: string;
  companies: UserCompany[];
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
