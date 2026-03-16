import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { toast } from 'sonner'
import { Hexagon, Loader2 } from 'lucide-react'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const API_BASE = `http://${window.location.hostname}:6400`

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)
      
      const res = await axios.post(`${API_BASE}/admin/login`, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      
      localStorage.setItem('token', res.data.access_token)
      toast.success('Login successful')
      navigate('/')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900 px-4 sm:px-6 lg:px-8 relative overflow-hidden transition-colors duration-200">
      
      {/* Background decoration */}
      <div className="absolute top-0 -translate-y-12 translate-x-1/3 right-0 w-96 h-96 bg-blue-500/20 dark:bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-0 translate-y-1/3 -translate-x-1/3 left-0 w-96 h-96 bg-indigo-500/20 dark:bg-indigo-600/20 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md space-y-8 z-10">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-2xl shadow-lg flex items-center justify-center mb-6 transform rotate-3">
            <Hexagon size={36} className="text-white drop-shadow-md" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
            Gemini Unified Gateway
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Sign in to access the admin dashboard
          </p>
        </div>
        
        <form onSubmit={handleLogin} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl p-8 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 w-full transition-colors duration-200">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email Address</label>
              <input 
                type="email" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-3 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder-gray-400 dark:placeholder-gray-500" 
                placeholder="admin@local.host"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-3 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder-gray-400 dark:placeholder-gray-500" 
                placeholder="••••••••"
              />
            </div>
            
            <button 
              type="submit"
              disabled={isLoading}
              className={`w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center space-x-2 ${isLoading ? 'opacity-80 cursor-not-allowed' : 'transform hover:-translate-y-0.5'}`}
            >
              {isLoading ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login