import { createContext, useState } from 'react';

export const AIProviderContext = createContext<any>(null);

export function AIProviderProvider({ children }: any) {
  const [config, setConfig] = useState<any>(null);
  return (
    <AIProviderContext.Provider value={{ config, setConfig }}>
      {children}
    </AIProviderContext.Provider>
  );
}
