import React, { useState, useEffect } from 'react'
import { Box, RefreshCcw, ExternalLink, ShieldCheck, AlertCircle, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const Packages = () => {
  const [packages, setPackages] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchPackages = async () => {
    setIsLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/admin/packages/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setPackages(res.data)
    } catch (err) {
      toast.error('Failed to fetch package versions')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchPackages()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <Box className="mr-3 text-blue-600" />
            System Packages
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Monitor versions of upstream adapters and core dependencies
          </p>
        </div>
        
        <button 
          onClick={fetchPackages}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-2.5 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-750 transition shadow-sm"
        >
          <RefreshCcw size={20} className="text-blue-500" />
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-100 dark:border-gray-700">
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Package Name</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Installed Version</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-700/50">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={4} className="px-6 py-4 h-16 bg-gray-50/20"></td>
                  </tr>
                ))
              ) : (
                packages.map((pkg, i) => (
                  <tr key={i} className="hover:bg-gray-50/50 dark:hover:bg-gray-750 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400 mr-3">
                          <Box size={18} />
                        </div>
                        <span className="font-semibold text-gray-900 dark:text-white">{pkg.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-mono text-sm text-gray-600 dark:text-gray-400">
                      {pkg.version}
                    </td>
                    <td className="px-6 py-4">
                      {pkg.status === 'installed' ? (
                        <span className="px-2.5 py-1 rounded-lg bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs font-bold flex items-center w-fit">
                          <CheckCircle2 size={12} className="mr-1" />
                          Up to Date
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-lg bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 text-xs font-bold flex items-center w-fit">
                          <AlertCircle size={12} className="mr-1" />
                          {pkg.status}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <a 
                        href={`https://pypi.org/project/${pkg.name}/`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-gray-400 hover:text-blue-600 transition p-2 inline-block"
                      >
                        <ExternalLink size={18} />
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Packages
