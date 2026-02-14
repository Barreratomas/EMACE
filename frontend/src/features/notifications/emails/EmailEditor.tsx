'use client';

import { useRef, useState } from 'react';
import { toast } from '@/hooks/use-toast';
import { Save, Eye, Bold, Italic, Underline, Link as LinkIcon, List, Heading, Eraser } from 'lucide-react';

export default function EmailEditor() {
  const editorRef = useRef<HTMLDivElement | null>(null);
  const [subject, setSubject] = useState('');
  const [html, setHtml] = useState('<p>Bienvenido a EMACE. Este es un ejemplo de plantilla.</p>');

  const applyCmd = (cmd: string, value?: string) => {
    try {
      document.execCommand(cmd, false, value);
    } catch {
      // noop
    }
  };

  const onInput = () => {
    if (!editorRef.current) return;
    setHtml(editorRef.current.innerHTML);
  };

  const handleSave = () => {
    toast.success('Plantilla guardada correctamente', 'EMAIL_TEMPLATE');
  };

  return (
    <div className="space-y-10">
      <div className="panel-industrial p-8 space-y-8 border-0 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h2 className="text-xl font-bold tracking-tight">Editor de Plantillas</h2>
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              className="px-5 py-2.5 bg-primary text-white rounded-xl text-[11px] font-bold uppercase tracking-wider hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
            >
              <Save size={16} /> Guardar Cambios
            </button>
            {/* <button
              className="px-5 py-2.5 bg-background/50 border border-border-ui/50 text-slate-500 rounded-xl text-[11px] font-bold uppercase tracking-wider hover:text-primary hover:border-primary/30 transition-all flex items-center gap-2"
              onClick={() => toast.info('Vista previa actualizada', 'PREVIEW')}
            >
              <Eye size={16} /> Previsualizar
            </button> */}
          </div>
        </div>

        <div className="space-y-4">
          <label className="block text-[11px] uppercase tracking-wider font-bold text-slate-500 ml-1">Asunto del Correo</label>
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full bg-slate-100/50 dark:bg-slate-900/50 border border-border-ui/50 p-4 text-slate-900 dark:text-slate-100 rounded-2xl focus:border-primary/50 focus:ring-4 focus:ring-primary/5 outline-none transition-all placeholder:text-slate-500 font-medium text-sm"
            placeholder="Ej: Confirmación de Activo Registrado"
          />
        </div>

        <div className="space-y-4">
          <label className="block text-[11px] uppercase tracking-wider font-bold text-slate-500 ml-1">Cuerpo del Mensaje</label>
          <div className="bg-background/40 backdrop-blur-md border border-border-ui/50 rounded-2xl overflow-hidden focus-within:border-primary/30 transition-colors">
            <div className="flex flex-wrap gap-1 p-2 bg-slate-50/50 dark:bg-slate-900/50 border-b border-border-ui/50">
              <button onClick={() => applyCmd('bold')} className="p-2.5 text-slate-400 hover:text-primary hover:bg-white dark:hover:bg-slate-800 rounded-lg transition-all" title="Negrita">
                <Bold size={16} />
              </button>
              <button onClick={() => applyCmd('italic')} className="p-2.5 text-slate-400 hover:text-primary hover:bg-white dark:hover:bg-slate-800 rounded-lg transition-all" title="Cursiva">
                <Italic size={16} />
              </button>
              <button onClick={() => applyCmd('underline')} className="p-2.5 text-slate-400 hover:text-primary hover:bg-white dark:hover:bg-slate-800 rounded-lg transition-all" title="Subrayado">
                <Underline size={16} />
              </button>
              <div className="w-px h-6 bg-border-ui/50 my-auto mx-1" />
              <button onClick={() => applyCmd('insertOrderedList')} className="p-2.5 text-slate-400 hover:text-primary hover:bg-white dark:hover:bg-slate-800 rounded-lg transition-all" title="Lista">
                <List size={16} />
              </button>
              <button onClick={() => applyCmd('formatBlock', 'h3')} className="p-2.5 text-slate-400 hover:text-primary hover:bg-white dark:hover:bg-slate-800 rounded-lg transition-all" title="Encabezado">
                <Heading size={16} />
              </button>
              <button
                onClick={() => {
                  const url = prompt('URL del enlace') || '';
                  if (url) applyCmd('createLink', url);
                }}
                className="p-2.5 text-slate-400 hover:text-primary hover:bg-white dark:hover:bg-slate-800 rounded-lg transition-all"
                title="Enlace"
              >
                <LinkIcon size={16} />
              </button>
              <button onClick={() => applyCmd('removeFormat')} className="p-2.5 text-slate-400 hover:text-primary hover:bg-white dark:hover:bg-slate-800 rounded-lg transition-all" title="Limpiar Formato">
                <Eraser size={16} />
              </button>
            </div>

            <div
              ref={editorRef}
              onInput={onInput}
              contentEditable
              suppressContentEditableWarning
              className="min-h-300px p-6 text-slate-900 dark:text-slate-100 outline-none font-body text-base leading-relaxed"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          </div>
        </div>
      </div>

      <div className="panel-industrial p-0 overflow-hidden border-0 shadow-xl">
        <div className="bg-background/50 backdrop-blur-md p-6 border-b border-border-ui/50">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2">
            <Eye size={14} className="text-primary" />
            Vista Previa de Comunicación
          </div>
        </div>
        <div className="p-10 bg-slate-50/30 dark:bg-slate-950/20">
          <div className="max-w-2xl mx-auto bg-white dark:bg-slate-900 rounded-3xl shadow-sm border border-border-ui/30 overflow-hidden">
            <div className="p-8 border-b border-border-ui/30 bg-slate-50/50 dark:bg-slate-900/50">
              <div className="text-sm font-bold text-slate-900 dark:text-slate-100">{subject || 'Sin Asunto'}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">De: EMACE Infrastructure <span className="text-primary">system@emace.ai</span></div>
            </div>
            <div className="p-10 prose prose-slate dark:prose-invert max-w-none">
              <div dangerouslySetInnerHTML={{ __html: html }} />
            </div>
            <div className="p-8 bg-slate-50/50 dark:bg-slate-900/50 border-t border-border-ui/30 text-center">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.3em]">
                EMACE // Ecosistema Inteligente
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

}
