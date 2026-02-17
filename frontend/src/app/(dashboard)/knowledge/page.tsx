import { getKnowledgeDocuments, KnowledgeManager } from '@/features/knowledge';

export const dynamic = 'force-dynamic';

export default async function KnowledgePage() {
  const documents = await getKnowledgeDocuments();

  return (
    <div className="container mx-auto py-10 px-4">
      <KnowledgeManager initialDocuments={documents} />
    </div>
  );
}
