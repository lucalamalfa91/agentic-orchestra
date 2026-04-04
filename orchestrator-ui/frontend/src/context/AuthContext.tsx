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

  return (
    <AuthContext.Provider value={{ user, setUser, token, setToken: handleSetToken }}>
      {children}
    </AuthContext.Provider>
  );
}
