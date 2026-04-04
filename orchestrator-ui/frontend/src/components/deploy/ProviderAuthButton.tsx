import { Button } from '../ui/button';

interface ProviderAuthButtonProps {
  provider: string;
  onClick: () => void;
}

export default function ProviderAuthButton({ provider, onClick }: ProviderAuthButtonProps) {
  return (
    <Button onClick={onClick} className="w-full">
      🔗 Connect {provider}
    </Button>
  );
}
