import { createContext, useState, useCallback } from 'react';

export const AuthContext = createContext<any>(null);

export function AuthProvider({ children }: any) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("jwt_token"));

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
