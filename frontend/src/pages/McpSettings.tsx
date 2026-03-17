import React, { useState, useEffect } from 'react'
import { Server, Key, Copy, Download, Code, Globe, Terminal, Check, Info, Shield, ExternalLink, AlertTriangle, RefreshCw, Layers } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const McpSettings = () => {
  const [tokens, setTokens] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [newToken, setNewToken] = useState<string | null>(null)
  const [tokenLabel, setTokenLabel] = useState('')
  const [activeTab, setActiveTab] = useState<'claude' | 'codex' | 'opencode'>('claude')
  const [mcpStatus, setMcpStatus] = useState({ reachable: false, toolsCount: 0, lastVerified: '' })
  const [isVerifying, setIsVerifying] = useState(false)

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchTokens = async () => {
    setIsLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/admin/mcp/tokens/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setTokens(res.data)
    } catch (err) {
      toast.error('Failed to fetch MCP tokens')
    } finally {
      setIsLoading(false)
    }
  }

  const verifyMcp = async () => {
    setIsVerifying(true)
    try {
      // FastMCP usually has a list tools endpoint or we can check the SSE mount
      const res = await axios.get(`${API_BASE}/mcp/tools`, {
        // We might need a token for this if it's protected by the middleware we added
        headers: { 'X-API-Key': tokens[0]?.key_hash || '' } 
      })
      setMcpStatus({ 
        reachable: true, 
        toolsCount: res.data.tools?.length || 0,
        lastVerified: new Date().toLocaleTimeString()
      })
    } catch (err) {
      // If we can't verify with a token, maybe it's just reachable
      try {
        await axios.get(`${API_BASE}/mcp/`)
        setMcpStatus(prev => ({ ...prev, reachable: true, lastVerified: new Date().toLocaleTimeString() }))
      } catch {
        setMcpStatus(prev => ({ ...prev, reachable: false, lastVerified: new Date().toLocaleTimeString() }))
      }
    } finally {
      setIsVerifying(false)
    }
  }

  useEffect(() => {
    fetchTokens()
    verifyMcp()
  }, [])

  const createToken = async () => {
    if (!tokenLabel) return toast.error('Please enter a label')
    try {
      const res = await axios.post(`${API_BASE}/admin/mcp/tokens/?label=${tokenLabel}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setNewToken(res.data.token)
      setTokens([...tokens, { id: res.data.id, label: tokenLabel, status: 'active', created_at: new Date() }])
      setTokenLabel('')
      toast.success('MCP token created successfully')
    } catch (err) {
      toast.error('Failed to create MCP token')
    }
  }

  const revokeToken = async (id: number) => {
    try {
      await axios.delete(`${API_BASE}/admin/mcp/tokens/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setTokens(tokens.filter(t => t.id !== id))
      toast.success('Token revoked')
    } catch (err) {
      toast.error('Failed to revoke token')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const getClaudeConfig = (token: string) => {
    return JSON.stringify({
      mcpServers: {
        "gemini-gateway": {
          command: "npx",
          args: ["-y", "@modelcontextprotocol/server-gemini-gateway", "--url", `${API_BASE}/mcp`],
          env: {
             "GATEWAY_AUTH_TOKEN": token
          }
        }
      }
    }, null, 2)
  }

  const getCodexConfig = (token: string) => {
    return `[mcp_servers.gemini_gateway]\nurl = "${API_BASE}/mcp"\nheaders = { "Authorization" = "Bearer ${token}" }`
  }

  const getOpenCodeConfig = (token: string) => {
    return JSON.stringify({
      "mcp": {
        "gemini-gateway": {
          "type": "remote",
          "url": `${API_BASE}/mcp`,
          "headers": {
            "Authorization": `Bearer ${token}`
          }
        }
      }
    }, null, 2)
  }

  const selectedTokenValue = tokens[0]?.id ? 'REVEALED_ONLY_ONCE' : 'Create a token first'

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <Server className="mr-3 text-blue-600" />
            MCP Clients
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Universal Model Context Protocol configuration for Claude, Codex, and OpenCode
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-white dark:bg-gray-800 p-2 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
           <div className={`w-3 h-3 rounded-full ${mcpStatus.reachable ? 'bg-green-500' : 'bg-red-500'}`} />
           <span className="text-sm font-medium">MCP Server: {mcpStatus.reachable ? 'Online' : 'Offline'}</span>
           <span className="text-xs text-gray-400 ml-2">{mcpStatus.toolsCount} tools</span>
           <button onClick={verifyMcp} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors">
             <RefreshCw size={14} className={isVerifying ? 'animate-spin' : ''} />
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Token Management */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
            <h2 className="text-lg font-bold flex items-center mb-4">
              <Shield className="mr-2 text-indigo-500" size={20} />
              MCP Tokens
            </h2>
            
            <div className="space-y-4">
              <div className="flex space-x-2">
                <input 
                  type="text"
                  placeholder="Token Label (e.g. Cursor)"
                  value={tokenLabel}
                  onChange={(e) => setTokenLabel(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-50 dark:bg-gray-900 border-none rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                />
                <button 
                  onClick={createToken}
                  className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
                >
                  Create
                </button>
              </div>

              {newToken && (
                <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-800 dark:text-amber-400">NEW TOKEN - REVEALED ONCE</span>
                    <button onClick={() => setNewToken(null)} className="text-gray-400 hover:text-gray-600"><X size={14} /></button>
                  </div>
                  <div className="flex items-center space-x-2 bg-white dark:bg-gray-950 p-2 rounded border border-amber-200 dark:border-amber-800">
                    <code className="text-xs break-all font-mono">{newToken}</code>
                    <button onClick={() => copyToClipboard(newToken)} className="text-blue-600"><Copy size={16} /></button>
                  </div>
                  <p className="text-[10px] text-amber-700 dark:text-amber-500 italic">Copy this now. You won't be able to see it again.</p>
                </div>
              )}

              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {tokens.map(t => (
                  <div key={t.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-transparent hover:border-gray-200 dark:hover:border-gray-700 transition-all">
                    <div>
                      <div className="text-sm font-medium truncate w-32">{t.label}</div>
                      <div className="text-[10px] text-gray-400">{new Date(t.created_at).toLocaleDateString()}</div>
                    </div>
                    <button 
                      onClick={() => revokeToken(t.id)}
                      className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                      title="Revoke Token"
                    >
                      <AlertTriangle size={14} />
                    </button>
                  </div>
                ))}
                {tokens.length === 0 && !isLoading && (
                  <div className="text-center py-8 text-gray-400 text-sm">No active tokens</div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-blue-600 text-white p-6 rounded-2xl shadow-lg shadow-blue-500/20 space-y-3">
             <h3 className="font-bold flex items-center">
               <Info size={18} className="mr-2" />
               Quick Tip
             </h3>
             <p className="text-sm text-blue-100">
               Use separate tokens for each client (Claude, Cursor, etc.) to track usage and revoke access individually if needed.
             </p>
          </div>
        </div>

        {/* Client Configuration */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 font-bold text-xl">
              <Layers className="text-blue-500" size={24} />
              <h2>Client Configuration</h2>
            </div>
            <div className="flex bg-gray-100 dark:bg-gray-900 p-1 rounded-xl">
              <button 
                onClick={() => setActiveTab('claude')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'claude' ? 'bg-white dark:bg-gray-800 shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Claude
              </button>
              <button 
                onClick={() => setActiveTab('codex')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'codex' ? 'bg-white dark:bg-gray-800 shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Codex
              </button>
              <button 
                onClick={() => setActiveTab('opencode')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'opencode' ? 'bg-white dark:bg-gray-800 shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                OpenCode
              </button>
            </div>
          </div>

          <div className="space-y-6">
            {activeTab === 'claude' && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center justify-between">
                   <span className="text-sm font-bold text-gray-700 dark:text-gray-300">CLI Add Command</span>
                   <span className="text-[10px] bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">Recommended</span>
                </div>
                <div className="relative">
                  <pre className="p-4 bg-gray-900 text-green-400 rounded-xl font-mono text-sm overflow-x-auto">
                    {`claude mcp add --transport http ${API_BASE}/mcp --header "Authorization: Bearer <TOKEN>"`}
                  </pre>
                  <button 
                    onClick={() => copyToClipboard(`claude mcp add --transport http ${API_BASE}/mcp --header "Authorization: Bearer ${tokens[0]?.token || 'YOUR_TOKEN'}"`)}
                    className="absolute top-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition"
                  >
                    <Copy size={16} />
                  </button>
                </div>

                <div className="pt-4">
                  <span className="text-sm font-bold text-gray-700 dark:text-gray-300">Manual JSON Config</span>
                </div>
                <div className="relative">
                  <pre className="p-4 bg-gray-900 text-gray-300 rounded-xl font-mono text-xs overflow-x-auto max-h-60">
                    {getClaudeConfig(tokens[0]?.token || '<YOUR_TOKEN>')}
                  </pre>
                  <button 
                    onClick={() => copyToClipboard(getClaudeConfig(tokens[0]?.token || ''))}
                    className="absolute top-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition"
                  >
                    <Copy size={16} />
                  </button>
                </div>
                <p className="text-xs text-gray-500 flex items-start">
                  <Globe size={14} className="mr-1.5 mt-0.5 shrink-0" />
                  <span>Config Path: <code>~/Library/Application Support/Claude/claude_desktop_config.json</code></span>
                </p>
              </div>
            )}

            {activeTab === 'codex' && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center justify-between">
                   <span className="text-sm font-bold text-gray-700 dark:text-gray-300">config.toml</span>
                </div>
                <div className="relative">
                  <pre className="p-4 bg-gray-900 text-gray-300 rounded-xl font-mono text-sm overflow-x-auto">
                    {getCodexConfig(tokens[0]?.token || '<YOUR_TOKEN>')}
                  </pre>
                  <button 
                    onClick={() => copyToClipboard(getCodexConfig(tokens[0]?.token || ''))}
                    className="absolute top-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition"
                  >
                    <Copy size={16} />
                  </button>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-100 dark:border-gray-700 space-y-2">
                   <h4 className="text-xs font-bold">Verification</h4>
                   <p className="text-[11px] text-gray-500">In the Codex TUI, use <code>/mcp</code> to manage servers or check the settings panel in the IDE.</p>
                </div>
                <p className="text-xs text-gray-500 flex items-start">
                  <Globe size={14} className="mr-1.5 mt-0.5 shrink-0" />
                  <span>Config Path: <code>~/.codex/config.toml</code></span>
                </p>
              </div>
            )}

            {activeTab === 'opencode' && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center justify-between">
                   <span className="text-sm font-bold text-gray-700 dark:text-gray-300">opencode.json</span>
                </div>
                <div className="relative">
                  <pre className="p-4 bg-gray-900 text-gray-300 rounded-xl font-mono text-xs overflow-x-auto max-h-60">
                    {getOpenCodeConfig(tokens[0]?.token || '<YOUR_TOKEN>')}
                  </pre>
                  <button 
                    onClick={() => copyToClipboard(getOpenCodeConfig(tokens[0]?.token || ''))}
                    className="absolute top-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition"
                  >
                    <Copy size={16} />
                  </button>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-100 dark:border-gray-700 space-y-2">
                   <h4 className="text-xs font-bold">Verification Command</h4>
                   <div className="flex items-center justify-between bg-white dark:bg-gray-950 p-2 rounded text-xs font-mono">
                      <code>opencode mcp list</code>
                      <button onClick={() => copyToClipboard('opencode mcp list')}><Copy size={12} /></button>
                   </div>
                </div>
                <p className="text-xs text-gray-500 flex items-start">
                  <Globe size={14} className="mr-1.5 mt-0.5 shrink-0" />
                  <span>Config Path: <code>~/.config/opencode/opencode.json</code></span>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Troubleshooting */}
      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
          <Info className="mr-2 text-blue-500" size={20} />
          Troubleshooting & Verification
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
           <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700/50 space-y-2">
              <h4 className="font-bold text-sm flex items-center text-amber-600"><AlertTriangle size={14} className="mr-1.5" /> Connection Refused</h4>
              <p className="text-xs text-gray-500">Ensure the gateway is running on 0.0.0.0 and your firewall allows connections on port 6400.</p>
           </div>
           <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700/50 space-y-2">
              <h4 className="font-bold text-sm flex items-center text-red-600"><AlertTriangle size={14} className="mr-1.5" /> Auth Error (401)</h4>
              <p className="text-xs text-gray-500">Double-check your MCP Token. Remember it must be passed as a Bearer token or X-API-Key header.</p>
           </div>
           <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700/50 space-y-2">
              <h4 className="font-bold text-sm flex items-center text-blue-600"><RefreshCw size={14} className="mr-1.5" /> Tools Not Listing</h4>
              <p className="text-xs text-gray-500">Restart your MCP client (Claude Desktop, IDE) after updating the configuration file.</p>
           </div>
        </div>
      </div>
    </div>
  )
}

const X = ({ size, className }: { size: number, className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
)

export default McpSettings
