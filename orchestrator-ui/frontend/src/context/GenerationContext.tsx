import React, { createContext, useContext, useState } from 'react';

interface GenerationContextType {
  activeGenerationId: string | null;
  setActiveGenerationId: (id: string | null) => void;
}

const GenerationContext = createContext<GenerationContextType | undefined>(undefined);

export const GenerationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeGenerationId, setActiveGenerationId] = useState<string | null>(null);

  return (
    <GenerationContext.Provider value={{ activeGenerationId, setActiveGenerationId }}>
      {children}
    </GenerationContext.Provider>
  );
};

export const useGenerationContext = () => {
  const context = useContext(GenerationContext);
  if (!context) {
    throw new Error('useGenerationContext must be used within GenerationProvider');
  }
  return context;
};
