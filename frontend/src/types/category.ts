export interface Subcategory {
  id: string;
  category_id: string;
  company_id: string;
  name: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  company_id: string;
  name: string;
  color: string;
  sort_order: number;
  is_system: boolean;
  subcategories: Subcategory[];
  created_at: string;
  updated_at: string;
}
