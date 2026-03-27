import React, { useState, useEffect } from 'react'
import { Search, Filter, History, ChevronLeft, ChevronRight, Activity, Clock, Terminal, AlertTriangle, CheckCircle, XCircle, ExternalLink, Eye, Download } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'
import { format } from 'date-fns'
import { toZonedTime } from 'date-fns-tz'

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
  request_body?: string
  response_body?: string
  request_headers?: string
  method?: string
}

const Logs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [isLoading, setIsLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)
  const [showModal, setShowModal] = useState(false)

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

  const getStatusIcon = (code?: number) => {
    if (!code) return <Clock size={14} />
    if (code >= 200 && code < 300) return <CheckCircle size={14} className="text-green-600" />
    if (code >= 400 && code < 500) return <AlertTriangle size={14} className="text-amber-600" />
    if (code >= 500) return <XCircle size={14} className="text-red-600" />
    return <Clock size={14} />
  }

  const formatKolkataTime = (utcDate: string) => {
    try {
      const date = new Date(utcDate)
      const kolkataDate = toZonedTime(date, 'Asia/Kolkata')
      return format(kolkataDate, 'yyyy-MM-dd HH:mm:ss')
    } catch {
      return utcDate
    }
  }

  const getImageUrl = (log: LogEntry): string | null => {
    // Check response body for image URLs
    if (log.response_body) {
      try {
        const response = JSON.parse(log.response_body)
        if (response.data?.[0]?.url) {
          return response.data[0].url
        }
        if (response.result_url) {
          return response.result_url
        }
      } catch {
        // Try to find URL in raw response
        const urlMatch = log.response_body.match(/https?:\/\/[^\s"']+\.(png|jpg|jpeg|gif|webp)/i)
        if (urlMatch) {
          return urlMatch[0]
        }
      }
    }
    return null
  }

  const getErrorMessage = (log: LogEntry): string | null => {
    if (log.status_code && log.status_code >= 400) {
      if (log.response_body) {
        try {
          const response = JSON.parse(log.response_body)
          return response.detail || response.error || response.message || null
        } catch {
          return log.response_body.substring(0, 500)
        }
      }
    }
    return null
  }

  const openImage = (url: string) => {
    if (url.startsWith('http')) {
      window.open(url, '_blank')
    } else {
      window.open(`${API_BASE}${url}`, '_blank')
    }
  }

  const renderJson = (str: string | undefined) => {
    if (!str) return <span className="text-gray-400 italic">N/A</span>
    try {
      const parsed = JSON.parse(str)
      return (
        <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded-lg overflow-x-auto max-h-60">
          {JSON.stringify(parsed, null, 2)}
        </pre>
      )
    } catch {
      return (
        <pre className="text-xs bg-gray-900 text-yellow-400 p-3 rounded-lg overflow-x-auto max-h-60 whitespace-pre-wrap">
          {str}
        </pre>
      )
    }
  }

  return (
    <div className="space-y-6">
      {/* Modal for log details */}
      {showModal && selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Request Details - #{selectedLog.id}
              </h2>
              <button 
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <XCircle size={20} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)] space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">Status</div>
                  <div className={`flex items-center font-bold ${getStatusColor(selectedLog.status_code)}`}>
                    {getStatusIcon(selectedLog.status_code)}
                    <span className="ml-2">{selectedLog.status_code || 'N/A'}</span>
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">Method</div>
                  <div className="font-bold text-gray-900 dark:text-white">{selectedLog.method || 'N/A'}</div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">Response Time</div>
                  <div className="font-bold text-gray-900 dark:text-white">{selectedLog.latency_ms ? `${selectedLog.latency_ms}ms` : 'N/A'}</div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">Model</div>
                  <div className="font-bold text-gray-900 dark:text-white truncate">{selectedLog.model_alias || 'N/A'}</div>
                </div>
              </div>

              {/* Time */}
              <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-xl">
                <div className="text-xs text-gray-500 mb-1">Time (Asia/Kolkata)</div>
                <div className="font-bold text-gray-900 dark:text-white">{formatKolkataTime(selectedLog.created_at)}</div>
              </div>

              {/* Endpoint */}
              <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-xl">
                <div className="text-xs text-gray-500 mb-1">Endpoint</div>
                <div className="font-mono text-sm text-gray-900 dark:text-white">{selectedLog.endpoint}</div>
              </div>

              {/* Error Message */}
              {getErrorMessage(selectedLog) && (
                <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-xl border border-red-200 dark:border-red-800">
                  <div className="text-xs text-red-600 dark:text-red-400 mb-1 font-semibold">Error</div>
                  <div className="text-sm text-red-800 dark:text-red-300">{getErrorMessage(selectedLog)}</div>
                </div>
              )}

              {/* Image/Files */}
              {getImageUrl(selectedLog) && (
                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-xl border border-green-200 dark:border-green-800">
                  <div className="text-xs text-green-600 dark:text-green-400 mb-2 font-semibold">Generated Image/File</div>
                  <div className="flex items-center gap-3">
                    <img 
                      src={getImageUrl(selectedLog)?.startsWith('http') ? getImageUrl(selectedLog) : `${API_BASE}${getImageUrl(selectedLog)}`} 
                      alt="Generated"
                      className="max-w-xs max-h-40 rounded-lg border border-gray-200"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none'
                      }}
                    />
                    <button
                      onClick={() => openImage(getImageUrl(selectedLog)!)}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      <ExternalLink size={16} />
                      Open Image
                    </button>
                  </div>
                </div>
              )}

              {/* Request Headers */}
              <div>
                <div className="text-xs text-gray-500 mb-2 font-semibold">Request Headers</div>
                {renderJson(selectedLog.request_headers)}
              </div>

              {/* Request Body */}
              <div>
                <div className="text-xs text-gray-500 mb-2 font-semibold">Request Body</div>
                {renderJson(selectedLog.request_body)}
              </div>

              {/* Response Body */}
              <div>
                <div className="text-xs text-gray-500 mb-2 font-semibold">Response Body</div>
                {selectedLog.response_body ? (
                  renderJson(selectedLog.response_body)
                ) : (
                  <div className="text-xs text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                    <p className="font-semibold mb-1">⚠️ Response body not captured</p>
                    <p>FastAPI streams responses directly to client. Response body is only captured for error responses (4xx, 5xx) or when explicitly stored by the endpoint.</p>
                    <p className="mt-1 text-xs opacity-75">This is a technical limitation - streaming responses (like /v1/chat/completions) don't store body in memory.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <History className="mr-3 text-blue-600" />
            Request Logs
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Monitor API traffic with full request/response details
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
              <option value="201">201 Created</option>
              <option value="400">400 Bad Request</option>
              <option value="401">401 Unauthorized</option>
              <option value="422">422 Unprocessable</option>
              <option value="500">500 Server Error</option>
              <option value="502">502 Bad Gateway</option>
              <option value="503">503 Service Unavailable</option>
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
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Time (IST)</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Endpoint</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Method</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Response Time</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Model</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-700/50 text-sm">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={7} className="px-4 py-4 h-14 bg-gray-50/20 dark:bg-gray-900/10"></td>
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-500 italic">
                    No logs found matching criteria
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-750 transition-colors group">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        <Clock size={14} className="mr-2 text-gray-400" />
                        <span className="text-gray-900 dark:text-gray-200 font-mono text-xs">
                          {formatKolkataTime(log.created_at).split(' ')[1]}
                        </span>
                        <span className="ml-2 text-xs text-gray-400">
                          {formatKolkataTime(log.created_at).split(' ')[0]}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center font-mono text-xs">
                        <Terminal size={14} className="mr-2 text-blue-400" />
                        <span className="text-gray-900 dark:text-gray-200 truncate max-w-[200px]">{log.endpoint}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-md text-xs font-bold ${
                        log.method === 'POST' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                        log.method === 'GET' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                        log.method === 'PUT' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                        log.method === 'DELETE' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {log.method || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-lg font-bold text-xs flex items-center w-fit ${getStatusColor(log.status_code)}`}>
                        {getStatusIcon(log.status_code)}
                        <span className="ml-1">{log.status_code || '---'}</span>
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`font-mono text-xs ${
                        (log.latency_ms || 0) > 5000 ? 'text-red-600' :
                        (log.latency_ms || 0) > 2000 ? 'text-amber-600' :
                        'text-gray-600 dark:text-gray-400'
                      }`}>
                        {log.latency_ms ? `${log.latency_ms}ms` : '---'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-gray-900 dark:text-gray-200 truncate max-w-[120px] text-xs">
                        {log.model_alias || '---'}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => {
                          setSelectedLog(log)
                          setShowModal(true)
                        }}
                        className="flex items-center gap-1 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition text-xs font-medium"
                      >
                        <Eye size={14} />
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-700 bg-gray-50/30 dark:bg-gray-900/30 flex items-center justify-between">
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
