import React, { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { BookOpen, Settings, Code2 } from 'lucide-react'

const TABS = [
  { id: 'configuration', label: 'Configuration', icon: Settings, file: '/docs/CONFIGURATION.md' },
  { id: 'api', label: 'API Reference', icon: Code2, file: '/docs/API.md' },
]

const Docs = () => {
  const [activeTab, setActiveTab] = useState('configuration')
  const [content, setContent] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const tab = TABS.find(t => t.id === activeTab)!

  useEffect(() => {
    setIsLoading(true)
    fetch(tab.file)
      .then(r => r.text())
      .then(text => { setContent(text); setIsLoading(false) })
      .catch(() => { setContent('Failed to load documentation.'); setIsLoading(false) })
  }, [activeTab])

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <BookOpen className="text-blue-600" size={28} /> Documentation
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1 text-sm">Configuration guides and API reference</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl w-fit">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === t.id
                ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <t.icon size={15} /> {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6 md:p-8">
        {isLoading ? (
          <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Loading…</div>
        ) : (
          <div className="prose prose-sm md:prose dark:prose-invert max-w-none
            prose-headings:font-bold prose-headings:text-gray-900 dark:prose-headings:text-white
            prose-a:text-blue-600 dark:prose-a:text-blue-400
            prose-code:bg-gray-100 dark:prose-code:bg-gray-700 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
            prose-pre:bg-gray-900 dark:prose-pre:bg-gray-950 prose-pre:rounded-xl
            prose-table:text-sm prose-th:bg-gray-50 dark:prose-th:bg-gray-700/50
            prose-hr:border-gray-200 dark:prose-hr:border-gray-700">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

export default Docs
