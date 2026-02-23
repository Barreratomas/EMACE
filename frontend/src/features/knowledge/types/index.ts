export interface KnowledgeDocument {
  id: string;
  name: string;
  created_at: string;
}

export interface IngestionResponse {
  message: string;
}

export interface KnowledgeUsage {
  used_bytes: number;
  used_mb: number;
  max_bytes: number;
  max_mb: number;
  usage_ratio: number;
}
