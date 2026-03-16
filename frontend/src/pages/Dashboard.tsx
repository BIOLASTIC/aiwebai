import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { Activity, Database, Users, TrendingUp, Clock, AlertCircle, Loader2, RefreshCw } from 'lucide-react'
import axios from 'axios'
import { toast } from 'sonner'
import { useTheme } from '../components/ThemeProvider'

const Dashboard = () => {
  const [summary, setSummary] = useState(null)
  const [recent, setRecent] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const { theme } = useTheme()

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchDashboardData = async (showLoading = false) => {
    if (showLoading) setIsRefreshing(true)
    try {
      const [summaryRes, recentRes] = await Promise.all([
        axios.get(`${API_BASE}/admin/analytics/summary`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_BASE}/admin/analytics/recent`, { headers: { Authorization: `Bearer ${token}` } })
      ])
      
      setSummary(summaryRes.data)
      setRecent(recentRes.data)
    } catch (err) {
      toast.error('Failed to load dashboard data')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(() => fetchDashboardData(false), 10000)
    return () => clearInterval(interval)
  }, [])

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full min-h-[60vh]">
        <Loader2 className="animate-spin text-blue-600 dark:text-blue-400" size={48} />
      </div>
    )
  }

  const defaultVolume = [{ date: new Date().toISOString().split('T')[0], count: 0 }]
  const volumeData = summary?.volume?.length > 0 ? summary.volume : defaultVolume
  const chartData = volumeData.map((v: any) => ({ name: v.date, requests: v.count, latency: summary?.latency?.avg || 0 }))

  const stats = [
    { label: 'Total Requests', value: summary?.total_requests || 0, icon: <TrendingUp size={24} />, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30' },
    { label: 'Avg Latency', value: `${(summary?.latency?.avg || 0).toFixed(0)}ms`, icon: <Clock size={24} />, color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/30' },
    { label: 'Error Rate', value: `${(summary?.error_rate || 0).toFixed(2)}%`, icon: <AlertCircle size={24} />, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30' },
  ]

  const chartAxisColor = theme === 'dark' ? '#9CA3AF' : '#4B5563'
  const chartGridColor = theme === 'dark' ? '#374151' : '#E5E7EB'

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white tracking-tight">Overview Dashboard</h1>
        <button 
          onClick={() => fetchDashboardData(true)} 
          disabled={isRefreshing}
          className="flex items-center space-x-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg shadow-sm transition-all disabled:opacity-50"
        >
          <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
          <span>Refresh</span>
        </button>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-4">
              <div className={`p-4 ${stat.bg} ${stat.color} rounded-xl`}>
                {stat.icon}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
        <div className="bg-white dark:bg-gray-800 p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
          <h2 className="text-lg font-bold mb-6 text-gray-800 dark:text-gray-200">Request Volume</h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={chartGridColor} />
                <XAxis dataKey="name" stroke={chartAxisColor} fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke={chartAxisColor} fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{ fill: theme === 'dark' ? '#374151' : '#F3F4F6' }}
                  contentStyle={{ backgroundColor: theme === 'dark' ? '#1F2937' : '#FFFFFF', borderColor: theme === 'dark' ? '#374151' : '#E5E7EB', borderRadius: '8px', color: theme === 'dark' ? '#F9FAFB' : '#111827' }}
                />
                <Bar dataKey="requests" fill="#3B82F6" radius={[4, 4, 0, 0]} maxBarSize={50} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
          <h2 className="text-lg font-bold mb-6 text-gray-800 dark:text-gray-200">Latency Distribution</h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={chartGridColor} />
                <XAxis dataKey="name" stroke={chartAxisColor} fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke={chartAxisColor} fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: theme === 'dark' ? '#1F2937' : '#FFFFFF', borderColor: theme === 'dark' ? '#374151' : '#E5E7EB', borderRadius: '8px', color: theme === 'dark' ? '#F9FAFB' : '#111827' }}
                />
                <Line type="monotone" dataKey="latency" stroke="#10B981" strokeWidth={3} dot={{ r: 4, fill: '#10B981', strokeWidth: 2, stroke: theme === 'dark' ? '#1F2937' : '#FFFFFF' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-bold mb-4 text-gray-800 dark:text-gray-200">Real-time Request Stream</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left whitespace-nowrap">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider rounded-tl-lg">Timestamp</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Endpoint</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Model</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider rounded-tr-lg">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50 text-sm">
              {recent.map((req: any, idx) => (
                <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <td className="px-6 py-4 text-gray-500 dark:text-gray-400">{new Date(req.timestamp).toLocaleString()}</td>
                  <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-200">{req.endpoint}</td>
                  <td className="px-6 py-4 text-gray-600 dark:text-gray-300">
                    <span className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded font-mono text-xs">{req.model || 'N/A'}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${req.status_code >= 400 ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400' : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400'}`}>
                      {req.status_code}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500 dark:text-gray-400">{req.latency}ms</td>
                </tr>
              ))}
              {recent.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <Activity size={32} className="text-gray-300 dark:text-gray-600" />
                      <p>No recent requests recorded in the system.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard