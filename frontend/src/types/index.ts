export interface UploadedFile {
  id: string;
  name: string;
  type: 'pdf' | 'docx';
  status: 'uploading' | 'indexing' | 'completed' | 'error' | 'deleting';
  progress: number;
  uploadedAt?: Date | string;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: Date | string;
  files_found?: string[];
  total_results?: number;
}