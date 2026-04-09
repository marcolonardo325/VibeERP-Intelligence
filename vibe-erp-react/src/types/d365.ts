export interface D365Vendor {
  id: string;
  name: string;
  group: string;
  country: string;
}

export interface D365Product {
  itemId: string;
  name: string;
  category: string;
}

export interface D365PurchaseOrder {
  poNumber: string;
  vendor: string;
  vendorId: string;
  status: string;
  currency: string;
}

export interface D365PurchaseAgreement {
  num: string;
  vendorId: string;
  vendor: string;
  cls: string;
  status: string;
  expiry: string;
  title: string;
  currency: string;
}

export interface D365POLine {
  po: string;
  itemId: string;
  item: string;
  vendor: string;
  price: number;
  qty: number;
  amount: number;
}

export interface D365KPIs {
  openPOs: number;
  totalSpend: number;
  activeVendors: number;
  inventoryItems: number;
  totalOnHand: number;
  lowStockAlerts: number;
}

export interface VendorSpend {
  id: string;
  name: string;
  spend: number;
  cumPct: number;
}

export interface CategorySpend {
  category: string;
  spend: number;
}

export interface VendorPerformance {
  id: string;
  name: string;
  totalPOs: number;
  totalSpend: number;
  avgPOValue: number;
  lineCount: number;
  avgLinePrice: number;
  spendShare: number;
  hasAgreement: boolean;
}

export interface ApiResponse<T> {
  data: T;
  count: number;
  source: string;
}

export interface POCreationRequest {
  vendorAccount: string;
  itemNumber: string;
  quantity: number;
  entity: string;
}

export interface POCreationResponse {
  success: boolean;
  poNumber: string;
  vendor: string;
  lineError?: string;
}