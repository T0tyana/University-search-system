import { apiClient } from './client';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string; 
}

export interface RegisterRequest {
  username: string;
  password: string;
}

export interface RegisterResponse {
  msg: string;
}

// Авторизация
export const loginApi = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/api/v1/login', data);
  return response.data;
};

// Регистрация
export const registerApi = async (data: RegisterRequest): Promise<RegisterResponse> => {
  const response = await apiClient.post<RegisterResponse>('/api/v1/register', data);
  return response.data;
};