import React, { useState, useEffect } from 'react'
import { Plus, Trash2, Download, Loader2, CheckCircle2, AlertCircle, Key, Globe, LayoutGrid, List as ListIcon, X, Pencil, Check, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const API_BASE = `http://${window.location.hostname}:6400`

const Accounts = () => {
  const [accounts, setAccounts] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isAdding, setIsAdding] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [isSyncingGemcli, setIsSyncingGemcli] = useState(false)
  const [gemcliStatus, setGemcliStatus] = useState<{ logged_in: boolean; email: string | null } | null>(null)
  const [newAccount, setNewAccount] = useState({ label: '', provider: 'webapi', credentials: '' })
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list')
  // inline rename state: { [id]: editingLabel }
  const [renameState, setRenameState] = useState<Record<number, string | undefined>>({})
  const [validateErrors, setValidateErrors] = useState<Record<number, string>>({})

  const token = localStorage.getItem('token')
  const headers = { Authorization: `Bearer ${token}` }

  const fetchAccounts = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/accounts/`, { headers })
      setAccounts(res.data)
    } catch (err) {
      toast.error('Failed to fetch accounts')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchGemcliStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/accounts/gemcli-status`, { headers })
      setGemcliStatus(res.data)
    } catch { /* silent */ }
  }

  const handleSyncGemcli = async () => {
    setIsSyncingGemcli(true)
    try {
      const res = await axios.post(`${API_BASE}/admin/accounts/import/gemcli`, {}, { headers })
      toast.success(`Synced gemcli account: ${res.data.email || res.data.label}`)
      fetchAccounts()
      fetchGemcliStatus()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to sync gemcli account')
    } finally {
      setIsSyncingGemcli(false)
    }
  }

  useEffect(() => { fetchAccounts(); fetchGemcliStatus() }, [])

  const handleAddAccount = async () => {
    if (!newAccount.label || !newAccount.credentials) {
      toast.error('Please fill in all fields')
      return
    }
    setIsLoading(true)
    try {
      await axios.post(`${API_BASE}/admin/accounts/`, {
        label: newAccount.label,
        provider: newAccount.provider,
        auth_methods: [{
          auth_type: newAccount.provider === 'webapi' ? 'cookie' : 'apikey',
          credentials: newAccount.credentials,
        }],
      }, { headers })
      toast.success('Account added successfully')
      setIsAdding(false)
      setNewAccount({ label: '', provider: 'webapi', credentials: '' })
      fetchAccounts()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to add account')
    } finally {
      setIsLoading(false)
    }
  }

  const handleImportBrowser = async (browser: string) => {
    setIsImporting(true)
    try {
      await axios.post(`${API_BASE}/admin/accounts/import/browser?browser=${browser}`, {}, { headers })
      toast.success(`Imported from ${browser} successfully`)
      fetchAccounts()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || `Failed to import from ${browser}`)
    } finally {
      setIsImporting(false)
    }
  }

  const handleValidate = async (id: number) => {
    const toastId = toast.loading('Validating account...')
    try {
      const res = await axios.post(`${API_BASE}/admin/accounts/${id}/validate`, {}, { headers })
      if (res.data.status === 'valid') {
        toast.success('Account is healthy', { id: toastId })
        setValidateErrors(e => { const n = { ...e }; delete n[id]; return n })
      } else {
        const errMsg = res.data.error || 'Credentials rejected by Gemini'
        toast.error('Account unhealthy', { id: toastId })
        setValidateErrors(e => ({ ...e, [id]: errMsg }))
      }
      fetchAccounts()
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Validation request failed'
      toast.error(msg, { id: toastId })
      setValidateErrors(e => ({ ...e, [id]: msg }))
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this account?')) return
    try {
      await axios.delete(`${API_BASE}/admin/accounts/${id}`, { headers })
      toast.success('Account deleted')
      fetchAccounts()
    } catch {
      toast.error('Delete failed')
    }
  }

  const startRename = (id: number, currentLabel: string) =>
    setRenameState(s => ({ ...s, [id]: currentLabel }))

  const cancelRename = (id: number) =>
    setRenameState(s => { const n = { ...s }; delete n[id]; return n })

  const saveRename = async (id: number) => {
    const newLabel = renameState[id]?.trim()
    if (!newLabel) return
    try {
      await axios.patch(`${API_BASE}/admin/accounts/${id}`, { label: newLabel }, { headers })
      toast.success('Renamed successfully')
      cancelRename(id)
      fetchAccounts()
    } catch {
      toast.error('Rename failed')
    }
  }

  const healthBadge = (h: string) => {
    if (h === 'healthy') return <><CheckCircle2 size={16} className="text-green-500" /><span className="text-green-600 dark:text-green-400 font-medium">Healthy</span></>
    if (h === 'unhealthy') return <><AlertCircle size={16} className="text-red-500" /><span className="text-red-600 dark:text-red-400 font-medium">Unhealthy</span></>
    return <><AlertCircle size={16} className="text-yellow-500" /><span className="text-yellow-600 dark:text-yellow-400 font-medium">Unknown</span></>
  }

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white tracking-tight">Accounts</h1>

        <div className="flex flex-wrap items-center gap-2">
          <div className="hidden sm:flex bg-gray-100 dark:bg-gray-800 p-1 rounded-lg mr-2">
            <button onClick={() => setViewMode('list')} className={`p-1.5 rounded-md ${viewMode === 'list' ? 'bg-white dark:bg-gray-700 shadow-sm text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}><ListIcon size={18} /></button>
            <button onClick={() => setViewMode('grid')} className={`p-1.5 rounded-md ${viewMode === 'grid' ? 'bg-white dark:bg-gray-700 shadow-sm text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}><LayoutGrid size={18} /></button>
          </div>

          {gemcliStatus?.logged_in && (
            <button onClick={handleSyncGemcli} disabled={isSyncingGemcli}
              title={`Sync gemcli account: ${gemcliStatus.email}`}
              className="bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-500/20 px-4 py-2.5 rounded-xl flex items-center space-x-2 hover:bg-green-100 transition disabled:opacity-50 font-medium text-sm">
              {isSyncingGemcli ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
              <span>Sync gemcli</span>
            </button>
          )}

          <button onClick={() => handleImportBrowser('chrome')} disabled={isImporting}
            title="Only works when the backend runs on the same machine as your Chrome browser"
            className="bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-500/20 px-4 py-2.5 rounded-xl flex items-center space-x-2 hover:bg-orange-100 transition disabled:opacity-50 font-medium text-sm">
            {isImporting ? <Loader2 size={18} className="animate-spin" /> : <Download size={18} />}
            <span>Import Chrome</span>
          </button>

          <button onClick={() => setIsAdding(!isAdding)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl flex items-center space-x-2 transition font-medium text-sm shadow-sm">
            {isAdding ? <X size={18} /> : <Plus size={18} />}
            <span>{isAdding ? 'Cancel' : 'Add Manual'}</span>
          </button>
        </div>
      </div>

      {isAdding && (
        <div className="bg-white dark:bg-gray-800 p-6 md:p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <h2 className="text-xl font-bold mb-6 text-gray-900 dark:text-white">Add Gemini Account</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Account Label</label>
              <input placeholder="e.g. Personal Workspace"
                className="w-full border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
                value={newAccount.label} onChange={e => setNewAccount({ ...newAccount, label: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Provider Type</label>
              <select className="w-full border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
                value={newAccount.provider} onChange={e => setNewAccount({ ...newAccount, provider: e.target.value })}>
                <option value="webapi">WebApi (Browser Cookies)</option>
                <option value="mcpcli">MCP-CLI (API Key or Profile)</option>
              </select>
            </div>
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Credentials</label>
              <textarea
                placeholder={newAccount.provider === 'webapi' ? 'Format: __Secure-1PSID|__Secure-1PSIDTS' : 'Paste Gemini API Key or leave {} for default profile'}
                className="w-full border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-3 rounded-xl h-28 font-mono text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                value={newAccount.credentials} onChange={e => setNewAccount({ ...newAccount, credentials: e.target.value })} />
            </div>
          </div>
          <div className="mt-6 flex justify-end space-x-3">
            <button onClick={() => setIsAdding(false)} className="px-5 py-2.5 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl font-medium">Cancel</button>
            <button onClick={handleAddAccount} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-xl font-medium shadow-sm">Save Account</button>
          </div>
        </div>
      )}

      {gemcliStatus?.logged_in && !accounts.some(a => a.provider === 'mcpcli' && a.email === gemcliStatus.email) && (
        <div className="flex items-center justify-between bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700/40 rounded-2xl px-5 py-3.5">
          <div>
            <p className="font-medium text-green-800 dark:text-green-300 text-sm">gemcli logged in as <span className="font-bold">{gemcliStatus.email}</span></p>
            <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">Click "Sync gemcli" to add this account to the gateway.</p>
          </div>
          <button onClick={handleSyncGemcli} disabled={isSyncingGemcli}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 disabled:opacity-50">
            {isSyncingGemcli ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            Sync Now
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-12 flex justify-center">
          <Loader2 className="animate-spin text-blue-600 dark:text-blue-400" size={48} />
        </div>
      ) : viewMode === 'list' ? (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left whitespace-nowrap">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Label</th>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Provider</th>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Health</th>
                  <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50 text-sm">
                {accounts.map((a: any) => (
                  <tr key={a.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-100">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${a.provider === 'webapi' ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' : 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'}`}>
                          {a.provider === 'webapi' ? <Globe size={16} /> : <Key size={16} />}
                        </div>
                        {renameState[a.id] !== undefined ? (
                          <div className="flex items-center gap-2">
                            <input autoFocus
                              className="border border-blue-400 bg-transparent px-2 py-0.5 rounded-lg text-sm focus:outline-none"
                              value={renameState[a.id]}
                              onChange={e => setRenameState(s => ({ ...s, [a.id]: e.target.value }))}
                              onKeyDown={e => { if (e.key === 'Enter') saveRename(a.id); if (e.key === 'Escape') cancelRename(a.id) }} />
                            <button onClick={() => saveRename(a.id)} className="text-green-600 hover:text-green-800"><Check size={15} /></button>
                            <button onClick={() => cancelRename(a.id)} className="text-gray-400 hover:text-gray-600"><X size={15} /></button>
                          </div>
                        ) : (
                          <div className="flex flex-col">
                            <div className="flex items-center gap-2 group/label">
                              <span>{a.label}</span>
                              <button onClick={() => startRename(a.id, a.label)} className="opacity-0 group-hover/label:opacity-100 text-gray-400 hover:text-blue-500 transition-opacity"><Pencil size={13} /></button>
                            </div>
                            {a.email && <span className="text-xs text-gray-400 dark:text-gray-500">{a.email}</span>}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 capitalize text-gray-600 dark:text-gray-300 font-medium">{a.provider}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${a.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}`}>{a.status}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center space-x-1.5">{healthBadge(a.health_status)}</div>
                        {validateErrors[a.id] && (
                          <span className="text-xs text-red-500 dark:text-red-400 max-w-xs break-words">{validateErrors[a.id]}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right space-x-3">
                      <button onClick={() => handleValidate(a.id)} className="text-blue-600 dark:text-blue-400 hover:text-blue-800 font-medium">Validate</button>
                      <button onClick={() => handleDelete(a.id)} className="text-red-500 hover:text-red-700 p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg inline-flex"><Trash2 size={16} /></button>
                    </td>
                  </tr>
                ))}
                {accounts.length === 0 && (
                  <tr><td colSpan={5} className="p-12 text-center text-gray-500">No accounts linked yet. Add one to get started.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((a: any) => (
            <div key={a.id} className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
              <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                <button onClick={() => startRename(a.id, a.label)} className="text-gray-400 hover:text-blue-500 bg-gray-50 dark:bg-gray-700 p-2 rounded-lg"><Pencil size={14} /></button>
                <button onClick={() => handleDelete(a.id)} className="text-red-500 hover:text-red-700 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg"><Trash2 size={14} /></button>
              </div>

              <div className="flex items-start space-x-4 mb-4">
                <div className={`p-3 rounded-xl mt-1 ${a.provider === 'webapi' ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' : 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'}`}>
                  {a.provider === 'webapi' ? <Globe size={24} /> : <Key size={24} />}
                </div>
                <div className="flex-1 min-w-0">
                  {renameState[a.id] !== undefined ? (
                    <div className="flex items-center gap-2">
                      <input autoFocus
                        className="border border-blue-400 bg-transparent px-2 py-0.5 rounded-lg text-sm focus:outline-none w-full"
                        value={renameState[a.id]}
                        onChange={e => setRenameState(s => ({ ...s, [a.id]: e.target.value }))}
                        onKeyDown={e => { if (e.key === 'Enter') saveRename(a.id); if (e.key === 'Escape') cancelRename(a.id) }} />
                      <button onClick={() => saveRename(a.id)} className="text-green-600"><Check size={15} /></button>
                      <button onClick={() => cancelRename(a.id)} className="text-gray-400"><X size={15} /></button>
                    </div>
                  ) : (
                    <h3 className="font-bold text-lg text-gray-900 dark:text-white leading-tight truncate">{a.label}</h3>
                  )}
                  <p className="text-sm text-gray-500 capitalize">{a.provider}</p>
                  {a.email && <p className="text-xs text-gray-400 dark:text-gray-500 truncate">{a.email}</p>}
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5 text-sm">{healthBadge(a.health_status)}</div>
                  <button onClick={() => handleValidate(a.id)} className="text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 px-3 py-1.5 rounded-lg font-medium">Validate</button>
                </div>
                {validateErrors[a.id] && (
                  <p className="mt-2 text-xs text-red-500 dark:text-red-400 break-words">{validateErrors[a.id]}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Accounts
