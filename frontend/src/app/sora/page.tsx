'use client';

import { useState, useCallback } from 'react';
import { generateSoraVideo } from '@/lib/api';
import ProgressBar from '@/components/ProgressBar';
import VideoPreview from '@/components/VideoPreview';

export default function SoraPage() {
  const [prompt, setPrompt] = useState('');
  const [duration, setDuration] = useState(5);
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [generating, setGenerating] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [resultVideo, setResultVideo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setGenerating(true);
    setError(null);
    setResultVideo(null);

    try {
      const data = await generateSoraVideo({ prompt, duration, aspect_ratio: aspectRatio });
      setTaskId(data.task_id);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Failed to start generation');
      setGenerating(false);
    }
  };

  const onComplete = useCallback((result: any) => {
    setGenerating(false);
    if (result?.file_path) setResultVideo(result.file_path);
  }, []);

  const onError = useCallback((msg: string) => {
    setGenerating(false);
    setError(msg);
  }, []);

  const promptSuggestions = [
    'A drone flying over a neon-lit cyberpunk city at night, rain reflecting on the streets',
    'Slow motion of ocean waves crashing on a beach at golden hour, cinematic',
    'A magical forest with glowing mushrooms and fireflies floating through the air',
    'Time-lapse of a busy city intersection transitioning from day to night',
    'An astronaut floating in space with Earth in the background, serene and peaceful',
  ];

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-1">AI Video Generator (Sora)</h1>
      <p className="text-gray-400 text-sm mb-6">
        Generate stunning videos from text descriptions using OpenAI Sora
      </p>

      <div className="space-y-4">
        {/* Prompt input */}
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Describe your video</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the video you want to create..."
            rows={4}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm resize-none focus:border-brand-500 focus:outline-none"
          />
        </div>

        {/* Prompt suggestions */}
        <div className="flex flex-wrap gap-2">
          {promptSuggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => setPrompt(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-gray-700 text-gray-400 hover:border-gray-500 hover:text-white transition-colors"
            >
              {s.slice(0, 50)}...
            </button>
          ))}
        </div>

        {/* Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Duration (seconds)</label>
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm"
            >
              <option value={5}>5 seconds</option>
              <option value={10}>10 seconds</option>
              <option value={15}>15 seconds</option>
              <option value={20}>20 seconds</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Aspect Ratio</label>
            <div className="flex gap-2">
              {['9:16', '16:9', '1:1'].map((ratio) => (
                <button
                  key={ratio}
                  onClick={() => setAspectRatio(ratio)}
                  className={`flex-1 px-3 py-2 rounded-lg text-sm border transition-all ${
                    aspectRatio === ratio
                      ? 'border-brand-500 bg-brand-500/20 text-brand-400'
                      : 'border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-500'
                  }`}
                >
                  {ratio}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Generate */}
        <button
          onClick={handleGenerate}
          disabled={generating || !prompt.trim()}
          className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 py-3 rounded-lg font-medium transition-all disabled:opacity-50"
        >
          {generating ? 'Generating with Sora...' : 'Generate Video'}
        </button>

        {/* Note about API key */}
        <p className="text-xs text-gray-600 text-center">
          Requires OPENAI_API_KEY to be set in backend .env
        </p>

        {/* Progress */}
        {taskId && generating && (
          <ProgressBar taskId={taskId} onComplete={onComplete} onError={onError} />
        )}

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
            {error}
          </div>
        )}

        {resultVideo && <VideoPreview filename={resultVideo} title={prompt.slice(0, 80)} />}
      </div>
    </div>
  );
}
