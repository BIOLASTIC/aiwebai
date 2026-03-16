import React, { useState, useEffect } from 'react'
import { Plus, Trash2, Download, Loader2, CheckCircle2, AlertCircle, RotateCw, RefreshCw, Server, Monitor } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const AdminPanel = () => {
  const [isRestarting, setIsRestarting] = useState(false)
  const [restartStatus, setRestartStatus] = useState<{
    backend?: string
    frontend?: string
    admin?: string
    overall?: string
  }>({})

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  // Check system status
  const checkStatus = async () => {
    try {
      const responses = await Promise.allSettled([
        fetch(`${API_BASE}/health`, { method: 'GET' }),
        fetch(`${API_BASE}/docs`, { method: 'GET' }),
      ])

      const backendHealthy = responses[0].status === 'fulfilled' ? responses[0].status === 200 : false
      const apiDocsAccessible = responses[1].status === 'fulfilled' ? responses[1].status === 200 : false

      return {
        backend: backendHealthy ? 'healthy' : 'unhealthy',
        apiDocs: apiDocsAccessible ? 'healthy' : 'unhealthy',
      }
    } catch (error) {
      return {
        backend: 'unhealthy',
        apiDocs: 'unhealthy',
      }
    }
  }

  // Restart system
  const handleRestartSystem = async () => {
    if (!confirm('Are you sure you want to restart the entire system? This will temporarily disconnect all services.')) {
      return
    }

    setIsRestarting(true)
    setRestartStatus({})

    try {
      const response = await axios.post(`${API_BASE}/admin/restart`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })

      const data = response.data
      setRestartStatus({
        backend: data.backend.status === 'success' ? 'success' : data.backend.status === 'error' ? 'error' : 'pending',
        frontend: data.frontend.status === 'success' ? 'success' : data.frontend.status === 'error' ? 'error' : 'pending',
        admin: data.status === 'success' ? 'success' : 'error',
        overall: data.status === 'success' ? 'success' : 'error',
      })

      if (data.status === 'success') {
        toast.success('System restart initiated!', { duration: 5000 })
        // Wait and check status after restart
        setTimeout(async () => {
          const status = await checkStatus()
          setRestartStatus(prev => ({
            ...prev,
            backend: status.backend,
            frontend: 'restarting',
          }))

          // Final check after restart completes
          setTimeout(async () => {
            const finalStatus = await checkStatus()
            setRestartStatus({
              backend: finalStatus.backend,
              frontend: finalStatus.apiDocs,
              overall: finalStatus.backend === 'healthy' && finalStatus.apiDocs === 'healthy' ? 'success' : 'pending',
            })

            if (finalStatus.backend === 'healthy' && finalStatus.apiDocs === 'healthy') {
              toast.success('System is ready!', { duration: 5000 })
            }
          }, 10000)
        }, 3000)
      } else {
        toast.error('Failed to initiate system restart', { duration: 5000 })
      }
    } catch (error) {
      toast.error('Failed to restart system: ' + (error.response?.data?.detail || error.message), { duration: 5000 })
      setRestartStatus({ overall: 'error' })
    } finally {
      setIsRestarting(false)
    }
  }

  // Restart backend only
  const handleRestartBackend = async () => {
    if (!confirm('Are you sure you want to restart only the backend? The frontend will continue running.')) {
      return
    }

    setIsRestarting(true)

    try {
      const response = await axios.post(`${API_BASE}/admin/restart/backend`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (response.data.status === 'success') {
        toast.success('Backend restarting...', { duration: 3000 })
        setRestartStatus(prev => ({ ...prev, backend: 'restarting' }))

        setTimeout(async () => {
          const status = await checkStatus()
          setRestartStatus({
            backend: status.backend,
            overall: status.backend === 'healthy' ? 'success' : 'pending',
          })

          if (status.backend === 'healthy') {
            toast.success('Backend is ready!', { duration: 3000 })
          }
        }, 5000)
      } else {
        toast.error('Failed to restart backend')
      }
    } catch (error) {
      toast.error('Failed to restart backend')
    } finally {
      setIsRestarting(false)
    }
  }

  // Restart frontend only
  const handleRestartFrontend = async () => {
    if (!confirm('Are you sure you want to restart only the frontend? The backend will continue running.')) {
      return
    }

    setIsRestarting(true)

    try {
      const response = await axios.post(`${API_BASE}/admin/restart/frontend`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (response.data.status === 'success') {
        toast.success('Frontend restarting...', { duration: 3000 })
        setRestartStatus(prev => ({ ...prev, frontend: 'restarting' }))

        setTimeout(async () => {
          const status = await checkStatus()
          setRestartStatus({
            frontend: status.apiDocs,
            overall: status.backend === 'healthy' && status.apiDocs === 'healthy' ? 'success' : 'pending',
          })

          if (status.apiDocs === 'healthy') {
            toast.success('Frontend is ready!', { duration: 3000 })
          }
        }, 5000)
      } else {
        toast.error('Failed to restart frontend')
      }
    } catch (error) {
      toast.error('Failed to restart frontend')
    } finally {
      setIsRestarting(false)
    }
  }

  // Manual restart via script
  const handleManualRestart = async () => {
    if (!confirm('This will execute the development restart script directly. Continue?')) {
      return
    }

    setIsRestarting(true)
    try {
      const response = await axios.post(`${API_BASE}/admin/restart/manual`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (response.data.status === 'success') {
        toast.success('Manual restart executed!', { duration: 3000 })
        setRestartStatus(prev => ({ ...prev, overall: 'restarting' }))

        setTimeout(async () => {
          const status = await checkStatus()
          setRestartStatus({
            backend: status.backend,
            frontend: status.apiDocs,
            overall: status.backend === 'healthy' && status.apiDocs === 'healthy' ? 'success' : 'pending',
          })

          if (status.backend === 'healthy' && status.apiDocs === 'healthy') {
            toast.success('System is ready with manual restart!', { duration: 5000 })
          }
        }, 10000)
      } else {
        toast.error('Failed to execute manual restart')
      }
    } catch (error) {
      toast.error('Failed to execute manual restart: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsRestarting(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <RefreshCw className="text-green-500" size={18} />
      case 'error':
        return <AlertCircle className="text-red-500" size={18} />
      case 'restarting':
        return <Loader2 className="text-yellow-500 animate-spin" size={18} />
      case 'healthy':
        return <CheckCircle2 className="text-green-500" size={18} />
      default:
        return <Server className="text-gray-500" size={18} />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success':
        return 'Success'
      case 'error':
        return 'Failed'
      case 'restarting':
        return 'Restarting...'
      case 'healthy':
        return 'Healthy'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
          Admin Control
        </h1>

        <div className="flex flex-wrap items-center gap-3">
          {/* Status Indicators */}
          <div className="hidden sm:flex items-center space-x-2 bg-gray-100 dark:bg-gray-800 p-2 rounded-lg">
            <Server className="text-gray-500 dark:text-gray-400" size={16} />
            <span className="text-sm text-gray-600 dark:text-gray-300">
              Backend: {restartStatus.backend || 'Checking...'}
            </span>
          </div>

          <div className="hidden sm:flex items-center space-x-2 bg-gray-100 dark:bg-gray-800 p-2 rounded-lg">
            <Monitor className="text-gray-500 dark:text-gray-400" size={16} />
            <span className="text-sm text-gray-600 dark:text-gray-300">
              Frontend: {restartStatus.frontend || 'Checking...'}
            </span>
          </div>

          {/* Restart Buttons */}
          <button
            onClick={handleRestartBackend}
            disabled={isRestarting}
            className="bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-500/20 px-4 py-2.5 rounded-xl flex items-center space-x-2 transition disabled:opacity-50 font-medium text-sm"
          >
            {isRestarting ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
            <span>Restart Backend</span>
          </button>

          <button
            onClick={handleRestartFrontend}
            disabled={isRestarting}
            className="bg-purple-50 dark:bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800 hover:bg-purple-100 dark:hover:bg-purple-500/20 px-4 py-2.5 rounded-xl flex items-center space-x-2 transition disabled:opacity-50 font-medium text-sm"
          >
            {isRestarting ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
            <span>Restart Frontend</span>
          </button>

          <button
            onClick={handleRestartSystem}
            disabled={isRestarting}
            className="bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 hover:bg-red-100 dark:hover:bg-red-500/20 px-4 py-2.5 rounded-xl flex items-center space-x-2 transition disabled:opacity-50 font-medium text-sm shadow-sm hover:shadow"
          >
            {isRestarting ? <Loader2 size={18} className="animate-spin" /> : <RotateCw size={18} />}
            <span>Restart System</span>
          </button>

          <button
            onClick={handleManualRestart}
            disabled={isRestarting}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600 px-4 py-2.5 rounded-xl flex items-center space-x-2 transition disabled:opacity-50 font-medium text-sm"
          >
            {isRestarting ? <Loader2 size={18} className="animate-spin" /> : <RotateCw size={18} />}
            <span>Full Restart</span>
          </button>
        </div>
      </div>

      {/* Status Details */}
      {restartStatus.backend || restartStatus.frontend ? (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Restart Status</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Backend</span>
                {getStatusIcon(restartStatus.backend)}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {getStatusText(restartStatus.backend || 'Checking')}
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Frontend</span>
                {getStatusIcon(restartStatus.frontend)}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {getStatusText(restartStatus.frontend || 'Checking')}
              </p>
            </div>
          </div>

          {restartStatus.overall === 'success' && (
            <div className="bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-800 p-4 rounded-xl">
              <div className="flex items-center space-x-2">
                <CheckCircle2 size={20} className="text-green-500" />
                <span className="text-sm font-medium text-green-700 dark:text-green-400">
                  System restart completed successfully!
                </span>
              </div>
            </div>
          )}

          {restartStatus.overall === 'error' && (
            <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-800 p-4 rounded-xl">
              <div className="flex items-center space-x-2">
                <AlertCircle size={20} className="text-red-500" />
                <span className="text-sm font-medium text-red-700 dark:text-red-400">
                  System restart failed. Please check the logs.
                </span>
              </div>
            </div>
          )}

          {restartStatus.overall === 'restarting' && (
            <div className="bg-yellow-50 dark:bg-yellow-500/10 border border-yellow-200 dark:border-yellow-800 p-4 rounded-xl">
              <div className="flex items-center space-x-2">
                <Loader2 size={20} className="text-yellow-500 animate-spin" />
                <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                  System is restarting... This may take a few seconds.
                </span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="flex items-center space-x-3">
            <Server className="text-gray-400 dark:text-gray-500" size={24} />
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Click the buttons above to restart individual services or the entire system.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Info */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-xl">
        <h3 className="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-2">
          Restart Options:
        </h3>
        <ul className="text-xs text-blue-600 dark:text-blue-400 space-y-1">
          <li>• <strong>Restart Backend:</strong> Restarts only the API server (recommended for code changes)</li>
          <li>• <strong>Restart Frontend:</strong> Restarts only the web interface (recommended for UI changes)</li>
          <li>• <strong>Restart System:</strong> Restarts both services (recommended for configuration changes)</li>
          <li>• <strong>Full Restart:</strong> Executes the development restart script with proper cleanup</li>
        </ul>
      </div>
    </div>
  )
}

export default AdminPanel
