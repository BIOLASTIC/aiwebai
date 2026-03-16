import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, ArrowLeft, Send, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const ForgotPassword = () => {
  const [email, setEmail] = useState('')
  const [isSent, setIsSent] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const API_BASE = `http://${window.location.hostname}:6400`

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await axios.post(`${API_BASE}/admin/password/reset`, { email })
      setIsSent(true)
      toast.success('Password reset link sent to your email')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to send reset link')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-gray-900 py-10 px-6 shadow-xl rounded-3xl sm:px-12 border border-gray-100 dark:border-gray-800">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">Forgot Password?</h1>
            <p className="mt-3 text-gray-500 dark:text-gray-400 text-sm">
              Enter your email and we'll send you a link to reset your password.
            </p>
          </div>

          {!isSent ? (
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 ml-1">Email address</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none group-focus-within:text-blue-500 transition-colors">
                    <Mail size={20} className="text-gray-400" />
                  </div>
                  <input
                    type="email"
                    required
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-gray-950 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-sm text-gray-900 dark:text-gray-200"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full flex justify-center items-center py-3.5 px-4 rounded-2xl shadow-lg text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
                >
                  {isLoading ? 'Sending Link...' : 'Send Reset Link'}
                  {!isLoading && <Send size={18} className="ml-2" />}
                </button>
              </div>
            </form>
          ) : (
            <div className="text-center py-6 space-y-6">
              <div className="inline-flex items-center justify-center p-4 bg-green-50 dark:bg-green-900/20 rounded-full text-green-600 dark:text-green-400">
                <CheckCircle2 size={48} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Check your email</h3>
                <p className="mt-2 text-gray-500 dark:text-gray-400">
                  We have sent a password reset link to <span className="font-semibold">{email}</span>.
                </p>
              </div>
              <button 
                onClick={() => setIsSent(false)}
                className="text-blue-600 dark:text-blue-400 font-medium hover:underline flex items-center justify-center mx-auto"
              >
                <RefreshCw size={16} className="mr-2" />
                Didn't receive it? Try again
              </button>
            </div>
          )}

          <div className="mt-10 pt-6 border-t border-gray-100 dark:border-gray-800">
            <Link 
              to="/login" 
              className="flex items-center justify-center text-sm font-bold text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition"
            >
              <ArrowLeft size={16} className="mr-2" />
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ForgotPassword
