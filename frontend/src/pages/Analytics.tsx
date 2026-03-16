import React, { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell,
} from 'recharts'
import { TrendingUp, Clock, AlertTriangle, Zap, Activity, Calendar, RefreshCcw } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']
const API_BASE = `http://${window.location.hostname}:6400`

const StatCard = ({ icon: Icon, color, value, label }: any) => (
  <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
    <div className={`inline-flex p-2.5 rounded-xl mb-4 ${color}`}><Icon size={22} /></div>
    <div className="text-3xl font-bold text-gray-900 dark:text-white">{value}</div>
    <div className="text-sm text-gray-500 mt-1">{label}</div>
  </div>
)

const EmptyChart = ({ label }: { label: string }) => (
  <div className="flex flex-col items-center justify-center h-48 text-gray-400 dark:text-gray-500 text-sm space-y-2">
    <Activity size={32} className="opacity-30" />
    <p>No {label} data yet</p>
    <p className="text-xs">Data appears after API requests are made</p>
  </div>
)

const Analytics = () => {
  const [summary, setSummary] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const token = localStorage.getItem('token')

  const fetchAnalytics = async () => {
    setIsLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/admin/analytics/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setSummary(res.data)
    } catch {
      toast.error('Failed to fetch analytics')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => { fetchAnalytics() }, [])

  const volumeData: any[] = summary?.volume ?? []
  const latency = summary?.latency ?? { avg: 0, min: 0, max: 0 }
  const errorRate: number = summary?.error_rate ?? 0
  const total: number = summary?.total_requests ?? 0
  const endpoints: any[] = summary?.endpoints ?? []
  const statuses: any[] = summary?.statuses ?? []

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <TrendingUp className="text-blue-600" size={28} /> Analytics
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1 text-sm">System performance and usage trends</p>
        </div>
        <button onClick={fetchAnalytics} disabled={isLoading}
          className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2.5 rounded-xl text-sm hover:bg-gray-50 transition shadow-sm disabled:opacity-50">
          <RefreshCcw size={16} className={`text-blue-500 ${isLoading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Activity} color="bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400" value={total.toLocaleString()} label="Total Requests" />
        <StatCard icon={Clock} color="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400" value={`${Math.round(latency.avg)}ms`} label="Avg Latency" />
        <StatCard icon={AlertTriangle} color="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400" value={`${errorRate}%`} label="Error Rate" />
        <StatCard icon={Zap} color="bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400" value={latency.max ? `${latency.max}ms` : '—'} label="Max Latency" />
      </div>

      {/* Volume chart */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
        <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-5">
          <Calendar size={17} className="text-blue-500" /> Request Volume (last 7 days)
        </h3>
        {volumeData.length === 0 ? <EmptyChart label="volume" /> : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={volumeData}>
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.12} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 11 }} dy={8} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }} />
                <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2.5} fill="url(#grad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Endpoint breakdown */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <h3 className="text-base font-bold text-gray-900 dark:text-white mb-5">Top Endpoints</h3>
          {endpoints.length === 0 ? <EmptyChart label="endpoint" /> : (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={endpoints} layout="vertical" margin={{ left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <YAxis type="category" dataKey="endpoint" width={150} axisLine={false} tickLine={false} tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Status breakdown */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <h3 className="text-base font-bold text-gray-900 dark:text-white mb-5">Response Codes</h3>
          {statuses.length === 0 ? <EmptyChart label="status" /> : (
            <div className="flex items-center gap-6 h-56">
              <div className="flex-1 h-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={statuses} dataKey="count" nameKey="status_code" cx="50%" cy="50%" outerRadius={80} innerRadius={46}>
                      {statuses.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: 12, border: 'none' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2">
                {statuses.map((s: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
                    <span className="font-medium text-gray-700 dark:text-gray-300">{s.status_code}</span>
                    <span className="text-gray-400">({s.count})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Latency detail */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
        <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-5">
          <Clock size={17} className="text-green-500" /> Latency Stats
        </h3>
        <div className="grid grid-cols-3 gap-6">
          {[
            { label: 'Min', value: latency.min, color: 'bg-green-500' },
            { label: 'Avg', value: Math.round(latency.avg), color: 'bg-blue-500' },
            { label: 'Max', value: latency.max, color: 'bg-red-500' },
          ].map(({ label, value, color }) => (
            <div key={label}>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-gray-500">{label}</span>
                <span className="font-bold text-gray-900 dark:text-white">{value}ms</span>
              </div>
              <div className="w-full bg-gray-100 dark:bg-gray-700 h-2 rounded-full">
                <div className={`${color} h-2 rounded-full`} style={{ width: value ? `${Math.min(100, (value / (latency.max || 1)) * 100)}%` : '0%' }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Analytics
