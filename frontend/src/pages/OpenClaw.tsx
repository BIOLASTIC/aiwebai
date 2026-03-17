import React, { useEffect, useState } from 'react'
import { Download, Package, Shield, Terminal, Info, ExternalLink, Layers, Cpu, Zap, AlertTriangle, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const API_BASE_URL = `http://${window.location.hostname}:6400`

interface AccountInfo {
  id: number
  label: string
  provider: string
  adapter_type: string
  health: string
  capabilities: string[]
  active: boolean
}

interface CapabilitySummary {
  system_status: string
  total_accounts: number
  active_accounts: number
  webapi_accounts: Array<{ id: number; label: string; active: boolean; health: string }>
  webapi_capabilities: string[]
  mcpcli_accounts: Array<{ id: number; label: string; active: boolean; health: string }>
  mcpcli_capabilities: string[]
  capability_notes: Record<string, string>
}

const CAPABILITY_ICONS: Record<string, string> = {
  chat: '💬',
  image: '🖼️',
  video: '🎬',
  music: '🎵',
  research: '🔬',
}

const ADAPTER_COLORS: Record<string, string> = {
  webapi: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800',
  mcpcli: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border-purple-200 dark:border-purple-800',
}

const OpenClawPage = () => {
  const API_BASE = `http://${window.location.hostname}:6400`
  const [accounts, setAccounts] = useState<AccountInfo[]>([])
  const [capabilities, setCapabilities] = useState<CapabilitySummary | null>(null)
  const [loadingCaps, setLoadingCaps] = useState(false)
  const [selectedAdapter, setSelectedAdapter] = useState<string>('auto')

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const downloadPlugin = (format: 'zip' | 'tgz') => {
    window.open(`${API_BASE}/plugins/openclaw/plugin.${format}`, '_blank')
  }

  const fetchCapabilities = async () => {
    setLoadingCaps(true)
    try {
      const token = localStorage.getItem('token')
      // Fetch via MCP tool call through REST-like proxy or directly via accounts endpoint
      const [acctRes, capsProxy] = await Promise.allSettled([
        axios.get(`${API_BASE_URL}/admin/accounts`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_BASE_URL}/mcp/status`, { headers: { Authorization: `Bearer ${token}` } }),
      ])

      if (acctRes.status === 'fulfilled') {
        const data = acctRes.value.data
        const acctList: AccountInfo[] = (Array.isArray(data) ? data : data.accounts || []).map((a: any) => ({
          id: a.id,
          label: a.label,
          provider: a.provider,
          adapter_type: a.provider,
          health: a.health_status || 'unknown',
          capabilities: a.provider === 'mcpcli' ? ['chat', 'image', 'video', 'music', 'research'] : ['chat', 'image'],
          active: a.status === 'active',
        }))
        setAccounts(acctList)

        // Build capability summary from accounts
        const webapi = acctList.filter(a => a.provider === 'webapi')
        const mcpcli = acctList.filter(a => a.provider === 'mcpcli')
        setCapabilities({
          system_status: acctList.length > 0 ? 'online' : 'degraded — no active accounts',
          total_accounts: acctList.length,
          active_accounts: acctList.filter(a => a.active).length,
          webapi_accounts: webapi.map(a => ({ id: a.id, label: a.label, active: a.active, health: a.health })),
          webapi_capabilities: ['chat', 'image'],
          mcpcli_accounts: mcpcli.map(a => ({ id: a.id, label: a.label, active: a.active, health: a.health })),
          mcpcli_capabilities: ['chat', 'image', 'video', 'music', 'research'],
          capability_notes: {
            chat: 'Available via webapi or mcpcli',
            image: 'Available via webapi or mcpcli (mcpcli required for imagen-3.0/veo models)',
            video: 'mcpcli only — webapi does not support video generation',
            music: 'mcpcli only — webapi does not support music generation',
            research: 'mcpcli only — webapi does not support deep research',
          },
        })
      }
    } catch (err: any) {
      toast.error('Failed to load capabilities')
    } finally {
      setLoadingCaps(false)
    }
  }

  useEffect(() => {
    fetchCapabilities()
  }, [])

  const adapterParam = selectedAdapter === 'auto' ? '' : `adapter: '${selectedAdapter === 'gemini-webapi' ? 'webapi' : 'mcpcli'}'`

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <Cpu className="mr-3 text-purple-600" />
            OpenClaw Integration
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Native plugin and skills for the OpenClaw agentic framework
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => downloadPlugin('zip')}
            className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-xl text-sm font-medium hover:bg-purple-700 transition shadow-sm"
          >
            <Download size={16} className="mr-2" />
            Download .zip
          </button>
          <button
            onClick={() => downloadPlugin('tgz')}
            className="flex items-center px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition border dark:border-gray-700 shadow-sm"
          >
            <Download size={16} className="mr-2" />
            Download .tgz
          </button>
        </div>
      </div>

      {/* System Status Banner */}
      {capabilities && (
        <div className={`flex items-center justify-between p-4 rounded-xl border ${capabilities.active_accounts > 0 ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800' : 'bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800'}`}>
          <div className="flex items-center space-x-3">
            {capabilities.active_accounts > 0
              ? <CheckCircle size={20} className="text-green-500" />
              : <AlertTriangle size={20} className="text-amber-500" />}
            <div>
              <div className={`font-semibold text-sm ${capabilities.active_accounts > 0 ? 'text-green-700 dark:text-green-300' : 'text-amber-700 dark:text-amber-300'}`}>
                {capabilities.system_status}
              </div>
              <div className="text-xs text-gray-500">{capabilities.active_accounts} of {capabilities.total_accounts} accounts active</div>
            </div>
          </div>
          <button onClick={fetchCapabilities} disabled={loadingCaps} className="p-2 rounded-lg hover:bg-white/50 dark:hover:bg-white/10 transition">
            <RefreshCw size={16} className={loadingCaps ? 'animate-spin text-gray-400' : 'text-gray-500'} />
          </button>
        </div>
      )}

      {/* Adapter Selector */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
        <h2 className="text-base font-bold mb-3 flex items-center">
          <Zap size={18} className="mr-2 text-yellow-500" />
          Adapter Selection
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          When calling MCP tools from OpenClaw, you can specify which adapter to use. This selection affects the example code below.
        </p>
        <div className="flex flex-wrap gap-3">
          {[
            { value: 'auto', label: 'Auto (recommended)', desc: 'Gateway picks the best adapter' },
            { value: 'gemini-webapi', label: 'gemini-webapi', desc: 'Chat + Image only' },
            { value: 'gemini-mcpcli', label: 'gemini-web-mcp-cli', desc: 'Full capabilities (video, music, research)' },
          ].map(opt => (
            <button
              key={opt.value}
              onClick={() => setSelectedAdapter(opt.value)}
              className={`flex-1 min-w-[160px] text-left px-4 py-3 rounded-xl border-2 transition text-sm ${selectedAdapter === opt.value ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}`}
            >
              <div className="font-semibold">{opt.label}</div>
              <div className="text-xs text-gray-400 mt-0.5">{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Accounts & Capabilities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Accounts with adapter badges */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <h2 className="text-base font-bold mb-4 flex items-center">
            <Info size={18} className="mr-2 text-blue-500" />
            Configured Accounts
          </h2>
          {accounts.length === 0 ? (
            <div className="text-sm text-gray-400 text-center py-6">No accounts configured yet. Add accounts in the Accounts section.</div>
          ) : (
            <div className="space-y-3">
              {accounts.map(acct => (
                <div key={acct.id} className="flex items-start justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-700">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{acct.label}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-mono ${ADAPTER_COLORS[acct.adapter_type] || 'bg-gray-100 text-gray-600'}`}>
                        {acct.adapter_type}
                      </span>
                      {acct.active
                        ? <CheckCircle size={14} className="text-green-500" />
                        : <XCircle size={14} className="text-red-400" />}
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {acct.capabilities.map(cap => (
                        <span key={cap} className="text-xs px-1.5 py-0.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded text-gray-600 dark:text-gray-400">
                          {CAPABILITY_ICONS[cap] || ''} {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-lg font-medium ${acct.health === 'healthy' ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400' : acct.health === 'unhealthy' ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}`}>
                    {acct.health}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Capability Matrix */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <h2 className="text-base font-bold mb-4 flex items-center">
            <Layers size={18} className="mr-2 text-purple-500" />
            Capability Matrix
          </h2>
          <div className="space-y-2">
            {capabilities && Object.entries(capabilities.capability_notes).map(([cap, note]) => {
              const webapiSupports = capabilities.webapi_capabilities.includes(cap)
              const mcpcliSupports = capabilities.mcpcli_capabilities.includes(cap)
              const hasWebapi = capabilities.webapi_accounts.some(a => a.active)
              const hasMcpcli = capabilities.mcpcli_accounts.some(a => a.active)
              const available = (webapiSupports && hasWebapi) || (mcpcliSupports && hasMcpcli)
              return (
                <div key={cap} className={`flex items-start p-3 rounded-xl border ${available ? 'bg-green-50 dark:bg-green-900/10 border-green-100 dark:border-green-900/30' : 'bg-gray-50 dark:bg-gray-900/30 border-gray-100 dark:border-gray-800'}`}>
                  <span className="text-lg mr-3 mt-0.5">{CAPABILITY_ICONS[cap] || '•'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm capitalize">{cap}</span>
                      <div className="flex gap-1">
                        <span className={`text-xs px-1.5 py-0.5 rounded border font-mono ${webapiSupports ? 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800' : 'bg-gray-100 text-gray-400 border-gray-200 dark:bg-gray-800 dark:text-gray-600 dark:border-gray-700 line-through'}`}>
                          webapi
                        </span>
                        <span className={`text-xs px-1.5 py-0.5 rounded border font-mono ${mcpcliSupports ? 'bg-purple-50 text-purple-600 border-purple-200 dark:bg-purple-900/20 dark:text-purple-300 dark:border-purple-800' : 'bg-gray-100 text-gray-400 border-gray-200 dark:bg-gray-800 dark:text-gray-600 dark:border-gray-700 line-through'}`}>
                          mcpcli
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{note}</p>
                  </div>
                  {available
                    ? <CheckCircle size={16} className="text-green-500 flex-shrink-0 mt-0.5" />
                    : <AlertTriangle size={16} className="text-amber-400 flex-shrink-0 mt-0.5" />}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Installation Instructions */}
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-6">
          <div className="flex items-center space-x-2 text-purple-600 dark:text-purple-400 font-bold text-lg">
            <Terminal className="text-purple-500" size={24} />
            <h2>Install Instructions</h2>
          </div>

          <div className="space-y-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-100 dark:border-gray-700 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">1. Local Directory Install</h4>
              <div className="relative">
                <pre className="p-3 bg-gray-900 text-gray-300 rounded-lg font-mono text-xs overflow-x-auto">
                  {`openclaw plugins add ./path/to/extracted/plugin`}
                </pre>
                <button
                  onClick={() => copyToClipboard(`openclaw plugins add ./path/to/extracted/plugin`)}
                  className="absolute top-2 right-2 p-1.5 bg-gray-800 text-white rounded transition"
                >
                  <Copy size={12} />
                </button>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-100 dark:border-gray-700 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">2. Package Install (.tgz)</h4>
              <div className="relative">
                <pre className="p-3 bg-gray-900 text-gray-300 rounded-lg font-mono text-xs overflow-x-auto">
                  {`openclaw plugins add ./gemini-gateway-plugin.tgz`}
                </pre>
                <button
                  onClick={() => copyToClipboard(`openclaw plugins add ./gemini-gateway-plugin.tgz`)}
                  className="absolute top-2 right-2 p-1.5 bg-gray-800 text-white rounded transition"
                >
                  <Copy size={12} />
                </button>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-100 dark:border-gray-700 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">3. Verify Installation</h4>
              <div className="relative">
                <pre className="p-3 bg-gray-900 text-gray-300 rounded-lg font-mono text-xs overflow-x-auto">
                  {`openclaw plugins list\nopenclaw skills list`}
                </pre>
                <button
                  onClick={() => copyToClipboard(`openclaw plugins list\nopenclaw skills list`)}
                  className="absolute top-2 right-2 p-1.5 bg-gray-800 text-white rounded transition"
                >
                  <Copy size={12} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* MCP Tool Usage with adapter param */}
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-6">
          <div className="flex items-center space-x-2 font-bold text-lg">
            <Zap className="text-yellow-500" size={24} />
            <h2>MCP Tool Usage</h2>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Adapter: <span className="font-mono font-bold text-purple-600">{selectedAdapter}</span>
            {selectedAdapter === 'auto' && <span className="ml-2 text-xs text-gray-400">(gateway auto-selects)</span>}
          </p>

          <div className="space-y-3">
            {[
              { tool: 'chat', snippet: `chat(prompt="Hello, Gemini!"${adapterParam ? ', ' + adapterParam : ''})` },
              { tool: 'generate_image', snippet: `generate_image(prompt="A sunset"${adapterParam ? ', ' + adapterParam : ''})` },
              { tool: 'generate_video', snippet: `generate_video(prompt="A flying bird"${adapterParam ? ', ' + adapterParam : ''})` },
              { tool: 'generate_music', snippet: `generate_music(prompt="Calm jazz"${adapterParam ? ', ' + adapterParam : ''})` },
              { tool: 'deep_research', snippet: `deep_research(prompt="History of AI"${adapterParam ? ', ' + adapterParam : ''})` },
              { tool: 'list_accounts', snippet: `list_accounts()` },
              { tool: 'get_capabilities', snippet: `get_capabilities()` },
            ].map(({ tool, snippet }) => (
              <div key={tool} className="relative">
                <pre className="p-3 bg-gray-900 text-gray-300 rounded-lg font-mono text-xs overflow-x-auto pr-10">
                  {snippet}
                </pre>
                <button
                  onClick={() => copyToClipboard(snippet)}
                  className="absolute top-2 right-2 p-1.5 bg-gray-700 text-white rounded transition hover:bg-gray-600"
                >
                  <Copy size={12} />
                </button>
              </div>
            ))}
          </div>

          {selectedAdapter === 'gemini-webapi' && (
            <div className="flex items-start p-3 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-xl text-sm">
              <AlertTriangle size={16} className="text-amber-500 mr-2 flex-shrink-0 mt-0.5" />
              <span className="text-amber-700 dark:text-amber-300">
                <strong>webapi</strong> does not support video, music, or deep research.
                Use <code className="font-mono">adapter='mcpcli'</code> for those capabilities.
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Bundled Skills + Version */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-6">
          <h2 className="text-xl font-bold flex items-center">
            <Package className="mr-2 text-blue-500" size={24} />
            Bundled Skills
          </h2>
          <div className="space-y-4">
            <div className="flex items-start space-x-3 p-4 rounded-xl bg-purple-50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-900/30">
              <div className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm text-purple-600">
                <Layers size={18} />
              </div>
              <div>
                <div className="font-bold text-sm">gateway-operator</div>
                <p className="text-xs text-gray-500 mt-1">Teaches OpenClaw how to use image, video, music and research tools via the gateway.</p>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-4 rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30">
              <div className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm text-blue-600">
                <Shield size={18} />
              </div>
              <div>
                <div className="font-bold text-sm">gateway-troubleshooter</div>
                <p className="text-xs text-gray-500 mt-1">Automated diagnostic routines for auth and connectivity issues.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 text-white p-8 rounded-2xl shadow-xl space-y-4">
          <h3 className="font-bold flex items-center text-lg">
            <Info size={20} className="mr-2 text-blue-400" />
            Version Information
          </h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Plugin Version</span>
              <div className="font-mono">1.0.0</div>
            </div>
            <div>
              <span className="text-gray-500">Release Date</span>
              <div className="font-mono">Mar 17, 2026</div>
            </div>
            <div>
              <span className="text-gray-500">Min OpenClaw</span>
              <div className="font-mono">v2.4.0</div>
            </div>
            <div>
              <span className="text-gray-500">Status</span>
              <div className="text-green-400 font-bold">STABLE</div>
            </div>
          </div>
          <div className="pt-2 border-t border-gray-700">
            <div className="text-xs text-gray-500 mb-2">MCP Server</div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
              <span className="font-mono text-xs text-green-400">{API_BASE}/mcp/</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const Copy = ({ size, className }: { size: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
)

export default OpenClawPage
