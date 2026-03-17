import React, { useState } from 'react';
import { Bot, User, Loader2, Image as ImageIcon, AlertTriangle } from 'lucide-react';
import FilePicker from './FilePicker';

const ADAPTER_ERROR_PREFIX = '__ADAPTER_ERROR__';

function AdapterErrorCard({ message }: { message: string }) {
  return (
    <div className="max-w-[72%] rounded-2xl px-4 py-3 text-sm border-2 border-red-400 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 shadow-sm">
      <div className="flex items-center gap-2 font-semibold mb-1">
        <AlertTriangle size={15} className="text-red-500 flex-shrink-0" />
        <span>Image Generation Error</span>
      </div>
      <p className="whitespace-pre-wrap leading-relaxed">{message}</p>
      <p className="mt-2 text-xs text-red-600 dark:text-red-300 italic">
        Run <code className="font-mono bg-red-100 dark:bg-red-900/40 px-1 rounded">gemcli login</code> in Terminal to enable Imagen 3.0 via mcpcli.
      </p>
    </div>
  );
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  imageUrl?: string;
  jobId?: string;
  ts: number;
}

interface ImagePanelProps {
  messages: Message[];
  isLoading: boolean;
  selectedFiles?: File[];
  onFileSelect?: (files: File[]) => void;
}

const ImagePanel: React.FC<ImagePanelProps> = ({ messages, isLoading, selectedFiles = [], onFileSelect }) => {
  const [expandedImage, setExpandedImage] = useState<string | null>(null);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500 space-y-3">
          <ImageIcon size={48} className="opacity-20" />
          <p className="text-sm">Generate images with Gemini</p>
        </div>
      ) : (
        messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center flex-shrink-0 mt-0.5">
                <ImageIcon size={16} className="text-blue-600 dark:text-blue-400" />
              </div>
            )}
            {msg.role === 'assistant' && msg.content.startsWith(ADAPTER_ERROR_PREFIX) ? (
              <AdapterErrorCard message={msg.content.slice(ADAPTER_ERROR_PREFIX.length)} />
            ) : (
              <div
                className={`max-w-[72%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-sm shadow-sm'
                }`}
              >
                {msg.content}
                {msg.imageUrl && (msg.imageUrl.startsWith('http') || msg.imageUrl.startsWith('/')) && (
                  <img
                    src={msg.imageUrl.startsWith("mock://") ? "https://placehold.co/600x400/png?text=Mock+Image+Generated" : msg.imageUrl}
                    alt="generated"
                    className="mt-3 rounded-xl max-w-full max-h-64 object-contain cursor-pointer"
                    onClick={() => setExpandedImage(msg.imageUrl!)}
                  />
                )}
                {msg.jobId && !msg.imageUrl && msg.content.includes('job started') && (
                  <div className="flex items-center gap-2 mt-2 text-xs opacity-60">
                    <Loader2 size={11} className="animate-spin" /> Generating image...
                  </div>
                )}
              </div>
            )}
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                <User size={16} className="text-gray-600 dark:text-gray-400" />
              </div>
            )}
          </div>
        ))
      )}
      
      {selectedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          {selectedFiles.map((file, index) => (
            <div key={index} className="flex items-center gap-2 bg-white dark:bg-gray-700 px-3 py-2 rounded-md shadow-sm">
              <span className="text-sm truncate max-w-xs">{file.name}</span>
            </div>
          ))}
        </div>
      )}
      
      {isLoading && (
        <div className="flex gap-3 justify-start">
          <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center flex-shrink-0 mt-0.5">
            <ImageIcon size={16} className="text-blue-600 dark:text-blue-400" />
          </div>
          <div className="max-w-[72%] rounded-2xl px-4 py-3 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-sm shadow-sm">
            <div className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" /> Generating image...
            </div>
          </div>
        </div>
      )}

      {/* Modal for expanded image */}
      {expandedImage && (
        <div 
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setExpandedImage(null)}
        >
          <img 
            src={expandedImage} 
            alt="expanded" 
            className="max-w-full max-h-full object-contain"
          />
        </div>
      )}
    </div>
  );
};

export default ImagePanel;