import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { FormField } from '@/components/common/FormField'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useUpdateMe } from '@/hooks/useProfile'
import { useAuthStore } from '@/store/authStore'

export default function Settings() {
  const user = useAuthStore((s) => s.user)
  const updateMe = useUpdateMe()
  const [serverError, setServerError] = useState(null)
  const [saved, setSaved] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: { username: user?.username, email: user?.email } })

  const onSubmit = async (values) => {
    setServerError(null)
    setSaved(false)
    try {
      await updateMe.mutateAsync(values)
      setSaved(true)
    } catch (err) {
      setServerError(err.response?.data?.detail ?? 'Update failed')
    }
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle>Settings</CardTitle>
          <CardDescription>Update your account details.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              label="Username"
              registration={register('username', { required: true, minLength: 3 })}
              error={errors.username && 'At least 3 characters'}
            />
            <FormField
              label="Email"
              type="email"
              registration={register('email', { required: true })}
              error={errors.email && 'Email is required'}
            />
            {serverError && <p className="text-sm text-destructive">{serverError}</p>}
            {saved && <p className="text-sm text-muted-foreground">Saved.</p>}
            <Button type="submit" disabled={isSubmitting} className="w-full">
              Save changes
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
