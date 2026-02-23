import { getKnowledgeDocuments, getKnowledgeUsage, KnowledgeManager } from '@/features/knowledge';

export const dynamic = 'force-dynamic';

export default async function KnowledgePage() {
  const [documents, usage] = await Promise.all([
    getKnowledgeDocuments(),
    getKnowledgeUsage(),
  ]);

  return (
    <div className="container mx-auto py-10 px-4">
      <KnowledgeManager initialDocuments={documents} initialUsage={usage} />
    </div>
  );
}
