import React from 'react'
import { Download, Package, Shield, Terminal, Info, Check, ExternalLink, Globe, Layers, Cpu } from 'lucide-react'
import { toast } from 'sonner'

const OpenClawPage = () => {
  const API_BASE = `http://${window.location.hostname}:6400`
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const downloadPlugin = (format: 'zip' | 'tgz') => {
    // In a real app, these files would be generated or served from /plugins
    window.open(`${API_BASE}/plugins/openclaw/plugin.${format}`, '_blank')
  }

  return (
    <div className="space-y-6 pb-12">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Installation Instructions */}
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-6">
          <div className="flex items-center space-x-2 text-purple-600 dark:text-purple-400 font-bold text-lg text-xl">
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

        {/* Plugin Metadata */}
        <div className="space-y-6">
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
           </div>
        </div>
      </div>
    </div>
  )
}

const Copy = ({ size, className }: { size: number, className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
)

const X = ({ size, className }: { size: number, className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
)

export default OpenClawPage
