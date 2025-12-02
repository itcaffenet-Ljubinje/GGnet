import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { clsx } from 'clsx'

interface LoginForm {
  username: string
  password: string
}

export default function LoginPage() {
  console.log('LoginPage component rendering')
  const [showPassword, setShowPassword] = useState(false)
  const { login, isLoading } = useAuthStore()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<LoginForm>()

  const onSubmit = async (data: LoginForm) => {
    try {
      const success = await login(data.username, data.password)
      if (!success) {
        setError('root', {
          type: 'manual',
          message: 'Invalid username or password',
        })
      }
    } catch (error) {
      setError('root', {
        type: 'manual',
        message: 'Login failed. Please try again.',
      })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-16 w-16 bg-blue-600 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-2xl">GG</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            Sign in to GGnet
          </h2>
          <p className="mt-2 text-center text-sm text-gray-300">
            Diskless Server Management Console
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="username" className="sr-only">
                Username
              </label>
              <input
                {...register('username', {
                  required: 'Username is required',
                  minLength: {
                    value: 3,
                    message: 'Username must be at least 3 characters',
                  },
                })}
                type="text"
                autoComplete="username"
                className={clsx(
                  'relative block w-full px-3 py-2 border placeholder-gray-400 text-white bg-gray-800 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
                  errors.username
                    ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                    : 'border-gray-600'
                )}
                placeholder="Username"
                disabled={isLoading}
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-400">{errors.username.message}</p>
              )}
            </div>
            
            <div className="relative">
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 6,
                    message: 'Password must be at least 6 characters',
                  },
                })}
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                className={clsx(
                  'relative block w-full px-3 py-2 pr-10 border placeholder-gray-400 text-white bg-gray-800 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
                  errors.password
                    ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                    : 'border-gray-600'
                )}
                placeholder="Password"
                disabled={isLoading}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400" />
                )}
              </button>
              {errors.password && (
                <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
              )}
            </div>
          </div>

          {errors.root && (
            <div className="rounded-md bg-red-900/50 border border-red-500 p-4">
              <div className="text-sm text-red-300">{errors.root.message}</div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className={clsx(
                'group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
                isLoading
                  ? 'bg-blue-500 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-300">
              Default credentials: <code className="bg-gray-700 text-gray-200 px-1 rounded">admin</code> / <code className="bg-gray-700 text-gray-200 px-1 rounded">admin123</code>
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Please change the default password after first login
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

