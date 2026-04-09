import React, { useState, useEffect, useMemo } from 'react';
import { 
  LayoutDashboard, Users, AlertCircle, RefreshCcw, 
  ShoppingCart, Search, Bell, Settings,
  Package, FileText, Plus, X, DollarSign,
  BarChart3, Boxes, ArrowUpRight, ArrowDownRight, Check,
  Handshake, Activity, TrendingUp, Award, XCircle, PieChart as PieChartIcon
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
  AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Legend
} from 'recharts';
import { useProcurement } from './hooks/useProcurement';
import type { POCreationRequest } from './types/d365';

type NavPage = 'dashboard' | 'vendors' | 'orders' | 'products' | 'agreements' | 'performance' | 'analytics';

const App: React.FC = () => {
  const { 
    vendors, products, purchaseOrders, purchaseAgreements,
    kpis, vendorSpend, vendorPerformance, poLines, categorySpend,
    loading, error, isSubmitting, createDraftPO, refresh 
  } = useProcurement();

  const [searchTerm, setSearchTerm] = useState('');
  const [activePage, setActivePage] = useState<NavPage>('dashboard');
  const [showCreatePO, setShowCreatePO] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => { setIsMounted(true); }, []);

  useEffect(() => {
    if (toastMessage) {
      const t = setTimeout(() => setToastMessage(null), 4000);
      return () => clearTimeout(t);
    }
  }, [toastMessage]);

  const [toastType, setToastType] = useState<'success' | 'error'>('success');

  const handleCreatePO = async (payload: POCreationRequest) => {
    const result = await createDraftPO(payload);
    if (result?.success) {
      setToastType('success');
      setToastMessage(`PO ${result.poNumber} created successfully${result.lineError ? ' (header only — line warning)' : ''}`);
      setShowCreatePO(false);
    } else {
      setToastType('error');
      const detail = result?.lineError || 'Check vendor/item and try again';
      setToastMessage(`PO creation failed: ${detail}`);
    }
  };

  const formatCurrency = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);

  if (!isMounted) return <div className="h-screen bg-slate-950" />;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      
      {/* ── SIDEBAR ── */}
      <aside className="w-64 bg-slate-900/80 border-r border-slate-800/60 flex flex-col backdrop-blur-sm">
        <div className="p-6 pb-8">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center">
              <Boxes size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-extrabold tracking-tight text-white">VIBE ERP</h1>
              <p className="text-[10px] text-slate-500 font-medium tracking-wider uppercase">Procurement</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 space-y-0.5">
          <p className="px-3 pb-2 text-[10px] font-bold text-slate-600 uppercase tracking-widest">Main</p>
          <NavItem icon={<LayoutDashboard size={18}/>} label="Dashboard" active={activePage === 'dashboard'} onClick={() => setActivePage('dashboard')} />
          <NavItem icon={<Users size={18}/>} label="Vendors" active={activePage === 'vendors'} onClick={() => setActivePage('vendors')} count={vendors.length} />
          <NavItem icon={<FileText size={18}/>} label="Purchase Orders" active={activePage === 'orders'} onClick={() => setActivePage('orders')} count={purchaseOrders.length} />
          <NavItem icon={<Handshake size={18}/>} label="Agreements" active={activePage === 'agreements'} onClick={() => setActivePage('agreements')} count={purchaseAgreements.length} />
          <NavItem icon={<Package size={18}/>} label="Products" active={activePage === 'products'} onClick={() => setActivePage('products')} count={products.length} />
          <NavItem icon={<Activity size={18}/>} label="Vendor Metrics" active={activePage === 'performance'} onClick={() => setActivePage('performance')} />
          <NavItem icon={<PieChartIcon size={18}/>} label="Analytics" active={activePage === 'analytics'} onClick={() => setActivePage('analytics')} />

          <div className="!mt-6">
            <p className="px-3 pb-2 text-[10px] font-bold text-slate-600 uppercase tracking-widest">Actions</p>
            <button 
              onClick={() => setShowCreatePO(true)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-semibold text-sm transition-colors"
            >
              <Plus size={18}/> <span>Create PO</span>
            </button>
          </div>
        </nav>

        <div className="p-3 mt-auto">
          <button
            onClick={refresh}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg border border-slate-700/60 text-slate-400 hover:text-white hover:border-slate-600 text-xs font-medium transition-colors"
          >
            <RefreshCcw size={14} className={loading ? "animate-spin" : ""} />
            {loading ? 'Syncing...' : 'Sync D365'}
          </button>
          <div className="mt-3 flex items-center gap-2 px-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[10px] text-slate-500">Connected to D365 F&O</span>
          </div>
        </div>
      </aside>

      {/* ── MAIN AREA ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* ── TOP BAR ── */}
        <header className="h-14 border-b border-slate-800/60 flex items-center justify-between px-6 bg-slate-950/80 backdrop-blur-sm shrink-0">
          <div className="flex-1 max-w-sm relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" size={15} />
            <input 
              type="text" placeholder="Search vendors, POs, products..." value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900/60 border border-slate-800/60 rounded-lg py-2 pl-9 pr-4 text-sm focus:ring-1 focus:ring-teal-500/50 focus:border-teal-500/50 outline-none placeholder:text-slate-600 transition-colors"
            />
          </div>
          <div className="flex items-center gap-3">
            <button className="relative p-2 rounded-lg hover:bg-slate-800/50 transition-colors">
              <Bell className="text-slate-500" size={18} />
              {(kpis?.lowStockAlerts ?? 0) > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
              )}
            </button>
            <button className="p-2 rounded-lg hover:bg-slate-800/50 transition-colors">
              <Settings className="text-slate-500" size={18} />
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-teal-500 to-blue-600 flex items-center justify-center text-xs font-bold">
              U
            </div>
          </div>
        </header>

        {/* ── PAGE CONTENT ── */}
        <main className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3">
              <RefreshCcw className="animate-spin" size={32} />
              <p className="text-sm">Synchronizing with Dynamics 365 F&O...</p>
            </div>
          ) : error ? (
            <div className="m-6 bg-red-500/10 border border-red-500/20 p-5 rounded-xl text-red-400 flex items-center gap-3 text-sm">
              <AlertCircle size={18} /> {error}
            </div>
          ) : (
            <div className="p-6 space-y-6">
              {activePage === 'dashboard' && (
                <DashboardView 
                  kpis={kpis} vendors={vendors} purchaseOrders={purchaseOrders}
                  vendorSpend={vendorSpend} formatCurrency={formatCurrency}
                  onNavigate={setActivePage} searchTerm={searchTerm}
                />
              )}
              {activePage === 'vendors' && (
                <VendorsView vendors={vendors} searchTerm={searchTerm} onCreatePO={() => { setShowCreatePO(true); }} />
              )}
              {activePage === 'orders' && (
                <OrdersView purchaseOrders={purchaseOrders} searchTerm={searchTerm} />
              )}
              {activePage === 'products' && (
                <ProductsView products={products} searchTerm={searchTerm} />
              )}
              {activePage === 'agreements' && (
                <AgreementsView agreements={purchaseAgreements} vendors={vendors} searchTerm={searchTerm} />
              )}
              {activePage === 'performance' && (
                <VendorPerformanceView performance={vendorPerformance} formatCurrency={formatCurrency} searchTerm={searchTerm} />
              )}
              {activePage === 'analytics' && (
                <AnalyticsView 
                  vendorSpend={vendorSpend} categorySpend={categorySpend}
                  vendorPerformance={vendorPerformance} purchaseOrders={purchaseOrders}
                  poLines={poLines} kpis={kpis} formatCurrency={formatCurrency}
                />
              )}
            </div>
          )}
        </main>
      </div>

      {/* ── CREATE PO MODAL ── */}
      {showCreatePO && (
        <CreatePOModal 
          vendors={vendors} products={products}
          isSubmitting={isSubmitting}
          onSubmit={handleCreatePO}
          onClose={() => setShowCreatePO(false)}
        />
      )}

      {/* ── TOAST ── */}
      {toastMessage && (
        <div className={`fixed bottom-6 right-6 border text-white px-5 py-3 rounded-xl shadow-2xl flex items-center gap-3 animate-slide-up z-50 ${
          toastType === 'success' ? 'bg-slate-800 border-slate-700/60' : 'bg-red-950 border-red-500/30'
        }`}>
          <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
            toastType === 'success' ? 'bg-emerald-500/20' : 'bg-red-500/20'
          }`}>
            {toastType === 'success' 
              ? <Check size={14} className="text-emerald-400" />
              : <XCircle size={14} className="text-red-400" />
            }
          </div>
          <span className="text-sm font-medium max-w-md">{toastMessage}</span>
        </div>
      )}
    </div>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   NAV ITEM
   ═══════════════════════════════════════════════════════════════════════════ */

const NavItem = ({ icon, label, active = false, onClick, count }: {
  icon: React.ReactNode; label: string; active?: boolean; onClick: () => void; count?: number;
}) => (
  <button 
    onClick={onClick}
    className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg transition-all text-sm ${
      active 
        ? 'bg-teal-500/10 text-teal-400 font-semibold border border-teal-500/20' 
        : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent'
    }`}
  >
    {icon}
    <span className="flex-1 text-left">{label}</span>
    {count !== undefined && count > 0 && (
      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${
        active ? 'bg-teal-500/20 text-teal-400' : 'bg-slate-800 text-slate-500'
      }`}>{count}</span>
    )}
  </button>
);


/* ═══════════════════════════════════════════════════════════════════════════
   DASHBOARD VIEW
   ═══════════════════════════════════════════════════════════════════════════ */

const DashboardView = ({ kpis, purchaseOrders, vendorSpend, formatCurrency, onNavigate }: {
  kpis: any; vendors: any[]; purchaseOrders: any[]; vendorSpend: any[];
  formatCurrency: (n: number) => string; onNavigate: (p: NavPage) => void; searchTerm: string;
}) => (
  <>
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-xl font-bold text-white">Procurement Dashboard</h2>
        <p className="text-xs text-slate-500 mt-0.5">Real-time data from Dynamics 365 F&O — USMF</p>
      </div>
    </div>

    {/* KPI CARDS */}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <KPICard 
        title="Total Spend" 
        value={formatCurrency(kpis?.totalSpend ?? 0)} 
        icon={<DollarSign size={18}/>} 
        trend="+12.3%" trendUp={true}
        accent="teal"
      />
      <KPICard 
        title="Open POs" 
        value={String(kpis?.openPOs ?? 0)} 
        icon={<FileText size={18}/>} 
        accent="blue"
        onClick={() => onNavigate('orders')}
      />
      <KPICard 
        title="Active Vendors" 
        value={String(kpis?.activeVendors ?? 0)} 
        icon={<Users size={18}/>} 
        accent="violet"
        onClick={() => onNavigate('vendors')}
      />
      <KPICard 
        title="Low Stock Alerts" 
        value={String(kpis?.lowStockAlerts ?? 0)} 
        icon={<AlertCircle size={18}/>} 
        accent="amber"
        alert={kpis?.lowStockAlerts > 0}
      />
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* TOP VENDOR SPEND */}
      <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-teal-500" />
            <h3 className="text-sm font-semibold text-white">Top Vendor Spend</h3>
          </div>
          <span className="text-[10px] text-slate-500 font-medium">D365 LIVE</span>
        </div>
        <div className="p-5 space-y-3">
          {vendorSpend.slice(0, 6).map((v, i) => (
            <div key={v.id} className="flex items-center gap-3">
              <span className="text-[10px] text-slate-600 font-mono w-4">{i + 1}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-300 truncate">{v.name}</span>
                  <span className="text-xs font-bold text-white ml-2">{formatCurrency(v.spend)}</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-teal-500 to-blue-500 rounded-full transition-all"
                    style={{ width: `${Math.min(v.cumPct, 100)}%` }} 
                  />
                </div>
              </div>
            </div>
          ))}
          {vendorSpend.length === 0 && <p className="text-xs text-slate-600 text-center py-4">No spend data available</p>}
        </div>
      </div>

      {/* RECENT POs */}
      <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-blue-500" />
            <h3 className="text-sm font-semibold text-white">Recent Purchase Orders</h3>
          </div>
          <button onClick={() => onNavigate('orders')} className="text-[10px] text-teal-500 hover:text-teal-400 font-medium">View All</button>
        </div>
        <div className="divide-y divide-slate-800/60">
          {purchaseOrders.slice(0, 8).map(po => (
            <div key={po.poNumber} className="px-5 py-3 flex items-center justify-between hover:bg-slate-800/30 transition-colors">
              <div>
                <p className="text-xs font-semibold text-white font-mono">{po.poNumber}</p>
                <p className="text-[10px] text-slate-500">{po.vendor}</p>
              </div>
              <StatusBadge status={po.status} />
            </div>
          ))}
          {purchaseOrders.length === 0 && <p className="text-xs text-slate-600 text-center py-6">No purchase orders</p>}
        </div>
      </div>
    </div>
  </>
);


/* ═══════════════════════════════════════════════════════════════════════════
   KPI CARD
   ═══════════════════════════════════════════════════════════════════════════ */

const KPICard = ({ title, value, icon, trend, trendUp, accent, alert, onClick }: {
  title: string; value: string; icon: React.ReactNode;
  trend?: string; trendUp?: boolean; accent: string; alert?: boolean; onClick?: () => void;
}) => {
  const accentMap: Record<string, string> = {
    teal: 'from-teal-500/10 to-teal-500/5 border-teal-500/20 text-teal-400',
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/20 text-blue-400',
    violet: 'from-violet-500/10 to-violet-500/5 border-violet-500/20 text-violet-400',
    amber: 'from-amber-500/10 to-amber-500/5 border-amber-500/20 text-amber-400',
  };
  const colors = accentMap[accent] || accentMap.teal;

  return (
    <div 
      onClick={onClick}
      className={`bg-gradient-to-br ${colors} border rounded-xl p-5 ${onClick ? 'cursor-pointer hover:scale-[1.02]' : ''} transition-all`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{title}</span>
        <div className={`p-1.5 rounded-lg bg-slate-800/50`}>{icon}</div>
      </div>
      <div className="flex items-end justify-between">
        <p className={`text-2xl font-extrabold text-white ${alert ? 'text-amber-400' : ''}`}>{value}</p>
        {trend && (
          <span className={`flex items-center gap-0.5 text-[10px] font-bold ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
            {trendUp ? <ArrowUpRight size={12}/> : <ArrowDownRight size={12}/>} {trend}
          </span>
        )}
      </div>
    </div>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   STATUS BADGE
   ═══════════════════════════════════════════════════════════════════════════ */

