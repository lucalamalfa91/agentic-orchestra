import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

export default function TechStackSelector({ onChange }: any) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <label className="text-sm font-medium">Frontend</label>
        <Select onValueChange={(v) => onChange({ frontend: v })}>
          <SelectTrigger>
            <SelectValue placeholder="React" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="react">React</SelectItem>
            <SelectItem value="vue">Vue</SelectItem>
            <SelectItem value="angular">Angular</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-sm font-medium">Backend</label>
        <Select onValueChange={(v) => onChange({ backend: v })}>
          <SelectTrigger>
            <SelectValue placeholder=".NET" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="dotnet">.NET</SelectItem>
            <SelectItem value="node">Node.js</SelectItem>
            <SelectItem value="python">Python</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-sm font-medium">Database</label>
        <Select onValueChange={(v) => onChange({ database: v })}>
          <SelectTrigger>
            <SelectValue placeholder="PostgreSQL" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="postgresql">PostgreSQL</SelectItem>
            <SelectItem value="mysql">MySQL</SelectItem>
            <SelectItem value="mongodb">MongoDB</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-sm font-medium">Deploy</label>
        <Select onValueChange={(v) => onChange({ deploy: v })}>
          <SelectTrigger>
            <SelectValue placeholder="Vercel" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="vercel">Vercel</SelectItem>
            <SelectItem value="railway">Railway</SelectItem>
            <SelectItem value="render">Render</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
