import React from 'react';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface JobStatusCardProps {
  jobId?: string;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  message: string;
}

const JobStatusCard: React.FC<JobStatusCardProps> = ({ 
  jobId, 
  status = 'pending', 
  progress = 0, 
  message 
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'failed':
        return <AlertCircle size={16} className="text-red-500" />;
      default:
        return <Loader2 size={16} className="animate-spin text-blue-500" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300';
      default:
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300';
    }
  };

  return (
    <div className={`flex items-center gap-2 p-3 rounded-lg ${getStatusColor()} text-xs`}>
      {getStatusIcon()}
      <span>{message}</span>
      {jobId && <span className="ml-auto text-xs opacity-70">Job: {jobId}</span>}
    </div>
  );
};

export default JobStatusCard;