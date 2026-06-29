import { apiClient } from './client';

export interface DocumentUploadResponse {
  file_id: string;
  file_name: string;
  status: string;
}

export interface DocumentItem {
  file_name: string;
  upload_date: string;
}

export interface DocumentsListResponse {
  documents: DocumentItem[];
}

export interface DeleteDocumentResponse {
  chunks_deleted: number;
  file_name: string;
  file_removed_from_disk: boolean;
  msg: string;
}

// Загрузка документа
export const uploadDocumentApi = async (file: File): Promise<DocumentUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
 
  const response = await apiClient.post<DocumentUploadResponse>('/api/v1/documents/upload', formData);
  return response.data;
};

// Получение списка документов
export const getDocumentsApi = async (): Promise<DocumentsListResponse> => {
  const response = await apiClient.get<DocumentsListResponse>('/api/v1/documents');
  return response.data;
};

// удаление документа
export const deleteDocumentApi = async (fileName: string): Promise<DeleteDocumentResponse> => {
  const response = await apiClient.delete<DeleteDocumentResponse>(`/api/v1/documents/${encodeURIComponent(fileName)}`);
  return response.data;
};