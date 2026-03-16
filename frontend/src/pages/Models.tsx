import React, { useState, useEffect } from 'react'
import { Search, RefreshCw, Cpu, Brain, Zap, Loader2 } from 'lucide-react'
import axios from 'axios'
import { toast } from 'sonner'

const Models = () => {
  const [models, setModels] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterFamily, setFilterFamily] = useState('All')

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchModels = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/models/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setModels(res.data)
    } catch (err) {
      toast.error('Failed to load models')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRefreshModels = async () => {
    setIsRefreshing(true)
    const toastId = toast.loading('Refreshing models from providers...')
    try {
      await axios.post(`${API_BASE}/admin/models/refresh`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Models refreshed successfully', { id: toastId })
      await fetchModels()
    } catch (err) {
      toast.error('Failed to refresh models', { id: toastId })
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchModels()
  }, [])

  const filteredModels = models.filter((m: any) => {
    const matchesSearch = m.display_name.toLowerCase().includes(searchTerm.toLowerCase()) || m.provider_model_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFamily = filterFamily === 'All' || m.family.toLowerCase() === filterFamily.toLowerCase()
    return matchesSearch && matchesFamily
  })

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white tracking-tight">Model Registry</h1>
        <button 
          onClick={handleRefreshModels}
          disabled={isRefreshing}
          className="bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/40 px-4 py-2.5 rounded-xl flex items-center space-x-2 transition-colors disabled:opacity-50 font-medium text-sm w-full sm:w-auto justify-center"
        >
          {isRefreshing ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
          <span>Refresh Models</span>
        </button>
      </div>

      <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4 mb-6">
        <div className="flex-grow flex items-center space-x-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2.5 rounded-xl shadow-sm focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all">
          <Search size={18} className="text-gray-400 dark:text-gray-500" />
          <input 
            type="text" 
            placeholder="Search models by name or ID..." 
            className="w-full bg-transparent border-none focus:outline-none text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500" 
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <select 
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2.5 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer min-w-[150px]"
          value={filterFamily}
          onChange={e => setFilterFamily(e.target.value)}
        >
          <option value="All">All Families</option>
          <option value="gemini">Gemini</option>
          <option value="imagen">Imagen</option>
          <option value="veo">Veo</option>
          <option value="lyria">Lyria</option>
        </select>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
           <div className="p-16 flex justify-center"><Loader2 className="animate-spin text-blue-600 dark:text-blue-400" size={48} /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left whitespace-nowrap">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Display Name</th>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Provider Name</th>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Family</th>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Provider</th>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
                {filteredModels.map((model: any) => (
                  <tr key={model.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg ${model.family === 'gemini' ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'}`}>
                          {model.family === 'gemini' ? <Zap size={16} /> : <Brain size={16} />}
                        </div>
                        <span className="font-semibold text-gray-900 dark:text-gray-100">{model.display_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600 dark:text-gray-400 font-mono text-sm">{model.provider_model_name}</td>
                    <td className="px-6 py-4">
                      <span className="capitalize text-gray-700 dark:text-gray-300 font-medium">{model.family}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                        <Cpu size={14} />
                        <span className="capitalize">{model.source_provider}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${model.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}`}>
                        {model.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {filteredModels.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <Box size={32} className="text-gray-300 dark:text-gray-600" />
                        <p>No models found matching your criteria.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Models