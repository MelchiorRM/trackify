import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'

import { register as registerUser } from '@/api/auth'
import { FormField } from '@/components/common/FormField'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/store/authStore'

export default function Register() {
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
      const data = await registerUser(values)
      setAuth({ user: data.user, accessToken: data.access_token })
      navigate('/')
    } catch (err) {
      setServerError(err.response?.data?.detail ?? 'Registration failed')
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-65px)] items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="space-y-1 text-center">
          <CardTitle>Create your account</CardTitle>
          <CardDescription>Start tracking movies, books, and music in one place.</CardDescription>
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
            <FormField
              label="Password"
              type="password"
              registration={register('password', { required: true, minLength: 8 })}
              error={errors.password && 'At least 8 characters'}
            />
            {serverError && <p className="text-sm text-destructive">{serverError}</p>}
            <Button type="submit" disabled={isSubmitting} className="w-full">
              Create account
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-primary underline-offset-4 hover:underline">
              Log in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
