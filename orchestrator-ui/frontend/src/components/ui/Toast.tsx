import { useState, useCallback } from 'react';

const useToast = () => {
  const [toasts, setToasts] = useState<any[]>([]);

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info', duration = 3000) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  return { toasts, showToast };
};

export function Toast({ message, type }: { message: string; type: 'success' | 'error' | 'info' }) {
  const bgColors: Record<'success' | 'error' | 'info', string> = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500'
  };
  const bgColor = bgColors[type];

  return (
    <div className={`${bgColor} text-white px-4 py-2 rounded-lg shadow-lg`}>
      {message}
    </div>
  );
}

export { useToast };
