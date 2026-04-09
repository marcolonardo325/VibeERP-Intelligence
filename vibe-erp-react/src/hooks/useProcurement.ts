import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import type { 
  D365Vendor, 
  D365Product,
  D365PurchaseOrder,
  D365PurchaseAgreement,
  D365POLine,
  D365KPIs,
  VendorSpend,
  VendorPerformance,
  CategorySpend,
  ApiResponse, 
  POCreationRequest, 
  POCreationResponse 
} from '../types/d365';

const API = 'http://localhost:5000/api';

export const useProcurement = () => {
  const [vendors, setVendors] = useState<D365Vendor[]>([]);
  const [products, setProducts] = useState<D365Product[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<D365PurchaseOrder[]>([]);
  const [purchaseAgreements, setPurchaseAgreements] = useState<D365PurchaseAgreement[]>([]);
  const [poLines, setPOLines] = useState<D365POLine[]>([]);
  const [kpis, setKpis] = useState<D365KPIs | null>(null);
  const [vendorSpend, setVendorSpend] = useState<VendorSpend[]>([]);
  const [categorySpend, setCategorySpend] = useState<CategorySpend[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [vendorRes, productRes, poRes, kpiRes, spendRes, agreementRes, poLineRes, catSpendRes] = await Promise.allSettled([
        axios.get<ApiResponse<D365Vendor[]>>(`${API}/vendors`),
        axios.get<ApiResponse<D365Product[]>>(`${API}/products`),
        axios.get<ApiResponse<D365PurchaseOrder[]>>(`${API}/purchase-orders`),
        axios.get<{ data: D365KPIs }>(`${API}/kpis`),
        axios.get<ApiResponse<VendorSpend[]>>(`${API}/vendor-spend`),
        axios.get<ApiResponse<D365PurchaseAgreement[]>>(`${API}/purchase-agreements`),
        axios.get<ApiResponse<D365POLine[]>>(`${API}/po-lines?top=500`),
        axios.get<ApiResponse<CategorySpend[]>>(`${API}/category-spend`),
      ]);

      if (vendorRes.status === 'fulfilled' && vendorRes.value.data?.data)
        setVendors(vendorRes.value.data.data);
      if (productRes.status === 'fulfilled' && productRes.value.data?.data)
        setProducts(productRes.value.data.data);
      if (poRes.status === 'fulfilled' && poRes.value.data?.data)
        setPurchaseOrders(poRes.value.data.data);
      if (kpiRes.status === 'fulfilled' && kpiRes.value.data?.data)
        setKpis(kpiRes.value.data.data);
      if (spendRes.status === 'fulfilled' && spendRes.value.data?.data)
        setVendorSpend(spendRes.value.data.data);
      if (agreementRes.status === 'fulfilled' && agreementRes.value.data?.data)
        setPurchaseAgreements(agreementRes.value.data.data);
      if (poLineRes.status === 'fulfilled' && poLineRes.value.data?.data)
        setPOLines(poLineRes.value.data.data);
      if (catSpendRes.status === 'fulfilled' && catSpendRes.value.data?.data)
        setCategorySpend(catSpendRes.value.data.data);
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Unable to load data. Check the Python bridge is running.");
    } finally {
      setLoading(false);
    }
  };

  // Compute vendor performance from PO headers, PO lines, spend, and agreements
  const vendorPerformance: VendorPerformance[] = useMemo(() => {
    if (!vendors.length) return [];

    const totalSpendAll = vendorSpend.reduce((s, v) => s + v.spend, 0) || 1;
    const agreementVendors = new Set(purchaseAgreements.map(a => a.vendorId));

    // Build a PO→vendor map from headers
    const poVendorMap: Record<string, string> = {};
    purchaseOrders.forEach(po => { poVendorMap[po.poNumber] = po.vendor; });

    // Aggregate PO lines by vendor
    const vendorLineData: Record<string, { lines: number; totalAmount: number; totalPrice: number }> = {};
    poLines.forEach(line => {
      const vid = line.vendor || poVendorMap[line.po] || '';
      if (!vid) return;
      if (!vendorLineData[vid]) vendorLineData[vid] = { lines: 0, totalAmount: 0, totalPrice: 0 };
      vendorLineData[vid].lines += 1;
      vendorLineData[vid].totalAmount += line.amount || 0;
      vendorLineData[vid].totalPrice += line.price || 0;
    });

    // Count POs per vendor
    const vendorPOCount: Record<string, number> = {};
    purchaseOrders.forEach(po => {
      vendorPOCount[po.vendor] = (vendorPOCount[po.vendor] || 0) + 1;
    });

    return vendors.map(v => {
      const spend = vendorSpend.find(s => s.id === v.id);
      const totalSpend = spend?.spend ?? 0;
      const poCount = vendorPOCount[v.id] || 0;
      const lineData = vendorLineData[v.id];

      return {
        id: v.id,
        name: v.name,
        totalPOs: poCount,
        totalSpend,
        avgPOValue: poCount > 0 ? totalSpend / poCount : 0,
        lineCount: lineData?.lines ?? 0,
        avgLinePrice: lineData && lineData.lines > 0 ? lineData.totalPrice / lineData.lines : 0,
        spendShare: (totalSpend / totalSpendAll) * 100,
        hasAgreement: agreementVendors.has(v.id),
      };
    }).filter(v => v.totalPOs > 0 || v.totalSpend > 0)
      .sort((a, b) => b.totalSpend - a.totalSpend);
  }, [vendors, purchaseOrders, poLines, vendorSpend, purchaseAgreements]);

  const createDraftPO = async (payload: POCreationRequest): Promise<POCreationResponse | null> => {
    setIsSubmitting(true);
    try {
      const response = await axios.post<POCreationResponse>(
        `${API}/create-purchase-order`, 
        payload
      );
      // Refresh data in background — don't let it block success
      fetchAll().catch(() => {});
      return response.data;
    } catch (err: any) {
      console.error("PO creation error:", err);
      // Surface the actual error message from the bridge
      const message = err?.response?.data?.error || err?.message || 'Unknown error';
      return { success: false, poNumber: '', vendor: payload.vendorAccount, lineError: message };
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  return { 
    vendors,
    products,
    purchaseOrders,
    purchaseAgreements,
    poLines,
    categorySpend,
    kpis,
    vendorSpend,
    vendorPerformance,
    loading, 
    isSubmitting, 
    error, 
    createDraftPO, 
    refresh: fetchAll 
  };
};