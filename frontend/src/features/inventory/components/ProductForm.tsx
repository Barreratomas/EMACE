'use client';

import { useState } from 'react';
import { Product } from '../types';
import { createProduct, updateProduct } from '../actions/inventory';
import { X, Save, AlertTriangle } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/Button';

interface ProductFormProps {
  product?: Product;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ProductForm({ product, onClose, onSuccess }: ProductFormProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<Partial<Product>>(
    product || {
      name: '',
      category: 'General',
      price: 0,
      type: 'physical',
      status: 'active',
      stock: 0,
      min_stock_threshold: 5,
      sla: '',
      description: '',
    }
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (product) {
        await updateProduct(product.id, formData);
        toast.success(`Activo ${formData.name} actualizado correctamente`, 'REGISTRO_ACTUALIZADO');
      } else {
        await createProduct(formData);
        toast.success(`Activo ${formData.name} registrado en el sistema`, 'REGISTRO_EXITOSO');
      }
      onSuccess();
      onClose();
    } catch (error: unknown) {
      console.error('Error saving product:', error);
      const message = error instanceof Error ? error.message : 'Error al procesar la solicitud';
      toast.error(message, 'ERROR_DE_SISTEMA');
    } finally {
      setLoading(false);
    }
  };

  const inputClasses = "w-full bg-slate-100/50 dark:bg-slate-900/50 border border-border-ui/50 p-3 rounded-xl text-sm focus:border-primary/50 focus:ring-4 focus:ring-primary/5 outline-none transition-all placeholder:text-slate-500";
  const labelClasses = "block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5";

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-[999] animate-in fade-in duration-300">
      <div className="panel-industrial p-0 w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col border-0">
        {/* Header */}
        <div className="border-b border-border-ui/50 p-6 flex justify-between items-center bg-background/50 backdrop-blur-md">
          <div>
            <h2 className="text-xl font-bold tracking-tight font-display">
              {product ? 'Modificar Activo' : 'Registrar Nuevo Activo'}
            </h2>
            <p className="text-[11px] text-slate-500 font-medium mt-1 uppercase tracking-wider">
              ID: {product ? product.id : 'N/A'} • ESTADO: {formData.status}
            </p>
          </div>
          <button 
            onClick={onClose} 
            className="p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all text-slate-500 hover:text-slate-900 dark:hover:text-slate-100"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit} className="p-8 space-y-8 overflow-y-auto flex-1 bg-background/30">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Basic Info */}
            <div className="space-y-6">
              <div>
                <label className={labelClasses}>Identificador de Activo</label>
                <input
                  required
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={inputClasses}
                  placeholder="Ej: Servidor Central RACK-01"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClasses}>Tipo de Recurso</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value as 'physical' | 'service' })}
                    className={inputClasses}
                  >
                    <option value="physical">Físico</option>
                    <option value="service">Servicio</option>
                  </select>
                </div>
                <div>
                  <label className={labelClasses}>Categoría</label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className={inputClasses}
                    placeholder="Categoría"
                  />
                </div>
              </div>

              <div>
                <label className={labelClasses}>Valor Unitario (USD)</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-primary font-bold text-sm">$</span>
                  <input
                    required
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
                    className={`${inputClasses} pl-8`}
                    placeholder="0.00"
                  />
                </div>
              </div>
            </div>

            {/* Status & Stock */}
            <div className="space-y-6">
              <div>
                <label className={labelClasses}>Estado Operacional</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as 'active' | 'paused' | 'archived' })}
                  className={`${inputClasses} font-semibold ${
                    formData.status === 'active' ? 'text-emerald-500' : 
                    formData.status === 'paused' ? 'text-amber-500' : 'text-slate-500'
                  }`}
                >
                  <option value="active">Activo / Online</option>
                  <option value="paused">Pausado / Standby</option>
                  <option value="archived">Archivado / Offline</option>
                </select>
              </div>

              {formData.type === 'physical' ? (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClasses}>Unidades Disponibles</label>
                    <input
                      type="number"
                      value={formData.stock}
                      onChange={(e) => setFormData({ ...formData, stock: parseInt(e.target.value) })}
                      className={inputClasses}
                    />
                  </div>
                  <div>
                    <label className={labelClasses}>Umbral de Alerta</label>
                    <input
                      type="number"
                      value={formData.min_stock_threshold}
                      onChange={(e) => setFormData({ ...formData, min_stock_threshold: parseInt(e.target.value) })}
                      className={inputClasses}
                    />
                  </div>
                </div>
              ) : (
                <div>
                  <label className={labelClasses}>Acuerdo de Nivel de Servicio (SLA)</label>
                  <input
                    type="text"
                    placeholder="Ej: 24/7 Soporte Crítico"
                    value={formData.sla || ''}
                    onChange={(e) => setFormData({ ...formData, sla: e.target.value })}
                    className={inputClasses}
                  />
                </div>
              )}

              <div>
                <label className={labelClasses}>Especificaciones / Notas</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className={`${inputClasses} resize-none`}
                  rows={3}
                  placeholder="Detalles adicionales del activo..."
                />
              </div>
            </div>
          </div>

          {/* Warning area if stock is low */}
          {formData.type === 'physical' && (formData.stock || 0) <= (formData.min_stock_threshold || 0) && (
            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/50 p-4 rounded-2xl flex items-center gap-3">
              <AlertTriangle className="text-amber-500" size={20} />
              <p className="text-xs font-medium text-amber-700 dark:text-amber-400">
                Atención: Stock por debajo del umbral crítico.
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t border-border-ui/50">
            <Button
              variant="ghost"
              type="button"
              onClick={onClose}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              variant="cyber"
              type="submit"
              disabled={loading}
            >
              <Save size={18} />
              {loading ? 'Procesando...' : product ? 'Actualizar Activo' : 'Confirmar Registro'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
