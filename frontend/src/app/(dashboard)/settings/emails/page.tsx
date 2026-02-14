import EmailEditor from '@/features/notifications/emails/EmailEditor';

export const dynamic = 'force-dynamic';

export default function EmailTemplatesPage() {
  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display">
            Plantillas de Correo
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-2 font-medium">
            Gestione y personalice las comunicaciones automáticas del sistema.
          </p>
        </div>
      </div>

      <EmailEditor />
    </div>
  );
}
