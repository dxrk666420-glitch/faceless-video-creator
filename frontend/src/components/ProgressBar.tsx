'use client';

import { useEffect, useState } from 'react';
import { getJobStatus } from '@/lib/api';

interface ProgressBarProps {
  taskId: string;
  onComplete?: (result: any) => void;
  onError?: (message: string) => void;
}

export default function ProgressBar({ taskId, onComplete, onError }: ProgressBarProps) {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('Starting...');

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const data = await getJobStatus(taskId);
        setStatus(data.status);
        setProgress(data.progress);
        setMessage(data.message);

        if (data.status === 'completed') {
          clearInterval(interval);
          onComplete?.(data.result);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          onError?.(data.message);
        }
      } catch {
        // ignore polling errors
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [taskId, onComplete, onError]);

  const barColor =
    status === 'failed'
      ? 'bg-red-500'
      : status === 'completed'
        ? 'bg-green-500'
        : 'bg-brand-500';

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-400">{message}</span>
        <span className="text-gray-500">{Math.round(progress)}%</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
