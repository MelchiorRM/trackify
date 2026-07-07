import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'

import { login } from '@/api/auth'
import { FormField } from '@/components/common/FormField'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/store/authStore'

export default function Login() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm()
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()
  const [serverError, setServerError] = useState(null)

  const onSubmit = async (values) => {
    setServerError(null)
    try {
      const data = await login(values)
      setAuth({ user: data.user, accessToken: data.access_token })
      navigate('/')
    } catch (err) {
      setServerError(err.response?.data?.detail ?? 'Login failed')
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-65px)] items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="space-y-1 text-center">
          <CardTitle>Welcome back</CardTitle>
          <CardDescription>Log in to continue tracking what you watch, read, and listen to.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              label="Email"
              type="email"
              registration={register('email', { required: true })}
              error={errors.email && 'Email is required'}
            />
            <FormField
              label="Password"
              type="password"
              registration={register('password', { required: true })}
              error={errors.password && 'Password is required'}
            />
            {serverError && <p className="text-sm text-destructive">{serverError}</p>}
            <Button type="submit" disabled={isSubmitting} className="w-full">
              Log in
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-muted-foreground">
            No account?{' '}
            <Link to="/register" className="font-medium text-primary underline-offset-4 hover:underline">
              Register
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
