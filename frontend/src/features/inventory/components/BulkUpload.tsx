'use client';

import { useState, useRef } from 'react';
import { X, Upload, FileText, CheckCircle2, AlertCircle, Loader2, ArrowRight, ArrowLeft, Database, AlertTriangle } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/Button';
import api from '@/lib/api';
import { importProducts } from '../actions/inventory';

interface BulkUploadProps {
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 'upload' | 'preview' | 'result';

export default function BulkUpload({ onClose, onSuccess }: BulkUploadProps) {
  const [step, setStep] = useState<Step>('upload');
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [conflictStrategy, setConflictStrategy] = useState<'skip' | 'update'>('skip');
  const [previewData, setPreviewData] = useState<any>(null);
  const [resultData, setResultData] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const validateAndSetFile = (file: File) => {
    const validTypes = ['.csv', '.xlsx'];
    const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (validTypes.includes(extension)) {
      setFile(file);
    } else {
      toast.error('Formato no soportado. Use .csv o .xlsx', 'ARCHIVO_INVALIDO');
    }
  };

  const handlePreview = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const result = await importProducts(formData, conflictStrategy, true);
      if (result.dry_run) {
        setPreviewData(result);
        setStep('preview');
      } else {
        throw new Error(result.error || 'Error al generar previsualización');
      }
    } catch (error: any) {
      toast.error(error.message, 'ERROR_PREVISUALIZACION');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const result = await importProducts(formData, conflictStrategy, false);
      if (!result.error) {
        setResultData(result);
        setStep('result');
        toast.success('Importación completada correctamente', 'EXITO');
      } else {
        throw new Error(result.error);
      }
    } catch (error: any) {
      toast.error(error.message, 'ERROR_IMPORTACION');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTemplate = async (format: 'csv' | 'xlsx') => {
    try {
      const response = await api.get('/inventory/import/template', {
        params: { format },
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `plantilla_inventario.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Error al descargar plantilla de inventario:', error);
      toast.error('Error al descargar la plantilla', 'ERROR_DESCARGA_PLANTILLA');
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-999 animate-in fade-in duration-300">
      <div className="panel-industrial p-0 w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col border-0 shadow-2xl">
        {/* Header */}
        <div className="border-b border-border-ui/50 p-6 flex justify-between items-center bg-background/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg text-primary">
              <Database size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight font-display">Asistente de Importación</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest ${step === 'upload' ? 'bg-primary text-white' : 'bg-slate-200 dark:bg-slate-800 text-slate-500'}`}>1. Carga</span>
                <div className="w-4 h-1px bg-slate-300 dark:bg-slate-700" />
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest ${step === 'preview' ? 'bg-primary text-white' : 'bg-slate-200 dark:bg-slate-800 text-slate-500'}`}>2. Previa</span>
                <div className="w-4 h-1px bg-slate-300 dark:bg-slate-700" />
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest ${step === 'result' ? 'bg-primary text-white' : 'bg-slate-200 dark:bg-slate-800 text-slate-500'}`}>3. Resultado</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all text-slate-500">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-8">
          {step === 'upload' && (
            <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-300">
              <div 
                className={`relative border-2 border-dashed rounded-3xl p-12 transition-all flex flex-col items-center justify-center text-center gap-6 ${
                  dragActive ? 'border-primary bg-primary/5' : 'border-border-ui/50 bg-slate-50/50 dark:bg-slate-900/50'
                } ${file ? 'border-emerald-500/50 bg-emerald-500/5' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={(e) => e.target.files?.[0] && validateAndSetFile(e.target.files[0])}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                
                <div className={`p-6 rounded-2xl ${file ? 'bg-emerald-500/10 text-emerald-500' : 'bg-primary/10 text-primary'}`}>
                  {file ? <FileText size={48} /> : <Upload size={48} />}
                </div>

                <div className="max-w-xs">
                  <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    {file ? file.name : 'Arrastra tu catálogo aquí'}
                  </p>
                  <p className="text-sm text-slate-500 mt-2">Soporta archivos CSV y Excel (.xlsx) de hasta 10MB</p>
                </div>

                {file && (
                  <div className="flex items-center gap-2 text-[10px] font-bold text-emerald-600 bg-emerald-500/10 px-4 py-1.5 rounded-full uppercase tracking-widest border border-emerald-500/20">
                    <CheckCircle2 size={14} /> Archivo cargado correctamente
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="panel-industrial p-6 space-y-4 bg-slate-50/30">
                  <h4 className="text-[11px] font-bold uppercase tracking-widest text-slate-500 flex items-center gap-2">
                    <Database size={14} /> Estrategia de Conflicto
                  </h4>
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 p-3 rounded-xl border border-border-ui/50 bg-white dark:bg-slate-900 cursor-pointer hover:border-primary/50 transition-all group">
                      <input 
                        type="radio" 
                        name="conflict" 
                        checked={conflictStrategy === 'skip'} 
                        onChange={() => setConflictStrategy('skip')}
                        className="text-primary focus:ring-primary/20"
                      />
                      <div>
                        <div className="text-xs font-bold group-hover:text-primary">Omitir Duplicados</div>
                        <div className="text-[10px] text-slate-500">No procesar productos con nombres existentes.</div>
                      </div>
                    </label>
                    <label className="flex items-center gap-3 p-3 rounded-xl border border-border-ui/50 bg-white dark:bg-slate-900 cursor-pointer hover:border-primary/50 transition-all group">
                      <input 
                        type="radio" 
                        name="conflict" 
                        checked={conflictStrategy === 'update'} 
                        onChange={() => setConflictStrategy('update')}
                        className="text-primary focus:ring-primary/20"
                      />
                      <div>
                        <div className="text-xs font-bold group-hover:text-primary">Actualizar Existentes</div>
                        <div className="text-[10px] text-slate-500">Sobrescribir datos si el producto ya existe.</div>
                      </div>
                    </label>
                  </div>
                </div>

                <div className="panel-industrial p-6 space-y-4 bg-slate-50/30">
                  <h4 className="text-[11px] font-bold uppercase tracking-widest text-slate-500 flex items-center gap-2">
                    <AlertCircle size={14} /> Esquema Requerido
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {['name', 'category', 'price'].map(col => (
                      <span key={col} className="px-2 py-1 bg-primary/5 border border-primary/20 text-primary text-[10px] font-mono font-bold rounded">{col}</span>
                    ))}
                    {['description', 'stock', 'type'].map(col => (
                      <span key={col} className="px-2 py-1 bg-slate-100 dark:bg-slate-800 border border-border-ui/50 text-slate-500 text-[10px] font-mono font-bold rounded">{col}</span>
                    ))}
                  </div>
                  <p className="text-[10px] text-slate-500 leading-relaxed italic">
                    * El sistema normalizará automáticamente los encabezados a minúsculas y eliminará espacios adicionales.
                  </p>
                  <div className="mt-4 flex flex-col gap-3">
                    <p className="text-[10px] text-slate-500">
                      Puedes descargar una plantilla de ejemplo para completar tu catálogo.
                    </p>
                    <div className="flex flex-col gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadTemplate('csv')}
                      >
                        <FileText size={14} className="mr-1" />
                        Plantilla CSV
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadTemplate('xlsx')}
                      >
                        <FileText size={14} className="mr-1" />
                        Plantilla XLSX
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 'preview' && (
            <div className="space-y-6 animate-in slide-in-from-right-4 duration-300">
              <div className="flex justify-between items-center bg-amber-500/10 border border-amber-500/20 p-4 rounded-2xl">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-500/20 rounded-lg text-amber-600 dark:text-amber-400">
                    <AlertTriangle size={20} />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-amber-900 dark:text-amber-100">Modo Previsualización</h4>
                    <p className="text-[11px] text-amber-700/70 dark:text-amber-400/70">Revise los datos antes de aplicar los cambios en la base de datos.</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-black text-amber-600">{previewData?.total_processed}</div>
                  <div className="text-[9px] font-bold uppercase tracking-widest text-amber-700/50">Registros</div>
                </div>
              </div>

              <div className="panel-industrial overflow-hidden p-0 border-border-ui/50">
                <div className="max-h-75 overflow-y-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="sticky top-0 bg-slate-50 dark:bg-slate-900 border-b border-border-ui/50 z-10">
                      <tr>
                        <th className="p-3 font-bold uppercase tracking-wider text-slate-500">Producto</th>
                        <th className="p-3 font-bold uppercase tracking-wider text-slate-500">Categoría</th>
                        <th className="p-3 font-bold uppercase tracking-wider text-slate-500">Precio</th>
                        <th className="p-3 font-bold uppercase tracking-wider text-slate-500">Estado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-ui/30">
                      {previewData?.preview?.slice(0, 50).map((row: any, i: number) => (
                        <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/50 transition-colors">
                          <td className="p-3">
                            <div className="font-bold">{row.name}</div>
                            <div className="text-[10px] text-slate-400 uppercase">{row.type}</div>
                          </td>
                          <td className="p-3 text-slate-600 dark:text-slate-400">{row.category}</td>
                          <td className="p-3 font-mono">${row.price}</td>
                          <td className="p-3">
                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-widest ${
                              row.conflict === 'update' ? 'bg-amber-100 text-amber-600' : 'bg-emerald-100 text-emerald-600'
                            }`}>
                              {row.conflict === 'update' ? 'Actualizar' : 'Nuevo'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {previewData?.preview?.length > 50 && (
                    <div className="p-4 text-center text-[10px] text-slate-500 bg-slate-50/30">
                      ... y {previewData.preview.length - 50} registros más.
                    </div>
                  )}
                </div>
              </div>

              {previewData?.errors?.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-2xl">
                  <h4 className="text-[10px] font-bold text-red-600 uppercase tracking-widest mb-2">Errores Detectados ({previewData.errors.length})</h4>
                  <ul className="text-[10px] text-red-500 space-y-1 font-mono">
                    {previewData.errors.slice(0, 5).map((err: string, i: number) => (
                      <li key={i}>• {err}</li>
                    ))}
                    {previewData.errors.length > 5 && <li>... y {previewData.errors.length - 5} errores más.</li>}
                  </ul>
                </div>
              )}
            </div>
          )}

          {step === 'result' && (
            <div className="flex flex-col items-center justify-center py-12 space-y-8 animate-in zoom-in-95 duration-500">
              <div className="relative">
                <div className="w-24 h-24 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-500">
                  <CheckCircle2 size={64} />
                </div>
                <div className="absolute -bottom-2 -right-2 bg-white dark:bg-slate-900 p-1.5 rounded-full shadow-lg">
                  <div className="bg-emerald-500 w-4 h-4 rounded-full animate-ping" />
                </div>
              </div>

              <div className="text-center space-y-2">
                <h3 className="text-2xl font-bold font-display">¡Importación Exitosa!</h3>
                <p className="text-sm text-slate-500">El catálogo ha sido actualizado en el servidor central.</p>
              </div>

              <div className="grid grid-cols-3 gap-4 w-full max-w-md">
                {[
                  { label: 'Importados', val: resultData.imported, color: 'text-emerald-500' },
                  { label: 'Actualizados', val: resultData.updated, color: 'text-amber-500' },
                  { label: 'Omitidos', val: resultData.skipped, color: 'text-slate-400' }
                ].map(stat => (
                  <div key={stat.label} className="panel-industrial p-4 text-center bg-slate-50/50">
                    <div className={`text-xl font-black ${stat.color}`}>{stat.val}</div>
                    <div className="text-[9px] font-bold uppercase tracking-widest text-slate-400">{stat.label}</div>
                  </div>
                ))}
              </div>

              {resultData.errors?.length > 0 && (
                <div className="w-full max-w-md p-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/30 rounded-xl">
                  <div className="text-xs font-bold text-red-600 mb-2">Resumen de Errores ({resultData.errors.length})</div>
                  <div className="max-h-24 overflow-y-auto text-[10px] font-mono text-red-500/80 space-y-1">
                    {resultData.errors.map((e: string, i: number) => <div key={i}>• {e}</div>)}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border-ui/50 p-6 flex justify-between items-center bg-background/50 backdrop-blur-md">
          {step === 'upload' ? (
            <Button variant="outline" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
          ) : (
            <Button variant="outline" onClick={() => setStep(step === 'preview' ? 'upload' : 'preview')} disabled={loading}>
              <ArrowLeft size={16} />
              Volver
            </Button>
          )}

          <div className="flex gap-3">
            {step === 'upload' && (
              <Button 
                variant="cyber" 
                onClick={handlePreview} 
                disabled={!file || loading}
                className="min-w-40"
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <><ArrowRight size={18} /> Previsualizar</>}
              </Button>
            )}
            {step === 'preview' && (
              <Button 
                variant="cyber" 
                onClick={handleConfirmImport} 
                disabled={loading}
                className="min-w-40 bg-emerald-600! border-emerald-500! shadow-emerald-500/20"
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <><CheckCircle2 size={18} /> Confirmar Carga</>}
              </Button>
            )}
            {step === 'result' && (
              <Button variant="cyber" onClick={onClose}>
                Finalizar
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
