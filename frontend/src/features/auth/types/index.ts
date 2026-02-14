export interface User {
  id: number;
  email: string;
  name: string;
  role_id?: number;
  is_active: boolean;
  plan_type: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
