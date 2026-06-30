import { apiClient } from './client';

export interface SearchHistoryItemApi {
  query: string;
  files_found: string[];
  total_results: number;
  timestamp: string;
}

export interface SearchHistoryResponse {
  history: SearchHistoryItemApi[];
}

// Получение истории поиска 
export const getSearchHistoryApi = async (): Promise<SearchHistoryResponse> => {
  const response = await apiClient.get<SearchHistoryResponse>('/api/v1/search/history');
  return response.data;
};


export interface SearchResult {
  chunk_id: string;
  file_name: string;
  page: number;
  text: string;
  score: number;
}

// 
export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;   // <-- Общее кол-во результатов (нужно для скролла)
  page: number;    // <-- Текущая страница
  size: number;    // <-- Размер страницы
}

// Поиск
export const searchApi = async (
  query: string, 
  page: number = 1, 
  size: number = 10, 
  fileName?: string // Опциональный фильтр, пока не используем в UI
): Promise<SearchResponse> => {
  const params: any = { q: query, page, size };
  if (fileName) {
    params.file_name = fileName;
  }
  
  const response = await apiClient.get<SearchResponse>('/api/v1/search', { params });
  return response.data;
};