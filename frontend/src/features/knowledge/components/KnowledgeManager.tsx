'use client';

import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/Button';
import { uploadKnowledgeDocument, deleteKnowledgeDocument } from '../actions/knowledge';
import { KnowledgeDocument } from '../types';
import { 
  FileUp, 
  FileText, 
  Trash2, 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  FileCode,
  Table
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface KnowledgeManagerProps {
  initialDocuments: KnowledgeDocument[];
}

export function KnowledgeManager({ initialDocuments }: KnowledgeManagerProps) {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>(initialDocuments);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
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
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0]);
    }
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    const result = await uploadKnowledgeDocument(formData);

    if (result.success) {
      setMessage({ type: 'success', text: `Archivo "${file.name}" procesado correctamente.` });
      // Refresh local list (though Server Actions should revalidate, we optimistic update or wait for refresh)
      // For simplicity in this demo, we rely on revalidatePath + manual refresh or just show success
    } else {
      setMessage({ type: 'error', text: result.error || 'Error al subir el archivo.' });
    }

    setIsUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDelete = async (sourceName: string) => {
    setIsDeleting(sourceName);
    const result = await deleteKnowledgeDocument(sourceName);
    if (result.success) {
      setDocuments(docs => docs.filter(d => d.name !== sourceName));
      setMessage({ type: 'success', text: 'Documento eliminado.' });
    } else {
      setMessage({ type: 'error', text: result.error || 'Error al eliminar.' });
    }
    setIsDeleting(null);
  };

  const getFileIcon = (name: string) => {
    if (name.endsWith('.pdf')) return <FileText className="text-rose-500" />;
    if (name.endsWith('.md')) return <FileCode className="text-blue-500" />;
    if (name.endsWith('.csv')) return <Table className="text-emerald-500" />;
    return <FileText className="text-slate-400" />;
  };

  return (
    <div className="space-y-8">
      {/* Header & Upload Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white uppercase font-mono">
            Ingesta de <span className="text-primary">Conocimiento</span>
          </h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Sube documentos técnicos, manuales o especificaciones para que tus agentes puedan consultarlos durante las operaciones.
          </p>
          
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs flex gap-3">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <p>Los archivos se procesan automáticamente mediante embeddings vectoriales para búsqueda semántica.</p>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div 
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={cn(
              "relative h-48 rounded-2xl border-2 border-dashed transition-all flex flex-col items-center justify-center gap-4 group cursor-pointer",
              dragActive 
                ? "border-primary bg-primary/5 scale-[1.01]" 
                : "border-slate-200 dark:border-white/10 hover:border-primary/50 hover:bg-slate-50 dark:hover:bg-white/5"
            )}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              ref={fileInputRef}
              type="file" 
              className="hidden" 
              accept=".pdf,.md,.txt,.csv"
              onChange={handleFileChange}
              disabled={isUploading}
            />
            
            <div className={cn(
              "w-12 h-12 rounded-full flex items-center justify-center transition-colors",
              isUploading ? "bg-primary/20" : "bg-slate-100 dark:bg-white/5 group-hover:bg-primary/20"
            )}>
              {isUploading ? (
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
              ) : (
                <FileUp className="w-6 h-6 text-slate-500 dark:text-slate-400 group-hover:text-primary" />
              )}
            </div>
            
            <div className="text-center">
              <p className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-sm">
                {isUploading ? 'Procesando Documento...' : 'Haz clic o arrastra un archivo'}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Soporta PDF, Markdown, TXT y CSV (Max 10MB)
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      {message && (
        <div className={cn(
          "p-4 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2",
          message.type === 'success' ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20" : "bg-rose-500/10 text-rose-600 border border-rose-500/20"
        )}>
          {message.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          <p className="text-sm font-medium">{message.text}</p>
          <button onClick={() => setMessage(null)} className="ml-auto text-xs uppercase font-bold opacity-70 hover:opacity-100">Cerrar</button>
        </div>
      )}

      {/* Documents List */}
      <div className="panel-industrial overflow-hidden">
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <h3 className="text-lg font-bold uppercase tracking-widest font-mono flex items-center gap-2">
            <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
            Base de Memoria Activa
          </h3>
          <span className="text-[10px] font-mono bg-white/5 px-2 py-1 rounded border border-white/10 uppercase">
            {documents.length} Entidades Cargadas
          </span>
        </div>

        <div className="divide-y divide-white/5">
          {documents.length > 0 ? (
            documents.map((doc) => (
              <div key={doc.name} className="p-4 flex items-center justify-between hover:bg-white/5 transition-colors group">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-white/5 flex items-center justify-center">
                    {getFileIcon(doc.name)}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-primary transition-colors">
                      {doc.name}
                    </h4>
                    <p className="text-[10px] font-mono text-slate-500 uppercase">
                      ID: {doc.id.substring(0, 8)}... • Cargado: {doc.created_at}
                    </p>
                  </div>
                </div>
                
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="text-slate-400 hover:text-rose-500 hover:bg-rose-500/10"
                  disabled={isDeleting === doc.name}
                  onClick={() => handleDelete(doc.name)}
                >
                  {isDeleting === doc.name ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </Button>
              </div>
            ))
          ) : (
            <div className="p-12 text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 dark:bg-white/5 text-slate-400 mb-4">
                <FileText className="w-6 h-6" />
              </div>
              <p className="text-slate-500 text-sm">No hay documentos en la base de conocimiento.</p>
              <p className="text-xs text-slate-400 mt-1">Sube archivos para empezar a entrenar a tus agentes.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
