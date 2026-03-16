import React, { useState } from 'react';
import { Bot, User, Loader2, Video } from 'lucide-react';
import FilePicker from './FilePicker';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  imageUrl?: string;
  jobId?: string;
  ts: number;
}

interface VideoPanelProps {
  messages: Message[];
  isLoading: boolean;
  selectedFiles?: File[];
  onFileSelect?: (files: File[]) => void;
}

const VideoPanel: React.FC<VideoPanelProps> = ({ messages, isLoading, selectedFiles = [], onFileSelect }) => {
  const [expandedVideo, setExpandedVideo] = useState<string | null>(null);
  const [expandedImage, setExpandedImage] = useState<string | null>(null);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500 space-y-3">
          <Video size={48} className="opacity-20" />
          <p className="text-sm">Generate videos with Gemini</p>
        </div>
      ) : (
        messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Video size={16} className="text-purple-600 dark:text-purple-400" />
              </div>
            )}
            <div 
              className={`max-w-[72%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-purple-600 text-white rounded-br-sm'
                  : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-sm shadow-sm'
              }`}
            >
              {msg.content}
              {msg.imageUrl && (
                <>
                  {(msg.imageUrl.split('.').pop()?.toLowerCase() || '').match(/^(mp4|webm|ogg)$/) ? (
                    <video 
                      src={msg.imageUrl} 
                      controls 
                      className="mt-3 rounded-xl max-w-full max-h-64 object-contain"
                      onClick={() => setExpandedVideo(msg.imageUrl!)}
                    />
                  ) : (
                    <img 
                      src={msg.imageUrl} 
                      alt="generated" 
                      className="mt-3 rounded-xl max-w-full max-h-64 object-contain cursor-pointer"
                      onClick={() => setExpandedImage(msg.imageUrl!)}
                    />
                  )}
                </>
              )}
              {msg.jobId && !msg.imageUrl && msg.content.includes('job started') && (
                <div className="flex items-center gap-2 mt-2 text-xs opacity-60">
                  <Loader2 size={11} className="animate-spin" /> Generating video...
                </div>
              )}
            </div>
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
          <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center flex-shrink-0 mt-0.5">
            <Video size={16} className="text-purple-600 dark:text-purple-400" />
          </div>
          <div className="max-w-[72%] rounded-2xl px-4 py-3 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-sm shadow-sm">
            <div className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" /> Generating video...
            </div>
          </div>
        </div>
      )}

      {/* Modal for expanded video */}
      {expandedVideo && (
        <div 
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setExpandedVideo(null)}
        >
          <video 
            src={expandedVideo} 
            controls 
            className="max-w-full max-h-full object-contain"
          />
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

export default VideoPanel;