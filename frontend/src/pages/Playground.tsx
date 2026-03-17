import React, { useState, useRef, useEffect, useCallback } from 'react'
import {
  Send, Plus, Trash2, Image as ImageIcon, Video, Music, Search,
  Loader2, Bot, User, Zap,
} from 'lucide-react'
import axios from 'axios'
import { toast } from 'sonner'
import ModelSelector from '../components/playground/ModelSelector'
import AccountSelector from '../components/playground/AccountSelector'
import ChatPanel from '../components/playground/ChatPanel'
import ImagePanel from '../components/playground/ImagePanel'
import VideoPanel from '../components/playground/VideoPanel'
import JobStatusCard from '../components/playground/JobStatusCard'
import FilePicker from '../components/playground/FilePicker'

const API_BASE = `http://${window.location.hostname}:6400`

interface Message {
  role: 'user' | 'assistant'
  content: string
  imageUrl?: string
  jobId?: string
  ts: number
}
interface Chat {
  id: string
  title: string
  messages: Message[]
  createdAt: number
}
interface AccountCapabilities {
  chat?: boolean;
  image?: boolean;
  video?: boolean;
  music?: boolean;
  research?: boolean;
}
interface Account {
  id: number;
  label: string;
  health_status: string;
  provider?: string;
  capabilities?: AccountCapabilities;
}
interface ModelItem { id: number; provider_model_name: string; display_name: string; family: string; source_provider?: string }

const generateId = (): string => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

const STORAGE_KEY = 'playground_chats_v2'
const loadChats = (): Chat[] => {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
}
const saveChats = (chats: Chat[]) => localStorage.setItem(STORAGE_KEY, JSON.stringify(chats))

const TOOL_OPTIONS = [
  { id: 'chat',     label: 'Chat',     icon: Bot },
  { id: 'image',    label: 'Image',    icon: ImageIcon },
  { id: 'video',    label: 'Video',    icon: Video },
  { id: 'music',    label: 'Music',    icon: Music },
  { id: 'research', label: 'Research', icon: Search },
]

