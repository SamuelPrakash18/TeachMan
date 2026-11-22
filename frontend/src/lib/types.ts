export interface Me {
  id: string;
  phone: string;
  role: string;
  public_id?: string | null;
  display_name?: string | null;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  role: string;
  public_id?: string | null;
}

export interface InvoiceItem {
  description: string;
  quantity: number;
  unit_paise: number;
  amount_paise: number;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  student_id: string;
  student_name: string;
  parent_name?: string | null;
  invoice_date: string;
  due_date: string;
  total_paise: number;
  paid_paise: number;
  outstanding_paise: number;
  status: string;
  days_overdue: number;
  items: InvoiceItem[];
}

export interface Payment {
  id: string;
  invoice_id: string;
  invoice_number: string;
  amount_paise: number;
  method: string;
  reference?: string | null;
  paid_on: string;
}

export interface Expense {
  id: string;
  title: string;
  category: string;
  amount_paise: number;
  due_date: string;
  paid_on?: string | null;
  status: string;
  is_recurring: boolean;
  notes?: string | null;
  overdue: boolean;
}

export interface Student {
  id: string;
  public_id: string;
  name: string;
  grade: string;
  address?: string | null;
  enrolled_on: string;
  parent_name?: string | null;
  parent_phone?: string | null;
}

export interface Child {
  id: string;
  public_id: string;
  name: string;
  grade: string;
  address?: string | null;
  enrolled_on: string;
}
