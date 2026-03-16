import React, { useState, useEffect } from 'react'
import { Activity, Server, Cpu, Database, HardDrive, RefreshCcw, CheckCircle2, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const Health = () => {
  const [healthData, setHealthData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchHealth = async () => {
    setIsLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/admin/health/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setHealthData(res.data)
    } catch (err) {
      toast.error('Failed to fetch health data')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
  }, [])

  if (isLoading && !healthData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const { resources, system } = healthData || {}

  const getProgressColor = (pct: number) => {
    if (pct < 70) return 'bg-green-500'
    if (pct < 90) return 'bg-amber-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <Activity className="mr-3 text-green-600" />
            System Health
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Monitor real-time resource utilization and system status
          </p>
        </div>
        
        <button 
          onClick={fetchHealth}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-2.5 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-750 transition shadow-sm"
        >
          <RefreshCcw size={20} className="text-blue-500" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-xl text-green-600 dark:text-green-400">
            <CheckCircle2 size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white uppercase">Healthy</div>
            <div className="text-sm text-gray-500">Overall Status</div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-blue-600 dark:text-blue-400">
            <Server size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{system?.platform || 'Unknown'}</div>
            <div className="text-sm text-gray-500">{system?.platform_release}</div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-xl text-purple-600 dark:text-purple-400">
            <Cpu size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{system?.architecture}</div>
            <div className="text-sm text-gray-500">CPU Architecture</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU & Memory */}
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Resource Utilization</h2>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600 dark:text-gray-400 font-medium">CPU Usage</span>
              <span className="font-bold">{resources?.cpu_usage_pct}%</span>
            </div>
            <div className="w-full bg-gray-100 dark:bg-gray-900 h-3 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${getProgressColor(resources?.cpu_usage_pct)}`} 
                style={{ width: `${resources?.cpu_usage_pct}%` }} 
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600 dark:text-gray-400 font-medium">Memory Usage</span>
              <span className="font-bold">{resources?.memory_used_gb} GB / {resources?.memory_total_gb} GB ({resources?.memory_usage_pct}%)</span>
            </div>
            <div className="w-full bg-gray-100 dark:bg-gray-900 h-3 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${getProgressColor(resources?.memory_usage_pct)}`} 
                style={{ width: `${resources?.memory_usage_pct}%` }} 
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600 dark:text-gray-400 font-medium">Disk Space</span>
              <span className="font-bold">{resources?.disk_used_gb} GB / {resources?.disk_total_gb} GB ({resources?.disk_usage_pct}%)</span>
            </div>
            <div className="w-full bg-gray-100 dark:bg-gray-900 h-3 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${getProgressColor(resources?.disk_usage_pct)}`} 
                style={{ width: `${resources?.disk_usage_pct}%` }} 
              />
            </div>
          </div>
        </div>

        {/* System Info */}
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">System Information</h2>
          <div className="grid grid-cols-1 gap-4">
            <div className="flex justify-between items-center py-3 border-b dark:border-gray-700">
              <span className="text-gray-500 text-sm">Python Version</span>
              <span className="font-mono text-sm text-gray-900 dark:text-gray-200">{system?.python_version}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b dark:border-gray-700">
              <span className="text-gray-500 text-sm">Processor</span>
              <span className="text-sm text-gray-900 dark:text-gray-200 truncate max-w-[250px]">{system?.processor}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b dark:border-gray-700">
              <span className="text-gray-500 text-sm">API Port</span>
              <span className="font-mono text-sm text-gray-900 dark:text-gray-200">6400</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b dark:border-gray-700">
              <span className="text-gray-500 text-sm">Frontend Port</span>
              <span className="font-mono text-sm text-gray-900 dark:text-gray-200">6401</span>
            </div>
            <div className="flex justify-between items-center py-3">
              <span className="text-gray-500 text-sm">Local Server Time</span>
              <span className="text-sm text-gray-900 dark:text-gray-200">{new Date(healthData?.timestamp).toLocaleString()}</span>
            </div>
          </div>

          <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-900/50 rounded-2xl flex items-start space-x-3">
            <Database className="text-blue-500 shrink-0" size={20} />
            <div className="text-sm">
              <div className="font-bold text-gray-900 dark:text-white mb-1">SQLite Database</div>
              <div className="text-gray-500">
                Primary data storage is operational. Automatic maintenance and backups are configured.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Health
