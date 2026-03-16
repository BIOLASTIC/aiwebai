import React, { useState, useEffect } from 'react'
import { Server, Key, Copy, Download, Code, Globe, Terminal, Check, Info } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

const McpSettings = () => {
  const [apiKeys, setApiKeys] = useState<any[]>([])
  const [selectedKey, setSelectedKey] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchKeys = async () => {
    setIsLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/admin/api-keys/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setApiKeys(res.data)
      if (res.data.length > 0) setSelectedKey(res.data[0].key_hash)
    } catch (err) {
      toast.error('Failed to fetch API keys')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchKeys()
  }, [])

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const generateClaudeConfig = () => {
    const config = {
      mcpServers: {
        "gemini-gateway": {
          command: "sh",
          args: ["-c", `export GATEWAY_API_KEY="${selectedKey}"; npx @modelcontextprotocol/server-gemini-gateway --url ${API_BASE}/mcp/sse`]
        }
      }
    }
    return JSON.stringify(config, null, 2)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <Server className="mr-3 text-blue-600" />
            MCP Configuration
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Connect Gemini Gateway to Claude, Cursor, and other MCP-aware IDEs
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Step 1: API Key Selection */}
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-6">
          <div className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 font-bold text-lg">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-50 dark:bg-blue-900/20 text-sm">1</span>
            <h2>Select API Key</h2>
          </div>
          <p className="text-sm text-gray-500">
            Choose an API key to authenticate your MCP client. All requests through MCP will use this key for billing and limits.
          </p>
          
          <div className="space-y-2">
            {apiKeys.length === 0 ? (
              <div className="p-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-900/30 rounded-xl text-amber-700 dark:text-amber-400 text-sm flex items-start">
                <Info size={18} className="mr-2 mt-0.5" />
                <span>No API keys found. Create one in the Admin section first.</span>
              </div>
            ) : (
              <select 
                value={selectedKey}
                onChange={(e) => setSelectedKey(e.target.value)}
                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition"
              >
                {apiKeys.map(k => (
                  <option key={k.id} value={k.key_hash}>{k.label || `Key #${k.id}`}</option>
                ))}
              </select>
            )}
          </div>
          
          {selectedKey && (
            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl flex items-center justify-between">
              <code className="text-xs font-mono text-gray-600 truncate mr-4">
                {selectedKey.substring(0, 10)}...{selectedKey.substring(selectedKey.length - 8)}
              </code>
              <button 
                onClick={() => copyToClipboard(selectedKey)}
                className="text-blue-600 hover:text-blue-700 transition"
              >
                <Copy size={18} />
              </button>
            </div>
          )}
        </div>

        {/* Step 2: Configuration Generator */}
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-6">
          <div className="flex items-center space-x-2 text-green-600 dark:text-green-400 font-bold text-lg">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-green-50 dark:bg-green-900/20 text-sm">2</span>
            <h2>Client Configuration</h2>
          </div>
          
          <div className="space-y-4">
            <div className="flex space-x-2">
              <button className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg font-medium">Claude Desktop</button>
              <button className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded-lg font-medium">Cursor</button>
              <button className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded-lg font-medium">Windsurf</button>
            </div>
            
            <div className="relative">
              <pre className="p-4 bg-gray-900 text-gray-300 rounded-xl font-mono text-xs overflow-x-auto max-h-60">
                {generateClaudeConfig()}
              </pre>
              <button 
                onClick={() => copyToClipboard(generateClaudeConfig())}
                className="absolute top-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition"
              >
                <Copy size={16} />
              </button>
            </div>
            
            <p className="text-xs text-gray-500">
              Paste this into your <code>claude_desktop_config.json</code>.
              <br />
              <span className="italic">macOS: ~/Library/Application Support/Claude/claude_desktop_config.json</span>
            </p>
          </div>
        </div>
      </div>

      {/* Connection Guide */}
      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
          <Code className="mr-2 text-blue-500" size={20} />
          Supported Tools & Resources
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { title: 'Chat & Streaming', desc: 'Unified chat endpoint for all Gemini models' },
            { title: 'Image/Video Gen', desc: 'Generate visual content directly from prompt' },
            { title: 'Deep Research', desc: 'Long-running multi-step reasoning sessions' },
            { title: 'Gems CRUD', desc: 'Create and manage system prompts as tools' },
            { title: 'Extensions', desc: 'Invoke Maps, YouTube, and Flights tools' },
            { title: 'History & Replay', desc: 'Access and delete conversation history' },
          ].map((tool, i) => (
            <div key={i} className="flex items-start space-x-3 p-4 rounded-xl bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700/50">
              <Check className="text-green-500 shrink-0 mt-1" size={16} />
              <div>
                <div className="font-bold text-sm text-gray-900 dark:text-white">{tool.title}</div>
                <div className="text-xs text-gray-500">{tool.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default McpSettings
