import React, { useEffect, useState } from 'react';
import { Zap, Loader2 } from 'lucide-react';
import { modelApi } from '../../lib/api';

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
  accountId,
  models = [],
  selectedModel = 'gemini-2.0-flash',
  onModelChange 
}) => {
  const [filteredModels, setFilteredModels] = useState<ModelItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!['chat', 'image', 'video'].includes(feature)) return;

    let isMounted = true;
    
    const fetchModels = async () => {
      setIsLoading(true);
      try {
        if (accountId && accountId !== 'auto') {
          const res = await modelApi.getModelsByAccountAndFeature(accountId, feature);
          if (isMounted) {
            setFilteredModels(res.data || []);
            if (res.data && res.data.length > 0 && onModelChange) {
              if (!res.data.find((m: ModelItem) => m.provider_model_name === selectedModel)) {
                onModelChange(res.data[0].provider_model_name);
              }
            }
          }
        } else {
          const fallback = models.filter(m => {
            if (feature === 'image') return m.family === 'image' || m.provider_model_name.includes('vision') || m.provider_model_name.includes('flash');
            if (feature === 'video') return m.provider_model_name.includes('video') || m.provider_model_name.includes('pro') || m.provider_model_name.includes('flash');
            return true;
          });
          if (isMounted) {
            setFilteredModels(fallback);
            if (fallback.length > 0 && onModelChange && !fallback.find((m: ModelItem) => m.provider_model_name === selectedModel)) {
              onModelChange(fallback[0].provider_model_name);
            }
          }
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load models:', err);
          setFilteredModels([]);
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchModels();
    return () => { isMounted = false; };
  }, [accountId, feature, models]);

  if (!['chat', 'image', 'video'].includes(feature)) return null;

  if (isLoading) {
    return (
      <label className="flex items-center gap-1.5 text-xs text-gray-500">
        <Loader2 size={12} className="animate-spin text-blue-500" />
        <span>Loading models...</span>
      </label>
    );
  }

  if (filteredModels.length === 0) {
    return (
      <label className="flex items-center gap-1.5 text-xs text-red-500">
        <Zap size={12} />
        <span>No {feature} models</span>
      </label>
    );
  }

  return (
    <label className="flex items-center gap-1.5 text-xs text-gray-500">
      <Zap size={12} className="text-yellow-500" />
      <span className="font-medium">Model:</span>
      <select 
        value={selectedModel}
        onChange={(e) => onModelChange?.(e.target.value)}
        className="bg-gray-100 dark:bg-gray-800 border-0 rounded-lg px-2 py-1.5 text-xs outline-none max-w-[180px]"
      >
        {filteredModels.map(model => (
          <option key={model.id} value={model.provider_model_name}>
            {model.display_name}
          </option>
        ))}
      </select>
    </label>
  );
};

export default ModelSelector;
