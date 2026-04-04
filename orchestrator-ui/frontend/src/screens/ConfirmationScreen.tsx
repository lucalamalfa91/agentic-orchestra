import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';

export default function ConfirmationScreen({ decisions, onConfirm, onEdit }: any) {
  if (!decisions) return null;

  const { tech_stack, reasoning } = decisions;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">✓ AI Design Confirmed</h2>

      <Card className="p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Frontend</p>
            <p className="text-lg font-bold">{tech_stack?.frontend}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Backend</p>
            <p className="text-lg font-bold">{tech_stack?.backend}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Database</p>
            <p className="text-lg font-bold">{tech_stack?.database}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Deploy</p>
            <p className="text-lg font-bold">{tech_stack?.deploy_platform}</p>
          </div>
        </div>

        {reasoning && (
          <div className="border-t pt-4">
            <p className="text-sm text-gray-600">AI Reasoning</p>
            <p className="text-sm mt-2">{reasoning}</p>
          </div>
        )}
      </Card>

      <div className="flex gap-4">
        <Button onClick={onEdit} variant="outline" className="flex-1">
          Change Settings
        </Button>
        <Button onClick={onConfirm} className="flex-1 bg-green-600 hover:bg-green-700">
          Looks Good, Continue
        </Button>
      </div>
    </div>
  );
}
