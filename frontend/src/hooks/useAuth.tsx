import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import { authApi, User, LoginCredentials, RegisterData, api } from '../api/client';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!user;

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const userData = await authApi.me();
        setUser(userData);
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      setError(null);
      setLoading(true);

      const tokenResponse = await authApi.login(credentials);
      // CRITICAL FIX: Save tokens to localStorage
      api.setTokens(tokenResponse.access_token, tokenResponse.refresh_token);

      const userData = await authApi.me();
      setUser(userData);
    } catch (err: unknown) {
      const errorResponse = err as { response?: { data?: { detail?: string } }; message?: string };
      const message = errorResponse.response?.data?.detail || errorResponse.message || 'Login failed';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    try {
      setError(null);
      setLoading(true);

      await authApi.register(data);

      const tokenResponse = await authApi.login({ email: data.email, password: data.password });
      // CRITICAL FIX: Save tokens to localStorage
      api.setTokens(tokenResponse.access_token, tokenResponse.refresh_token);

      const userData = await authApi.me();
      setUser(userData);
    } catch (err: unknown) {
      const errorResponse = err as { response?: { data?: { detail?: string } }; message?: string };
      const message = errorResponse.response?.data?.detail || errorResponse.message || 'Registration failed';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    authApi.logout();
    setUser(null);
    setError(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authApi.me();
      setUser(userData);
    } catch {
      setUser(null);
      authApi.logout();
    }
  }, []);

  const value: AuthContextType = {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default useAuth;
