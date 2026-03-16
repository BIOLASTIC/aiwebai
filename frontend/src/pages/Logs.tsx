import React, { useState, useEffect } from 'react'
import { Search, Filter, History, ChevronLeft, ChevronRight, Activity, Clock, Terminal } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'
import { format } from 'date-fns'

interface LogEntry {
  id: number
  user_id?: number
  account_id?: number
  provider?: string
  endpoint?: string
  model_alias?: string
  resolved_model?: string
  feature_type?: string
  stream_mode?: boolean
  latency_ms?: number
  status_code?: number
  retry_count?: number
  created_at: string
}

const Logs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [isLoading, setIsLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<string>('all')

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchLogs = async () => {
    setIsLoading(true)
    try {
      let url = `${API_BASE}/admin/logs/?page=${page}&page_size=${pageSize}`
      if (filterStatus !== 'all') {
        url += `&status_code=${filterStatus}`
      }
      
      const res = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setLogs(res.data.items)
      setTotal(res.data.total)
    } catch (err) {
      toast.error('Failed to fetch logs')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [page, filterStatus])

  const getStatusColor = (code?: number) => {
    if (!code) return 'text-gray-500'
    if (code >= 200 && code < 300) return 'text-green-600 bg-green-50 dark:bg-green-900/20'
    if (code >= 400 && code < 500) return 'text-amber-600 bg-amber-50 dark:bg-amber-900/20'
    if (code >= 500) return 'text-red-600 bg-red-50 dark:bg-red-900/20'
    return 'text-gray-600'
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <History className="mr-3 text-blue-600" />
            Request Logs
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Monitor API traffic and troubleshoot issues
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <select 
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value)
                setPage(1)
              }}
              className="pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 transition shadow-sm outline-none"
            >
              <option value="all">All Status</option>
              <option value="200">200 OK</option>
              <option value="400">400 Bad Request</option>
              <option value="401">401 Unauthorized</option>
              <option value="500">500 Server Error</option>
            </select>
          </div>
          
          <button 
            onClick={fetchLogs}
            className="p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-750 transition shadow-sm"
          >
            <Activity size={20} className="text-blue-500" />
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/50 dark:bg-gray-900/50 border-b border-gray-100 dark:border-gray-700">
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Time</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Endpoint</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Latency</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Model</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Provider</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-700/50 text-sm">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={6} className="px-6 py-4 h-12 bg-gray-50/20 dark:bg-gray-900/10"></td>
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500 italic">
                    No logs found matching criteria
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-750 transition-colors group">
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                      <div className="flex items-center">
                        <Clock size={14} className="mr-2 text-gray-400" />
                        {format(new Date(log.created_at), 'HH:mm:ss')}
                        <span className="ml-2 text-xs opacity-60">
                          {format(new Date(log.created_at), 'MMM d')}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center font-mono text-xs">
                        <Terminal size={14} className="mr-2 text-blue-400" />
                        <span className="text-gray-900 dark:text-gray-200">{log.endpoint}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-1 rounded-lg font-bold text-xs ${getStatusColor(log.status_code)}`}>
                        {log.status_code || '---'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400 font-mono text-xs">
                      {log.latency_ms ? `${log.latency_ms}ms` : '---'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-gray-900 dark:text-gray-200 truncate max-w-[150px]">
                        {log.model_alias || '---'}
                      </div>
                      <div className="text-[10px] text-gray-400 truncate max-w-[150px]">
                        {log.resolved_model}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs font-medium">
                        {log.provider || '---'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-700 bg-gray-50/30 dark:bg-gray-900/30 flex items-center justify-between">
          <div className="text-xs text-gray-500">
            Showing {Math.min(pageSize, logs.length)} of {total} results
          </div>
          
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-white dark:hover:bg-gray-800 transition"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-sm font-medium px-2">Page {page} of {Math.ceil(total / pageSize) || 1}</span>
            <button 
              onClick={() => setPage(Math.min(Math.ceil(total / pageSize), page + 1))}
              disabled={page >= Math.ceil(total / pageSize)}
              className="p-1.5 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-white dark:hover:bg-gray-800 transition"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Logs
