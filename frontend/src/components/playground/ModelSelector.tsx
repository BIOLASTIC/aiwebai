import React, { useEffect, useState } from 'react';
import { Zap, Loader2 } from 'lucide-react';
import { modelApi } from '../../lib/api';

interface AccountCapabilities {
  chat?: boolean;
  image?: boolean;
  video?: boolean;
  music?: boolean;
  research?: boolean;
}

interface ModelItem {
  id: number;
  provider_model_name: string;
  display_name: string;
  family: string;
  source_provider?: string;
  capabilities?: Record<string, boolean>;
}

interface ModelSelectorProps {
  feature: string;
  accountId: string;
  accountProvider?: string;
  accountCapabilities?: AccountCapabilities;
  models?: ModelItem[];
  selectedModel?: string;
  onModelChange?: (model: string) => void;
}

const PROVIDER_LIB: Record<string, string> = {
  webapi: 'gemini-webapi',
  mcpcli: 'gemini-web-mcp-cli',
};

function sourceProviderBadge(source?: string) {
  if (!source) return null;
  const isWebapi = source === 'webapi';
  return (
    <span
      className={`ml-1 px-1 py-0.5 rounded text-[10px] font-semibold ${
        isWebapi
          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
          : 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300'
      }`}
    >
      {isWebapi ? 'webapi' : 'mcpcli'}
    </span>
  );
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  feature,
  accountId,
  accountProvider,
  accountCapabilities,
  models = [],
  selectedModel = 'gemini-3.0-flash',
  onModelChange,
}) => {
  const [filteredModels, setFilteredModels] = useState<ModelItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const SUPPORTED_FEATURES = ['chat', 'image', 'video', 'music', 'research'];

  useEffect(() => {
    if (!SUPPORTED_FEATURES.includes(feature)) return;

    let isMounted = true;

    const fetchModels = async () => {
      setIsLoading(true);
      try {
        if (accountId && accountId !== 'auto') {
          const res = await modelApi.getModelsByAccountAndFeature(accountId, feature);
          if (isMounted) {
            let data: ModelItem[] = res.data || [];

            // Filter by account provider if it is webapi — webapi only supports chat+image
            if (accountProvider === 'webapi') {
              const webapiCapFeatures = ['chat', 'image'];
              if (!webapiCapFeatures.includes(feature)) {
                data = [];
              }
            }

            setFilteredModels(data);
            if (data.length > 0 && onModelChange) {
              if (!data.find((m) => m.provider_model_name === selectedModel)) {
                onModelChange(data[0].provider_model_name);
              }
            }
          }
        } else {
          // fallback: filter from provided models list by feature capability
          const fallback = models.filter((m) => {
            if (feature === 'image') {
              const caps = m.capabilities || {};
              return caps.images === true;
            }
            if (feature === 'video') {
              return (
                m.provider_model_name.includes('veo') ||
                m.provider_model_name.includes('video')
              );
            }
            if (feature === 'music') {
              return (
                m.provider_model_name.includes('lyria') ||
                m.provider_model_name.includes('music')
              );
            }
            if (feature === 'research') {
              return (
                m.provider_model_name.includes('research')
              );
            }
            return true;
          });
          // Sort: mcpcli dedicated models first (imagen-3.0, veo-2.0, lyria-1.0)
          fallback.sort((a, b) => {
            const aIsDedicated = a.provider_model_name.includes('imagen') || a.provider_model_name.includes('veo') || a.provider_model_name.includes('lyria');
            const bIsDedicated = b.provider_model_name.includes('imagen') || b.provider_model_name.includes('veo') || b.provider_model_name.includes('lyria');
            if (aIsDedicated && !bIsDedicated) return -1;
            if (!aIsDedicated && bIsDedicated) return 1;
            return 0;
          });
          if (isMounted) {
            setFilteredModels(fallback);
            if (
              fallback.length > 0 &&
              onModelChange &&
              !fallback.find((m) => m.provider_model_name === selectedModel)
            ) {
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
    return () => {
      isMounted = false;
    };
  }, [accountId, accountProvider, feature, models]);

  if (!SUPPORTED_FEATURES.includes(feature)) return null;

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

  const selectedModelData = filteredModels.find(
    (m) => m.provider_model_name === selectedModel
  );
  const selectedSource = selectedModelData?.source_provider;
  const libName = selectedSource ? PROVIDER_LIB[selectedSource] : undefined;

  return (
    <label className="flex items-center gap-1.5 text-xs text-gray-500">
      <Zap size={12} className="text-yellow-500" />
      <span className="font-medium">Model:</span>
      <select
        value={selectedModel}
        onChange={(e) => onModelChange?.(e.target.value)}
        className="bg-gray-100 dark:bg-gray-800 border-0 rounded-lg px-2 py-1.5 text-xs outline-none max-w-[180px]"
        title={libName ? `Uses ${libName}` : undefined}
      >
        {filteredModels.map((model) => (
          <option key={model.id} value={model.provider_model_name}>
            {model.display_name}
            {model.source_provider
              ? ` [${model.source_provider === 'webapi' ? 'webapi' : 'mcpcli'}]`
              : ''}
          </option>
        ))}
      </select>
      {selectedSource && sourceProviderBadge(selectedSource)}
      {libName && (
        <span className="text-gray-400 italic hidden sm:inline">
          via {libName}
        </span>
      )}
    </label>
  );
};

export default ModelSelector;