const StatusBadge = ({ status }: { status: string }) => {
  const statusLabel = status || 'Open';
  const isOpen = statusLabel.toLowerCase().includes('open') || statusLabel === 'None';
  return (
    <span className={`text-[10px] font-bold px-2 py-1 rounded-md ${
      isOpen ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
             : 'bg-slate-800 text-slate-400 border border-slate-700/60'
    }`}>
      {statusLabel}
    </span>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   VENDORS VIEW
   ═══════════════════════════════════════════════════════════════════════════ */

const VendorsView = ({ vendors, searchTerm, onCreatePO }: {
  vendors: any[]; searchTerm: string; onCreatePO: (vendorId: string) => void;
}) => {
  const filtered = vendors.filter(v =>
    v.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Vendors</h2>
          <p className="text-xs text-slate-500 mt-0.5">{filtered.length} vendors from D365 F&O</p>
        </div>
      </div>
      <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800/60">
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Account</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Name</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Group</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Country</th>
              <th className="text-right px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {filtered.map(v => (
              <tr key={v.id} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-5 py-3 text-xs font-mono text-teal-400 font-semibold">{v.id}</td>
                <td className="px-5 py-3 text-sm text-white font-medium">{v.name}</td>
                <td className="px-5 py-3 text-xs text-slate-400">{v.group || '—'}</td>
                <td className="px-5 py-3 text-xs text-slate-400">{v.country || '—'}</td>
                <td className="px-5 py-3 text-right">
                  <button 
                    onClick={() => onCreatePO(v.id)}
                    className="text-xs font-semibold text-teal-500 hover:text-teal-400 transition-colors"
                  >
                    Create PO
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="text-sm text-slate-600 text-center py-10">No vendors match your search</p>
        )}
      </div>
    </>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   ORDERS VIEW
   ═══════════════════════════════════════════════════════════════════════════ */

const OrdersView = ({ purchaseOrders, searchTerm }: { purchaseOrders: any[]; searchTerm: string }) => {
  const filtered = purchaseOrders.filter(po =>
    po.poNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
    po.vendor.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Purchase Orders</h2>
          <p className="text-xs text-slate-500 mt-0.5">{filtered.length} orders from D365 F&O</p>
        </div>
      </div>
      <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800/60">
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">PO Number</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Vendor Account</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Currency</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {filtered.map(po => (
              <tr key={po.poNumber} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-5 py-3 text-sm font-mono text-blue-400 font-semibold">{po.poNumber}</td>
                <td className="px-5 py-3 text-sm text-white">{po.vendor}</td>
                <td className="px-5 py-3 text-xs text-slate-400">{po.currency}</td>
                <td className="px-5 py-3"><StatusBadge status={po.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="text-sm text-slate-600 text-center py-10">No purchase orders match your search</p>
        )}
      </div>
    </>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   PRODUCTS VIEW
   ═══════════════════════════════════════════════════════════════════════════ */

const ProductsView = ({ products, searchTerm }: { products: any[]; searchTerm: string }) => {
  const filtered = products.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.itemId.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      <div>
        <h2 className="text-xl font-bold text-white">Released Products</h2>
        <p className="text-xs text-slate-500 mt-0.5">{filtered.length} products from D365 F&O</p>
      </div>
      <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800/60">
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Item Number</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Product Name</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Category</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {filtered.map(p => (
              <tr key={p.itemId} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-5 py-3 text-xs font-mono text-violet-400 font-semibold">{p.itemId}</td>
                <td className="px-5 py-3 text-sm text-white font-medium">{p.name}</td>
                <td className="px-5 py-3 text-xs text-slate-400">{p.category}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="text-sm text-slate-600 text-center py-10">No products match your search</p>
        )}
      </div>
    </>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   PURCHASE AGREEMENTS VIEW
   ═══════════════════════════════════════════════════════════════════════════ */

const AgreementsView = ({ agreements, vendors, searchTerm }: {
  agreements: any[]; vendors: any[]; searchTerm: string;
}) => {
  const vendorNames: Record<string, string> = {};
  vendors.forEach(v => { vendorNames[v.id] = v.name; });

  const filtered = agreements.filter(a =>
    (a.num || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (a.vendorId || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (vendorNames[a.vendorId] || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (a.title || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusStyle = (status: string) => {
    const s = status?.toLowerCase() || '';
    if (s.includes('effective') || s.includes('active')) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    if (s.includes('closed') || s.includes('expired')) return 'bg-red-500/10 text-red-400 border-red-500/20';
    return 'bg-slate-800 text-slate-400 border-slate-700/60';
  };

  return (
    <>
      <div>
        <h2 className="text-xl font-bold text-white">Purchase Agreements</h2>
        <p className="text-xs text-slate-500 mt-0.5">{filtered.length} agreements from D365 F&O</p>
      </div>
      <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800/60">
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Agreement ID</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Vendor</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Title</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Classification</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Currency</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Expiry</th>
              <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {filtered.map(a => (
              <tr key={a.num} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-5 py-3 text-xs font-mono text-blue-400 font-semibold">{a.num}</td>
                <td className="px-5 py-3">
                  <p className="text-sm text-white font-medium">{vendorNames[a.vendorId] || a.vendorId}</p>
                  <p className="text-[10px] text-slate-500 font-mono">{a.vendorId}</p>
                </td>
                <td className="px-5 py-3 text-xs text-slate-300">{a.title || '—'}</td>
                <td className="px-5 py-3 text-xs text-slate-400">{a.cls || '—'}</td>
                <td className="px-5 py-3 text-xs text-slate-400">{a.currency || '—'}</td>
                <td className="px-5 py-3 text-xs text-slate-400">{a.expiry || '—'}</td>
                <td className="px-5 py-3">
                  <span className={`text-[10px] font-bold px-2 py-1 rounded-md border ${getStatusStyle(a.status)}`}>
                    {a.status || 'Draft'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="text-sm text-slate-600 text-center py-10">No purchase agreements found</p>
        )}
      </div>
    </>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   VENDOR PERFORMANCE / OTIF VIEW
   ═══════════════════════════════════════════════════════════════════════════ */

const VendorPerformanceView = ({ performance, formatCurrency, searchTerm }: {
  performance: any[]; formatCurrency: (n: number) => string; searchTerm: string;
}) => {
  const filtered = performance.filter((v: any) =>
    v.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const topSpend = performance[0]?.totalSpend || 1;

  const getScoreColor = (share: number) => {
    if (share >= 10) return 'text-teal-400';
    if (share >= 3) return 'text-blue-400';
    return 'text-slate-400';
  };

  const getRiskLabel = (v: any) => {
    if (v.spendShare > 25) return { label: 'High Concentration', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' };
    if (v.hasAgreement) return { label: 'Under Agreement', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' };
    if (v.totalPOs <= 2) return { label: 'Low Volume', color: 'text-slate-400 bg-slate-800 border-slate-700/60' };
    return { label: 'Active', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' };
  };

  return (
    <>
      <div>
        <h2 className="text-xl font-bold text-white">Vendor Performance & Selection Metrics</h2>
        <p className="text-xs text-slate-500 mt-0.5">Computed from live D365 F&O purchase order data — {filtered.length} vendors with transactions</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-teal-500/10 to-teal-500/5 border border-teal-500/20 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={14} className="text-teal-400" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Active Vendors</span>
          </div>
          <p className="text-2xl font-extrabold text-white">{performance.length}</p>
        </div>
        <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <Award size={14} className="text-blue-400" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">With Agreements</span>
          </div>
          <p className="text-2xl font-extrabold text-white">{performance.filter((v: any) => v.hasAgreement).length}</p>
        </div>
        <div className="bg-gradient-to-br from-violet-500/10 to-violet-500/5 border border-violet-500/20 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 size={14} className="text-violet-400" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Avg PO Value</span>
          </div>
          <p className="text-2xl font-extrabold text-white">
            {formatCurrency(performance.length > 0 ? performance.reduce((s: number, v: any) => s + v.avgPOValue, 0) / performance.length : 0)}
          </p>
        </div>
        <div className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 border border-amber-500/20 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={14} className="text-amber-400" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">High Concentration</span>
          </div>
          <p className="text-2xl font-extrabold text-white">{performance.filter((v: any) => v.spendShare > 25).length}</p>
        </div>
      </div>

      {/* Data table */}
      <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-teal-500" />
            <h3 className="text-sm font-semibold text-white">Vendor Scorecard</h3>
          </div>
          <span className="text-[10px] text-slate-500 font-medium">Ranked by total spend</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800/60">
                <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">#</th>
                <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Vendor</th>
                <th className="text-right px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total POs</th>
                <th className="text-right px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total Spend</th>
                <th className="text-right px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Avg PO Value</th>
                <th className="text-right px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">PO Lines</th>
                <th className="text-right px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Avg Line Price</th>
                <th className="text-center px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Spend Share</th>
                <th className="text-left px-5 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {filtered.map((v: any, i: number) => {
                const risk = getRiskLabel(v);
                return (
                  <tr key={v.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-5 py-3 text-xs text-slate-600 font-mono">{i + 1}</td>
                    <td className="px-5 py-3">
                      <p className="text-sm text-white font-medium">{v.name}</p>
                      <p className="text-[10px] text-slate-500 font-mono">{v.id}</p>
                    </td>
                    <td className="px-5 py-3 text-sm text-white text-right font-semibold">{v.totalPOs}</td>
                    <td className="px-5 py-3 text-right">
                      <p className="text-sm text-white font-semibold">{formatCurrency(v.totalSpend)}</p>
                      <div className="mt-1 h-1 bg-slate-800 rounded-full overflow-hidden w-20 ml-auto">
                        <div className="h-full bg-gradient-to-r from-teal-500 to-blue-500 rounded-full" style={{ width: `${(v.totalSpend / topSpend) * 100}%` }} />
                      </div>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-300 text-right">{formatCurrency(v.avgPOValue)}</td>
                    <td className="px-5 py-3 text-sm text-slate-300 text-right">{v.lineCount}</td>
                    <td className="px-5 py-3 text-sm text-slate-300 text-right">{formatCurrency(v.avgLinePrice)}</td>
                    <td className="px-5 py-3 text-center">
                      <span className={`text-sm font-bold ${getScoreColor(v.spendShare)}`}>{v.spendShare.toFixed(1)}%</span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={`text-[10px] font-bold px-2 py-1 rounded-md border ${risk.color}`}>{risk.label}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <p className="text-sm text-slate-600 text-center py-10">No vendor performance data available</p>
          )}
        </div>
      </div>
    </>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   ANALYTICS VIEW — Recharts
   ═══════════════════════════════════════════════════════════════════════════ */

const CHART_COLORS = ['#14b8a6', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4', '#84cc16'];

const ChartTooltipContent = ({ active, payload, label, formatter }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-700/60 rounded-lg px-3 py-2 shadow-xl">
      <p className="text-[10px] text-slate-400 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-xs font-semibold" style={{ color: p.color }}>
          {p.name}: {formatter ? formatter(p.value) : p.value}
        </p>
      ))}
    </div>
  );
};

const AnalyticsView = ({ vendorSpend, categorySpend, vendorPerformance, purchaseOrders, poLines, formatCurrency }: {
  vendorSpend: any[]; categorySpend: any[]; vendorPerformance: any[];
  purchaseOrders: any[]; poLines: any[]; kpis: any;
  formatCurrency: (n: number) => string;
}) => {
  // ── Derived data for charts ──

  // Top 10 vendors by spend for bar chart
  const topVendorData = useMemo(() => 
    vendorSpend.slice(0, 10).map(v => ({
      name: v.name.length > 18 ? v.name.substring(0, 18) + '…' : v.name,
      spend: v.spend,
      fullName: v.name,
    })), [vendorSpend]);

  // Category spend for pie chart
  const categoryData = useMemo(() => 
    categorySpend.slice(0, 8).map((c, i) => ({
      name: c.category,
      value: c.spend,
      fill: CHART_COLORS[i % CHART_COLORS.length],
    })), [categorySpend]);

  // PO status distribution for donut
  const statusData = useMemo(() => {
    const map: Record<string, number> = {};
    purchaseOrders.forEach(po => {
      const s = po.status || 'Open';
      map[s] = (map[s] || 0) + 1;
    });
    return Object.entries(map).map(([name, value], i) => ({
      name, value, fill: CHART_COLORS[i % CHART_COLORS.length],
    }));
  }, [purchaseOrders]);

  // Vendor PO count distribution (top 8) for horizontal bar
  const vendorPOCountData = useMemo(() =>
    vendorPerformance.slice(0, 8).map(v => ({
      name: v.name.length > 20 ? v.name.substring(0, 20) + '…' : v.name,
      orders: v.totalPOs,
      lines: v.lineCount,
    })), [vendorPerformance]);

  // Spend concentration (Pareto) area chart
  const paretoData = useMemo(() =>
    vendorSpend.slice(0, 15).map((v, i) => ({
      name: `V${i + 1}`,
      spend: v.spend,
      cumPct: v.cumPct,
      fullName: v.name,
    })), [vendorSpend]);

  // Radar: top 5 vendors multi-dimension comparison
  const radarData = useMemo(() => {
    const top5 = vendorPerformance.slice(0, 5);
    if (!top5.length) return [];
    const maxSpend = Math.max(...top5.map(v => v.totalSpend)) || 1;
    const maxPOs = Math.max(...top5.map(v => v.totalPOs)) || 1;
    const maxLines = Math.max(...top5.map(v => v.lineCount)) || 1;
    const maxAvg = Math.max(...top5.map(v => v.avgPOValue)) || 1;
    const maxShare = Math.max(...top5.map(v => v.spendShare)) || 1;

    const dims = ['Spend', 'PO Count', 'Line Items', 'Avg PO Value', 'Spend Share'];
    return dims.map((dim, di) => {
      const entry: any = { dimension: dim };
      top5.forEach((v) => {
        const vals = [
          v.totalSpend / maxSpend,
          v.totalPOs / maxPOs,
          v.lineCount / maxLines,
          v.avgPOValue / maxAvg,
          v.spendShare / maxShare,
        ];
        entry[v.name.substring(0, 12)] = Math.round(vals[di] * 100);
      });
      return entry;
    });
  }, [vendorPerformance]);

  const radarKeys = useMemo(() =>
    vendorPerformance.slice(0, 5).map(v => v.name.substring(0, 12)), [vendorPerformance]);

  // Item frequency from PO lines (top items)
  const itemFrequency = useMemo(() => {
    const map: Record<string, { count: number; totalAmount: number }> = {};
    poLines.forEach((line: any) => {
      const id = line.itemId || line.item || 'Unknown';
      if (!map[id]) map[id] = { count: 0, totalAmount: 0 };
      map[id].count += 1;
      map[id].totalAmount += line.amount || 0;
    });
    return Object.entries(map)
      .sort((a, b) => b[1].totalAmount - a[1].totalAmount)
      .slice(0, 10)
      .map(([item, d]) => ({ item, count: d.count, amount: d.totalAmount }));
  }, [poLines]);

  return (
    <>
      <div>
        <h2 className="text-xl font-bold text-white">Procurement Analytics</h2>
        <p className="text-xs text-slate-500 mt-0.5">Visual insights from Dynamics 365 F&O live data</p>
      </div>

      {/* ── Row 1: Vendor Spend Bar + Category Pie ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3 bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 size={16} className="text-teal-500" />
              <h3 className="text-sm font-semibold text-white">Top Vendor Spend</h3>
            </div>
            <span className="text-[10px] text-slate-500 font-medium">TOP 10</span>
          </div>
          <div className="p-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topVendorData} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} axisLine={false} />
                <YAxis type="category" dataKey="name" width={130} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} />
                <Tooltip content={<ChartTooltipContent formatter={(v: number) => formatCurrency(v)} />} cursor={{ fill: 'rgba(148,163,184,0.05)' }} />
                <Bar dataKey="spend" radius={[0, 6, 6, 0]} maxBarSize={24}>
                  {topVendorData.map((_, i) => (
                    <Cell key={i} fill={i === 0 ? '#14b8a6' : i < 3 ? '#0d9488' : '#115e59'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800/60 flex items-center gap-2">
            <PieChartIcon size={16} className="text-violet-500" />
            <h3 className="text-sm font-semibold text-white">Spend by Category</h3>
          </div>
          <div className="p-4 h-72 flex items-center justify-center">
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={categoryData} cx="50%" cy="50%" innerRadius={50} outerRadius={85} paddingAngle={3} dataKey="value" stroke="none">
                    {categoryData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip content={<ChartTooltipContent formatter={(v: number) => formatCurrency(v)} />} />
                  <Legend 
                    wrapperStyle={{ fontSize: 10 }}
                    formatter={(value: string) => <span className="text-slate-400 text-[10px]">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-600">No category data available</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Row 2: Spend Concentration + PO Status ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-blue-500" />
              <h3 className="text-sm font-semibold text-white">Spend Concentration (Pareto)</h3>
            </div>
            <span className="text-[10px] text-slate-500 font-medium">80/20 ANALYSIS</span>
          </div>
          <div className="p-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={paretoData} margin={{ left: 10, right: 10, top: 5, bottom: 5 }}>
                <defs>
                  <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} />
                <YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} axisLine={false} />
                <YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(v) => `${v}%`} axisLine={false} domain={[0, 100]} />
                <Tooltip content={<ChartTooltipContent formatter={(v: number) => typeof v === 'number' && v <= 100 ? `${v.toFixed(1)}%` : formatCurrency(v)} />} />
                <Area yAxisId="left" type="monotone" dataKey="spend" stroke="#14b8a6" fill="url(#spendGrad)" strokeWidth={2} name="Spend" />
                <Area yAxisId="right" type="monotone" dataKey="cumPct" stroke="#3b82f6" fill="none" strokeWidth={2} strokeDasharray="5 5" name="Cumulative %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800/60 flex items-center gap-2">
            <FileText size={16} className="text-amber-500" />
            <h3 className="text-sm font-semibold text-white">PO Status Distribution</h3>
          </div>
          <div className="p-4 h-64 flex items-center justify-center">
            {statusData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={statusData} cx="50%" cy="50%" outerRadius={75} dataKey="value" stroke="none" label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`} labelLine={false} fontSize={10} fill="#fff">
                    {statusData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip content={<ChartTooltipContent />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-600">No PO data</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Row 3: Vendor Orders + Radar ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users size={16} className="text-teal-500" />
              <h3 className="text-sm font-semibold text-white">Vendor Order Volume</h3>
            </div>
            <span className="text-[10px] text-slate-500 font-medium">POs & LINES</span>
          </div>
          <div className="p-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={vendorPOCountData} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} />
                <YAxis type="category" dataKey="name" width={150} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} />
                <Tooltip content={<ChartTooltipContent />} cursor={{ fill: 'rgba(148,163,184,0.05)' }} />
                <Bar dataKey="orders" fill="#3b82f6" radius={[0, 4, 4, 0]} maxBarSize={16} name="Purchase Orders" />
                <Bar dataKey="lines" fill="#8b5cf6" radius={[0, 4, 4, 0]} maxBarSize={16} name="PO Lines" />
                <Legend wrapperStyle={{ fontSize: 10 }} formatter={(v: string) => <span className="text-slate-400 text-[10px]">{v}</span>} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Award size={16} className="text-violet-500" />
              <h3 className="text-sm font-semibold text-white">Top 5 Vendor Comparison</h3>
            </div>
            <span className="text-[10px] text-slate-500 font-medium">RADAR</span>
          </div>
          <div className="p-4 h-72">
            {radarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                  <PolarGrid stroke="#1e293b" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <PolarRadiusAxis tick={false} axisLine={false} />
                  {radarKeys.map((key, i) => (
                    <Radar key={key} name={key} dataKey={key} stroke={CHART_COLORS[i]} fill={CHART_COLORS[i]} fillOpacity={0.1} strokeWidth={2} />
                  ))}
                  <Legend wrapperStyle={{ fontSize: 10 }} formatter={(v: string) => <span className="text-slate-400 text-[10px]">{v}</span>} />
                  <Tooltip content={<ChartTooltipContent />} />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-600 text-center mt-20">Not enough vendor data for comparison</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Row 4: Top Procured Items ── */}
      <div className="bg-slate-900/50 border border-slate-800/60 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package size={16} className="text-teal-500" />
            <h3 className="text-sm font-semibold text-white">Most Procured Items</h3>
          </div>
          <span className="text-[10px] text-slate-500 font-medium">BY VALUE</span>
        </div>
        <div className="p-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={itemFrequency} margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="item" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} interval={0} angle={-30} textAnchor="end" height={50} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} axisLine={false} />
              <Tooltip content={<ChartTooltipContent formatter={(v: number) => formatCurrency(v)} />} cursor={{ fill: 'rgba(148,163,184,0.05)' }} />
              <Bar dataKey="amount" radius={[6, 6, 0, 0]} maxBarSize={32} name="Total Value">
                {itemFrequency.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
};


/* ═══════════════════════════════════════════════════════════════════════════
   CREATE PO MODAL
   ═══════════════════════════════════════════════════════════════════════════ */

const CreatePOModal = ({ vendors, products, isSubmitting, onSubmit, onClose }: {
  vendors: any[]; products: any[]; isSubmitting: boolean;
  onSubmit: (payload: POCreationRequest) => void; onClose: () => void;
}) => {
  const [vendorAccount, setVendorAccount] = useState('');
  const [itemNumber, setItemNumber] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [entity, setEntity] = useState('USMF');
  const [vendorSearch, setVendorSearch] = useState('');
  const [productSearch, setProductSearch] = useState('');
  const [showVendorDropdown, setShowVendorDropdown] = useState(false);
  const [showProductDropdown, setShowProductDropdown] = useState(false);

  const filteredVendors = vendors.filter(v =>
    v.name.toLowerCase().includes(vendorSearch.toLowerCase()) ||
    v.id.toLowerCase().includes(vendorSearch.toLowerCase())
  ).slice(0, 8);

  const filteredProducts = products.filter(p =>
    p.name.toLowerCase().includes(productSearch.toLowerCase()) ||
    p.itemId.toLowerCase().includes(productSearch.toLowerCase())
  ).slice(0, 8);

  const selectedVendor = vendors.find(v => v.id === vendorAccount);
  const selectedProduct = products.find(p => p.itemId === itemNumber);

  const canSubmit = vendorAccount && itemNumber && quantity > 0;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-slate-800/60 rounded-2xl w-full max-w-lg shadow-2xl" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-teal-500/10">
              <ShoppingCart size={18} className="text-teal-400" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Create Purchase Order</h3>
              <p className="text-[10px] text-slate-500">Submit to D365 Finance & Operations</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-800 transition-colors">
            <X size={18} className="text-slate-400" />
          </button>
        </div>

        {/* Form */}
        <div className="p-6 space-y-5">
          
          {/* Legal Entity */}
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Legal Entity</label>
            <select 
              value={entity} onChange={e => setEntity(e.target.value)}
              className="w-full bg-slate-800/50 border border-slate-700/60 rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:ring-1 focus:ring-teal-500/50 appearance-none cursor-pointer"
            >
              <option value="USMF">USMF — Contoso Entertainment</option>
              <option value="USRT">USRT — Contoso Retail</option>
              <option value="DEMF">DEMF — Contoso Germany</option>
            </select>
          </div>

          {/* Vendor Select */}
          <div className="relative">
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Vendor Account *</label>
            {selectedVendor ? (
              <div className="flex items-center justify-between bg-slate-800/50 border border-teal-500/30 rounded-lg px-3 py-2.5">
                <div>
                  <span className="text-sm font-medium text-white">{selectedVendor.name}</span>
                  <span className="text-xs text-teal-400 ml-2 font-mono">{selectedVendor.id}</span>
                </div>
                <button onClick={() => { setVendorAccount(''); setVendorSearch(''); }} className="text-slate-400 hover:text-white">
                  <X size={14} />
                </button>
              </div>
            ) : (
              <div>
                <input
                  type="text" placeholder="Search vendor..."
                  value={vendorSearch}
                  onChange={e => { setVendorSearch(e.target.value); setShowVendorDropdown(true); }}
                  onFocus={() => setShowVendorDropdown(true)}
                  className="w-full bg-slate-800/50 border border-slate-700/60 rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:ring-1 focus:ring-teal-500/50 placeholder:text-slate-600"
                />
                {showVendorDropdown && filteredVendors.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-slate-800 border border-slate-700/60 rounded-lg shadow-xl max-h-48 overflow-y-auto">
                    {filteredVendors.map(v => (
                      <button
                        key={v.id}
                        onClick={() => { setVendorAccount(v.id); setShowVendorDropdown(false); setVendorSearch(''); }}
                        className="w-full text-left px-3 py-2 hover:bg-slate-700/50 transition-colors flex items-center justify-between"
                      >
                        <span className="text-sm text-white">{v.name}</span>
                        <span className="text-[10px] text-slate-400 font-mono">{v.id}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Product Select */}
          <div className="relative">
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Item Number *</label>
            {selectedProduct ? (
              <div className="flex items-center justify-between bg-slate-800/50 border border-teal-500/30 rounded-lg px-3 py-2.5">
                <div>
                  <span className="text-sm font-medium text-white">{selectedProduct.name}</span>
                  <span className="text-xs text-violet-400 ml-2 font-mono">{selectedProduct.itemId}</span>
                </div>
                <button onClick={() => { setItemNumber(''); setProductSearch(''); }} className="text-slate-400 hover:text-white">
                  <X size={14} />
                </button>
              </div>
            ) : (
              <div>
                <input
                  type="text" placeholder="Search product..."
                  value={productSearch}
                  onChange={e => { setProductSearch(e.target.value); setShowProductDropdown(true); }}
                  onFocus={() => setShowProductDropdown(true)}
                  className="w-full bg-slate-800/50 border border-slate-700/60 rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:ring-1 focus:ring-teal-500/50 placeholder:text-slate-600"
                />
                {showProductDropdown && filteredProducts.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-slate-800 border border-slate-700/60 rounded-lg shadow-xl max-h-48 overflow-y-auto">
                    {filteredProducts.map(p => (
                      <button
                        key={p.itemId}
                        onClick={() => { setItemNumber(p.itemId); setShowProductDropdown(false); setProductSearch(''); }}
                        className="w-full text-left px-3 py-2 hover:bg-slate-700/50 transition-colors flex items-center justify-between"
                      >
                        <span className="text-sm text-white">{p.name}</span>
                        <span className="text-[10px] text-slate-400 font-mono">{p.itemId}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Quantity *</label>
            <input
              type="number" min={1} value={quantity}
              onChange={e => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full bg-slate-800/50 border border-slate-700/60 rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:ring-1 focus:ring-teal-500/50"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800/60 flex items-center justify-end gap-3">
          <button 
            onClick={onClose}
            className="px-4 py-2.5 rounded-lg border border-slate-700/60 text-sm text-slate-400 hover:text-white hover:border-slate-600 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={() => canSubmit && onSubmit({ vendorAccount, itemNumber, quantity, entity })}
            disabled={!canSubmit || isSubmitting}
            className="px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-semibold text-sm flex items-center gap-2 transition-colors"
          >
            {isSubmitting ? (
              <><RefreshCcw size={14} className="animate-spin" /> Submitting...</>
            ) : (
              <><ShoppingCart size={14} /> Create Purchase Order</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;