const Playground = () => {
  const token = localStorage.getItem('token')
  const headers = { Authorization: `Bearer ${token}` }

  const [chats, setChats] = useState<Chat[]>(loadChats)
  const [activeChatId, setActiveChatId] = useState<string | null>(() => loadChats()[0]?.id ?? null)
  const [prompt, setPrompt] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedTool, setSelectedTool] = useState('chat')

  // Default model per tool
  const DEFAULT_MODEL: Record<string, string> = {
    chat: 'gemini-3.0-flash',
    image: 'imagen-3.0',
    video: 'veo-2.0',
    music: 'lyria-1.0',
    research: 'gemini-research',
  }
  const [accounts, setAccounts] = useState<Account[]>([])
  const [models, setModels] = useState<ModelItem[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<string>('auto')
  const [selectedModel, setSelectedModel] = useState('gemini-3.0-flash')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [selectedAdapter, setSelectedAdapter] = useState<string>('auto')

  const bottomRef = useRef<HTMLDivElement>(null)

  const selectedAccount = accounts.find(a => String(a.id) === selectedAccountId)

  const activeChat = chats.find(c => c.id === activeChatId) ?? null

  useEffect(() => {
    axios.get(`${API_BASE}/admin/accounts/`, { headers }).then(r => setAccounts(r.data)).catch(() => {})
    axios.get(`${API_BASE}/admin/models/`, { headers }).then(r => setModels(r.data)).catch(() => {})
  }, [])

  useEffect(() => { saveChats(chats) }, [chats])
  useEffect(() => { 
    if (bottomRef.current && typeof bottomRef.current.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' }) 
    }
  }, [activeChat?.messages])

  const newChat = () => {
    const chat: Chat = { id: generateId(), title: 'New Chat', messages: [], createdAt: Date.now() }
    setChats(prev => [chat, ...prev])
    setActiveChatId(chat.id)
  }

  const deleteChat = (id: string) => {
    const next = chats.filter(c => c.id !== id)
    setChats(next)
    if (activeChatId === id) setActiveChatId(next[0]?.id ?? null)
  }

  const appendMessage = (chatId: string, msg: Message) => {
    setChats(prev => prev.map(c => {
      if (c.id !== chatId) return c
      const messages = [...c.messages, msg]
      const title = c.messages.length === 0 && msg.role === 'user'
        ? msg.content.slice(0, 42) + (msg.content.length > 42 ? '…' : '') : c.title
      return { ...c, messages, title }
    }))
  }

  const updateLastAssistant = (chatId: string, update: Partial<Message>) => {
    setChats(prev => prev.map(c => {
      if (c.id !== chatId) return c
      const messages = [...c.messages]
      const idx = [...messages].reverse().findIndex(m => m.role === 'assistant')
      if (idx >= 0) messages[messages.length - 1 - idx] = { ...messages[messages.length - 1 - idx], ...update }
      return { ...c, messages }
    }))
  }

  const pollJob = useCallback((chatId: string, jobId: string, type: string) => {
    const iv = setInterval(async () => {
      try {
        const r = await axios.get(`${API_BASE}/native/tasks/${jobId}`, { headers })
        if (r.data.status === 'completed') {
          clearInterval(iv)
          const rawUrl: string | undefined = r.data.result_url
          // Resolve root-relative URLs to absolute using the API base, and
          // drop any value that isn't a valid URL (guards against old error strings)
          const imageUrl = rawUrl?.startsWith('/')
            ? `${API_BASE}${rawUrl}`
            : rawUrl?.startsWith('http')
            ? rawUrl
            : undefined
          updateLastAssistant(chatId, {
            content: `${type.charAt(0).toUpperCase() + type.slice(1)} generation complete.`,
            imageUrl,
          })
        } else if (r.data.status === 'failed') {
          clearInterval(iv)
          updateLastAssistant(chatId, { content: `Generation failed: ${r.data.error || 'Unknown error'}` })
        }
      } catch { clearInterval(iv) }
    }, 3_000)
  }, [])

  const handleSend = async () => {
    if (!prompt.trim()) return
    let chatId = activeChatId
    if (!chatId) {
      const chat: Chat = { id: generateId(), title: 'New Chat', messages: [], createdAt: Date.now() }
      setChats(prev => [chat, ...prev])
      setActiveChatId(chat.id)
      chatId = chat.id
    }
    const userMsg: Message = { role: 'user', content: prompt, ts: Date.now() }
    appendMessage(chatId, userMsg)
    setPrompt('')
    setIsLoading(true)
    try {
      if (selectedTool === 'chat') {
        const currentMsgs = chats.find(c => c.id === chatId)?.messages ?? []
        const history = [...currentMsgs, userMsg].map(m => ({ role: m.role, content: m.content }))
        const res = await axios.post(`${API_BASE}/v1/chat/completions`, {
          model: selectedModel,
          messages: history,
        }, { headers })
        appendMessage(chatId, { role: 'assistant', content: res.data.choices[0].message.content, ts: Date.now() })
      } else {
        // If we have files to upload, upload them first and get file IDs
        let uploadedFileIds: string[] = [];
        if (['image', 'video'].includes(selectedTool) && selectedFiles.length > 0) {
          const formData = new FormData();
          // Create a temporary formdata to upload files
          selectedFiles.forEach((file, index) => {
            formData.append(`file`, file, file.name);
          });
          
          try {
            // Upload the files to the server
            const uploadResponse = await axios.post(`${API_BASE}/v1/files`, formData, { 
              headers: { ...headers, 'Content-Type': 'multipart/form-data' } 
            });
            
            // Extract file IDs from response (assuming each file upload returns an ID)
            // The API returns a list of file objects
            if (Array.isArray(uploadResponse.data)) {
              uploadedFileIds = uploadResponse.data.map((file: any) => file.id);
            } else if (uploadResponse.data && uploadResponse.data.id) {
              uploadedFileIds = [uploadResponse.data.id]; // single file
            }
          } catch (uploadError) {
            console.error('File upload failed:', uploadError);
          }
        }
        
        // Prepare request payload with reference files and account/model info
        const requestPayload: any = {
          prompt: userMsg.content,
          model: selectedModel,
          account_id: selectedAccountId !== 'auto' ? parseInt(selectedAccountId) : undefined,
          ...(selectedAdapter !== 'auto' ? { adapter: selectedAdapter } : {}),
        };
        
        // Add reference file IDs if available for image/video tools
        if (uploadedFileIds.length > 0) {
          requestPayload.reference_file_ids = uploadedFileIds;
        }
        
        const res = await axios.post(`${API_BASE}/native/tasks/${selectedTool}`, requestPayload, { headers })
        const jobId: string = res.data.job_id
        appendMessage(chatId, {
          role: 'assistant',
          content: `${selectedTool.charAt(0).toUpperCase() + selectedTool.slice(1)} job started (ID: ${jobId})…`,
          jobId,
          ts: Date.now(),
        })
        pollJob(chatId, jobId, selectedTool)
        
        // Clear selected files after successful submission
        if (uploadedFileIds.length > 0) {
          setSelectedFiles([]);
        }
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message
      toast.error(detail)
      const isAdapterError =
        typeof detail === 'string' &&
        (detail.includes('not available') || detail.includes('gemcli login'))
      const errorContent = isAdapterError
        ? `__ADAPTER_ERROR__${detail}`
        : `Error: ${detail}`
      appendMessage(chatId, { role: 'assistant', content: errorContent, ts: Date.now() })
    } finally {
      setIsLoading(false)
    }
  }

  // Render the appropriate panel based on selected tool
  const renderPanel = () => {
    if (!activeChat) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500 space-y-3">
          <Bot size={48} className="opacity-20" />
          <p className="text-sm">Select a tool and start chatting</p>
        </div>
      );
    }

    switch (selectedTool) {
      case 'chat':
        return <ChatPanel messages={activeChat.messages} isLoading={isLoading} />;
      case 'image':
        return <ImagePanel 
          messages={activeChat.messages} 
          isLoading={isLoading} 
          selectedFiles={selectedFiles}
          onFileSelect={setSelectedFiles}
        />;
      case 'video':
        return <VideoPanel 
          messages={activeChat.messages} 
          isLoading={isLoading} 
          selectedFiles={selectedFiles}
          onFileSelect={setSelectedFiles}
        />;
      default:
        // For music and research, we can reuse ImagePanel as it has similar display logic
        return <ImagePanel 
          messages={activeChat.messages} 
          isLoading={isLoading} 
          selectedFiles={selectedFiles}
          onFileSelect={setSelectedFiles}
        />;
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-3 border-b border-gray-200 dark:border-gray-700">
          <button onClick={newChat}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl font-medium text-sm transition">
            <Plus size={16} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {chats.length === 0 && <p className="text-xs text-gray-400 text-center mt-6">No chats yet</p>}
          {chats.map(c => (
            <div key={c.id} onClick={() => setActiveChatId(c.id)}
              className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition ${
                c.id === activeChatId
                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'
              }`}>
              <span className="text-xs truncate flex-1">{c.title}</span>
              <button onClick={e => { e.stopPropagation(); deleteChat(c.id) }}
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 ml-1 flex-shrink-0">
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-2 flex flex-wrap items-center gap-3">
          <div className="flex bg-gray-100 dark:bg-gray-800 rounded-xl p-1 gap-0.5">
            {TOOL_OPTIONS.map(t => (
              <button key={t.id} onClick={() => { setSelectedTool(t.id); setSelectedModel(DEFAULT_MODEL[t.id] ?? 'gemini-2.0-flash') }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  selectedTool === t.id
                    ? 'bg-white dark:bg-gray-700 text-blue-600 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                }`}>
                <t.icon size={13} /> {t.label}
              </button>
            ))}
          </div>

          <AccountSelector
            accounts={accounts}
            selectedAccountId={selectedAccountId}
            onSelect={setSelectedAccountId}
          />

          {['chat', 'image', 'video', 'music', 'research'].includes(selectedTool) && (
            <ModelSelector
              feature={selectedTool}
              accountId={selectedAccountId}
              accountProvider={selectedAccount?.provider}
              accountCapabilities={selectedAccount?.capabilities}
              models={models}
              selectedModel={selectedModel}
              onModelChange={setSelectedModel}
            />
          )}

          {selectedTool !== 'chat' && (
            <label className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="font-medium">Backend:</span>
              <select
                value={selectedAdapter}
                onChange={(e) => setSelectedAdapter(e.target.value)}
                className="bg-gray-100 dark:bg-gray-800 border-0 rounded-lg px-2 py-1.5 text-xs outline-none"
              >
                <option value="auto">Auto</option>
                <option value="webapi">webapi (gemini-webapi)</option>
                <option value="mcpcli">mcpcli (gemini-web-mcp-cli)</option>
              </select>
            </label>
          )}
          
          {['image', 'video'].includes(selectedTool) && (
            <div className="flex items-center gap-2">
              <FilePicker 
                onFileSelect={(files) => setSelectedFiles(prev => [...prev, ...files])}
                acceptedTypes={selectedTool === 'image' ? 'image/*' : 'image/*,video/*'}
                multiple={true}
              />
              {selectedFiles.length > 0 && (
                <div className="flex gap-1">
                  {selectedFiles.slice(0, 2).map((file, index) => (
                    <span key={index} className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 rounded">
                      {file.name.substring(0, 8)}...
                    </span>
                  ))}
                  {selectedFiles.length > 2 && (
                    <span className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 rounded">
                      +{selectedFiles.length - 2}
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Messages */}
        {renderPanel()}
        <div ref={bottomRef} />

        {/* Input */}
        <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-4">
          <div className="flex items-end gap-3 bg-gray-50 dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 px-4 py-3 focus-within:ring-2 focus-within:ring-blue-500 transition">
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
              disabled={isLoading}
              rows={1}
              placeholder={selectedTool === 'chat' ? 'Message… (Enter to send)' : `Describe the ${selectedTool} to generate…`}
              className="flex-1 bg-transparent outline-none resize-none text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 leading-relaxed max-h-40 overflow-y-auto"
            />
            <button onClick={handleSend} disabled={isLoading || !prompt.trim()}
              className="w-9 h-9 flex items-center justify-center rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white transition flex-shrink-0">
              {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">Chat history is kept per session in browser storage</p>
        </div>
      </div>
    </div>
  )
}

export default Playground
