import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';
import TechStackSelector from './TechStackSelector';

export default function AdvancedSettings({ onTechStackChange }: any) {
  return (
    <Collapsible>
      <CollapsibleTrigger className="text-sm font-medium">⚙️ Advanced Settings</CollapsibleTrigger>
      <CollapsibleContent className="mt-4 space-y-4">
        <TechStackSelector onChange={onTechStackChange} />
      </CollapsibleContent>
    </Collapsible>
  );
}
