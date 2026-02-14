'use client';

import { useMemo, useState } from 'react';
import { Product } from '../types';
import { deleteProduct, adjustStock, bulkUpdateProductStatus } from '../actions/inventory';
import { Plus, Edit, Trash2, Package, Search, AlertTriangle, CheckCircle, PauseCircle, Archive, MoreHorizontal, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import ProductForm from './ProductForm';
import { Button } from '@/components/ui/Button';

export default function InventoryList({ initialProducts }: { initialProducts: Product[] }) {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'paused' | 'archived'>('all');
  const [typeFilter, setTypeFilter] = useState<'all' | 'physical' | 'service'>('all');
  const [search, setSearch] = useState('');
  const [lowOnly, setLowOnly] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [bulkStatus, setBulkStatus] = useState<'active' | 'paused' | 'archived'>('paused');

  const handleEdit = (p: Product) => {
    setEditingProduct(p);
    setIsFormOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('¿CONFIRMAR DESMANTELAMIENTO DE ACTIVO?')) {
      await deleteProduct(id);
    }
  };

  const toggleSelect = (id: number) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const applyBulkStatus = async () => {
    if (selected.size === 0) return;
    await bulkUpdateProductStatus(Array.from(selected), bulkStatus);
    setSelected(new Set());
  };

  const filtered = useMemo(() => {
    return initialProducts.filter(p => {
      if (statusFilter !== 'all' && p.status !== statusFilter) return false;
      if (typeFilter !== 'all' && p.type !== typeFilter) return false;
      if (lowOnly && p.type === 'physical') {
        const stock = p.stock ?? 0;
        const min = p.min_stock_threshold ?? 5;
        if (!(stock < min)) return false;
      }
      if (search) {
        const s = search.toLowerCase();
        if (!(p.name.toLowerCase().includes(s) || p.category.toLowerCase().includes(s))) return false;
      }
      return true;
    });
  }, [initialProducts, statusFilter, typeFilter, search, lowOnly]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle size={14} className="text-emerald-500" />;
      case 'paused': return <PauseCircle size={14} className="text-amber-500" />;
      case 'archived': return <Archive size={14} className="text-zinc-500" />;
      default: return null;
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 pb-8 border-b border-border-ui/50">
        <div>
          <div className="flex items-center gap-2 text-primary text-[11px] font-bold mb-3 uppercase tracking-[0.2em]">
            <Package size={14} className="animate-pulse" /> Asset Management System
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display">Inventario Central</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Gestione y supervise los activos críticos de la infraestructura.</p>
        </div>
        <Button
          variant="cyber"
          onClick={() => { setEditingProduct(undefined); setIsFormOpen(true); }}
        >
          <Plus size={18} />
          Registrar Activo
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <div className="panel-industrial p-6 space-y-6">
            <div className="flex items-center gap-2 pb-4 border-b border-border-ui/30">
              <Search className="text-primary" size={16} />
              <h3 className="text-sm font-bold tracking-tight">Filtros de Sistema</h3>
            </div>
            
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-[11px] text-slate-500 uppercase font-bold tracking-wider">Búsqueda Global</label>
                <div className="relative group">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={14} />
                  <input 
                    type="text" 
                    placeholder="Filtrar por nombre..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-slate-100/50 dark:bg-slate-900/50 border border-border-ui/50 py-2.5 pl-10 pr-4 rounded-xl text-xs focus:border-primary/50 focus:ring-4 focus:ring-primary/5 outline-none transition-all placeholder:text-slate-500"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] text-slate-500 uppercase font-bold tracking-wider">Estado Operacional</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['all', 'active', 'paused', 'archived'] as const).map((s) => (
                    <button
                      key={s}
                      onClick={() => setStatusFilter(s)}
                      className={`px-3 py-2 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all border ${
                        statusFilter === s 
                          ? 'bg-primary text-white border-primary shadow-md shadow-primary/20' 
                          : 'bg-slate-50 dark:bg-slate-900/30 border-border-ui/50 text-slate-500 hover:border-primary/30'
                      }`}
                    >
                      {s === 'all' ? 'Todos' : s === 'active' ? 'Activo' : s === 'paused' ? 'Pausa' : 'Archiv'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-border-ui/30">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className={`w-10 h-5 rounded-full p-1 transition-colors ${lowOnly ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-800'}`}>
                    <div className={`w-3 h-3 bg-white rounded-full transition-transform ${lowOnly ? 'translate-x-5' : 'translate-x-0'}`} />
                  </div>
                  <input 
                    type="checkbox" 
                    className="hidden" 
                    checked={lowOnly}
                    onChange={(e) => setLowOnly(e.target.checked)}
                  />
                  <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 group-hover:text-primary transition-colors">Bajo Stock Únicamente</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          <div className="panel-industrial overflow-hidden border-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/50 dark:bg-slate-900/50 border-b border-border-ui/50">
                    <th className="p-5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                      <div className="flex items-center gap-2">
                        <input 
                          type="checkbox" 
                          className="rounded border-slate-300 dark:border-slate-700 text-primary focus:ring-primary/20"
                          onChange={(e) => {
                            if (e.target.checked) setSelected(new Set(filtered.map(p => p.id)));
                            else setSelected(new Set());
                          }}
                        />
                        Identificador
                      </div>
                    </th>
                    <th className="p-5 text-[10px] font-bold uppercase tracking-widest text-slate-500">Categoría / Tipo</th>
                    <th className="p-5 text-[10px] font-bold uppercase tracking-widest text-slate-500 text-right">Valor / Stock</th>
                    <th className="p-5 text-[10px] font-bold uppercase tracking-widest text-slate-500">Estado</th>
                    <th className="p-5 text-[10px] font-bold uppercase tracking-widest text-slate-500 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-ui/30">
                  {filtered.map((p) => {
                    const isLow = p.type === 'physical' && (p.stock || 0) <= (p.min_stock_threshold || 5);
                    return (
                      <tr 
                        key={p.id} 
                        className={`group transition-colors hover:bg-primary/2 cursor-default ${selected.has(p.id) ? 'bg-primary/5' : ''}`}
                      >
                        <td className="p-5">
                          <div className="flex items-center gap-3">
                            <input 
                              type="checkbox" 
                              checked={selected.has(p.id)}
                              onChange={() => toggleSelect(p.id)}
                              className="rounded border-slate-300 dark:border-slate-700 text-primary focus:ring-primary/20"
                            />
                            <div>
                              <div className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-primary transition-colors">{p.name}</div>
                              <div className="text-[10px] font-medium text-slate-400 uppercase tracking-tight">REF: {p.id.toString().padStart(6, '0')}</div>
                            </div>
                          </div>
                        </td>
                        <td className="p-5">
                          <div className="flex flex-col gap-1">
                            <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">{p.category}</span>
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md w-fit uppercase ${
                              p.type === 'physical' ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'
                            }`}>
                              {p.type}
                            </span>
                          </div>
                        </td>
                        <td className="p-5 text-right">
                          <div className="text-sm font-bold text-slate-900 dark:text-slate-100">${p.price.toLocaleString()}</div>
                          <div className={`text-[10px] font-bold mt-1 ${isLow ? 'text-rose-500' : 'text-slate-400'}`}>
                            {p.type === 'physical' ? `${p.stock} UNIDADES` : 'SLA ACTIVO'}
                          </div>
                        </td>
                        <td className="p-5">
                          <div className={`flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider ${
                            p.status === 'active' ? 'text-emerald-500' : 
                            p.status === 'paused' ? 'text-amber-500' : 'text-slate-400'
                          }`}>
                            <div className={`w-1.5 h-1.5 rounded-full ${
                              p.status === 'active' ? 'bg-emerald-500 animate-pulse' : 
                              p.status === 'paused' ? 'bg-amber-500' : 'bg-slate-400'
                            }`} />
                            {p.status}
                          </div>
                        </td>
                        <td className="p-5 text-right">
                          <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button 
                              onClick={() => handleEdit(p)}
                              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-primary transition-all"
                            >
                              <Edit size={16} />
                            </button>
                            <button 
                              onClick={() => handleDelete(p.id)}
                              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-rose-500 transition-all"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {filtered.length === 0 && (
              <div className="p-20 text-center flex flex-col items-center gap-4 bg-background/50">
                <div className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-slate-900 flex items-center justify-center text-slate-300 dark:text-slate-700">
                  <Search size={32} />
                </div>
                <div>
                  <div className="font-bold text-slate-900 dark:text-slate-100">No se encontraron resultados</div>
                  <div className="text-xs text-slate-500 mt-1">Intente ajustar los filtros de búsqueda</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {isFormOpen && (
        <ProductForm 
          product={editingProduct} 
          onClose={() => setIsFormOpen(false)} 
          onSuccess={() => {}} 
        />
      )}
    </div>
  );
}
