import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function FormField({ label, error, registration, type = 'text', ...props }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={registration.name}>{label}</Label>
      <Input id={registration.name} type={type} {...registration} {...props} />
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
