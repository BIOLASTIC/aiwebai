import React, { useState, useEffect } from 'react'
import { CheckCircle2, XCircle, AlertCircle, HelpCircle, Activity, LayoutGrid, Info } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const Features = () => {
  const [parityData, setParityData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchParity = async () => {
    setIsLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/admin/parity/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setParityData(res.data)
    } catch (err) {
      toast.error('Failed to fetch feature parity matrix')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchParity()
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle2 className="text-green-500" size={20} />
      case 'partial': return <AlertCircle className="text-amber-500" size={20} />
      case 'unsupported': return <XCircle className="text-gray-300 dark:text-gray-700" size={20} />
      case 'broken': return <XCircle className="text-red-500" size={20} />
      default: return <HelpCircle className="text-gray-400" size={20} />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return 'Working'
      case 'partial': return 'Partial'
      case 'unsupported': return 'N/A'
      case 'broken': return 'Broken'
      default: return 'Unknown'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <LayoutGrid className="mr-3 text-blue-600" />
            Feature Parity Matrix
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Real-time status of capabilities across different adapters
          </p>
        </div>
        
        <button 
          onClick={fetchParity}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-750 transition shadow-sm text-sm font-medium flex items-center"
        >
          <Activity size={16} className="mr-2 text-blue-500" />
          Test All Features
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-100 dark:border-gray-700">
                <th className="px-8 py-5 text-xs font-bold text-gray-500 uppercase tracking-wider">Feature Capability</th>
                <th className="px-8 py-5 text-xs font-bold text-gray-500 uppercase tracking-wider text-center">webapi Adapter</th>
                <th className="px-8 py-5 text-xs font-bold text-gray-500 uppercase tracking-wider text-center">mcp-cli Adapter</th>
                <th className="px-8 py-5 text-xs font-bold text-gray-500 uppercase tracking-wider">Notes & Fallback</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-700/50">
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={4} className="px-8 py-5 h-16 bg-gray-50/20"></td>
                  </tr>
                ))
              ) : (
                parityData.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50/50 dark:hover:bg-gray-750 transition-colors">
                    <td className="px-8 py-5">
                      <span className="font-bold text-gray-900 dark:text-white">{row.feature}</span>
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex flex-col items-center">
                        {getStatusIcon(row.webapi)}
                        <span className="text-[10px] mt-1 font-medium text-gray-500 uppercase">{getStatusText(row.webapi)}</span>
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex flex-col items-center">
                        {getStatusIcon(row.mcpcli)}
                        <span className="text-[10px] mt-1 font-medium text-gray-500 uppercase">{getStatusText(row.mcpcli)}</span>
                      </div>
                    </td>
                    <td className="px-8 py-5 text-sm text-gray-500 italic">
                      {row.notes}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/10 p-6 rounded-2xl border border-blue-100 dark:border-blue-900/20 flex items-start space-x-4">
        <Info className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" size={20} />
        <div className="text-sm text-blue-800 dark:text-blue-300">
          <p className="font-bold mb-1">How fallback works</p>
          <p>
            The gateway automatically routes requests based on this matrix. If a feature is only supported by one adapter, it will be used exclusively. If both support it, <strong>webapi</strong> is preferred for streaming efficiency, while <strong>mcp-cli</strong> is used for advanced generation tasks.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Features
