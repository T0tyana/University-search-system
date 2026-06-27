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

export interface SearchResponse {
  results: SearchResult[];
}

// Поиск
export const searchApi = async (query: string): Promise<SearchResponse> => {
  const response = await apiClient.get<SearchResponse>('/api/v1/search', {
    params: { q: query }
  });
  return response.data;
};