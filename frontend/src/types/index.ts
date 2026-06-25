export interface UploadedFile {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'txt';
  status: 'uploading' | 'indexing' | 'completed' | 'error';
  progress: number;
  uploadedAt?: Date;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: Date;
}