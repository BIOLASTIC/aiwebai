import React from 'react';
import { Zap } from 'lucide-react';

interface ModelItem {
  id: number;
  provider_model_name: string;
  display_name: string;
  family: string;
}

interface ModelSelectorProps {
  feature: string;
  accountId: string;
  models?: ModelItem[];
  selectedModel?: string;
  onModelChange?: (model: string) => void;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ 
  feature, 
  models = [],
  selectedModel = 'gemini-2.0-flash',
  onModelChange 
}) => {
  // Show model selector for chat, image, and video features
  if (!['chat', 'image', 'video'].includes(feature)) return null;

  return (
    <label className="flex items-center gap-1.5 text-xs text-gray-500">
      <Zap size={12} className="text-yellow-500" />
      <span className="font-medium">Model:</span>
      <select 
        value={selectedModel}
        onChange={(e) => onModelChange?.(e.target.value)}
        className="bg-gray-100 dark:bg-gray-800 border-0 rounded-lg px-2 py-1.5 text-xs outline-none max-w-[180px]"
      >
        {models.length > 0
          ? models.map(model => (
              <option key={model.id} value={model.provider_model_name}>
                {model.display_name}
              </option>
            ))
          : (
            <>
              <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
              <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
              <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
            </>
          )}
      </select>
    </label>
  );
};

export default ModelSelector;