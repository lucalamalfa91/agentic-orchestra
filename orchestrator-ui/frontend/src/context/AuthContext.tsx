import { createContext, useState, useCallback, useEffect } from 'react';

// Helper to decode JWT and extract user info
function decodeJWT(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

export const AuthContext = createContext<any>(null);

export function AuthProvider({ children }: any) {
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState(localStorage.getItem("jwt_token"));

  // Decode JWT and set user when token changes
  useEffect(() => {
    if (token) {
      const decoded = decodeJWT(token);
      if (decoded) {
        console.log('[AuthContext] Decoded JWT:', decoded);
        setUser({
          id: decoded.user_id || decoded.sub,
          name: decoded.name || decoded.username,
          email: decoded.email
        });
      }
    } else {
      setUser(null);
    }
  }, [token]);

  const handleSetToken = useCallback((newToken: string | null) => {
    setToken(newToken);
    if (newToken) {
      localStorage.setItem("jwt_token", newToken);
    } else {
      localStorage.removeItem("jwt_token");
    }
  }, []);

  // Alias for login - same as setToken
  const login = useCallback((newToken: string) => {
    handleSetToken(newToken);
  }, [handleSetToken]);

  // Logout - clear token and user
  const logout = useCallback(() => {
    handleSetToken(null);
    setUser(null);
  }, [handleSetToken]);

  return (
    <AuthContext.Provider value={{
      user,
      setUser,
      token,
      setToken: handleSetToken,
      login,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
}
