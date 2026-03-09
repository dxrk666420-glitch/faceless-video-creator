'use client';

import { useState, useCallback } from 'react';
import { uploadVideo, analyzeVideo, generateClips, getProject } from '@/lib/api';
import FileUploader from '@/components/FileUploader';
import ProgressBar from '@/components/ProgressBar';
import VideoPreview from '@/components/VideoPreview';

interface Clip {
  start: number;
  end: number;
  title: string;
  text: string;
  score: number;
  selected: boolean;
}

export default function ClipperPage() {
  const [step, setStep] = useState<'upload' | 'analyzing' | 'select' | 'generating' | 'done'>('upload');
  const [projectId, setProjectId] = useState<number | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [videoInfo, setVideoInfo] = useState<any>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [resultVideos, setResultVideos] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [addCaptions, setAddCaptions] = useState(true);

  const handleUpload = async (file: File) => {
    setError(null);
    try {
      const data = await uploadVideo(file);
      setProjectId(data.project_id);
      setVideoInfo(data.video_info);

      // Start analysis
      setStep('analyzing');
      const analysisData = await analyzeVideo(data.project_id);
      setTaskId(analysisData.task_id);
    } catch (e: any) {
      setError(e.message || 'Upload failed');
    }
  };

  const onAnalysisComplete = useCallback(
    async (result: any) => {
      if (result?.clips) {
        setClips(result.clips.map((c: any) => ({ ...c, selected: true })));
      } else if (projectId) {
        // Fetch from project config
        const project = await getProject(projectId);
        const projectClips = project.config?.clips || [];
        setClips(projectClips.map((c: any) => ({ ...c, selected: true })));
      }
      setStep('select');
    },
    [projectId]
  );

  const toggleClip = (idx: number) => {
    setClips((prev) =>
      prev.map((c, i) => (i === idx ? { ...c, selected: !c.selected } : c))
    );
  };

  const handleGenerate = async () => {
    if (!projectId) return;
    const selectedClips = clips.filter((c) => c.selected);
    if (selectedClips.length === 0) return;

    setStep('generating');
    setError(null);

    try {
      const data = await generateClips(projectId, {
        clips: selectedClips.map((c) => ({ start: c.start, end: c.end, title: c.title })),
        add_captions: addCaptions,
        aspect_ratio: '9:16',
      });
      setTaskId(data.task_id);
    } catch (e: any) {
      setError(e.message || 'Generation failed');
      setStep('select');
    }
  };

  const onGenerationComplete = useCallback(
    async () => {
      if (projectId) {
        const project = await getProject(projectId);
        setResultVideos(project.videos || []);
      }
      setStep('done');
    },
    [projectId]
  );

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold mb-1">Auto Video Clipper</h1>
      <p className="text-gray-400 text-sm mb-6">
        Upload long-form videos and let AI find the best moments for short-form content
      </p>

      {/* Step: Upload */}
      {step === 'upload' && (
        <FileUploader
          onFileSelect={handleUpload}
          accept="video/*"
          label="Drag and drop a video file (MP4, MOV, AVI), or click to browse"
        />
      )}

      {/* Step: Analyzing */}
      {step === 'analyzing' && taskId && (
        <div className="space-y-4">
          {videoInfo && (
            <div className="p-4 bg-gray-900/50 border border-gray-800 rounded-lg text-sm">
              <span className="text-gray-400">Duration: </span>
              <span>{formatTime(videoInfo.duration)}</span>
              <span className="text-gray-600 mx-2">&middot;</span>
              <span className="text-gray-400">Resolution: </span>
              <span>
                {videoInfo.width}x{videoInfo.height}
              </span>
              <span className="text-gray-600 mx-2">&middot;</span>
              <span className="text-gray-400">Size: </span>
              <span>{videoInfo.size_mb} MB</span>
            </div>
          )}
          <ProgressBar
            taskId={taskId}
            onComplete={onAnalysisComplete}
            onError={(msg) => {
              setError(msg);
              setStep('upload');
            }}
          />
        </div>
      )}

      {/* Step: Select clips */}
      {step === 'select' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Found {clips.length} potential clips
            </h2>
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={addCaptions}
                onChange={(e) => setAddCaptions(e.target.checked)}
                className="rounded"
              />
              Add captions
            </label>
          </div>

          <div className="space-y-2">
            {clips.map((clip, i) => (
              <div
                key={i}
                onClick={() => toggleClip(i)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  clip.selected
                    ? 'border-brand-500 bg-brand-500/10'
                    : 'border-gray-800 bg-gray-900/50 opacity-50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={clip.selected}
                      readOnly
                      className="rounded"
                    />
                    <span className="text-sm font-medium">Clip {i + 1}</span>
                    <span className="text-xs text-gray-500">
                      {formatTime(clip.start)} — {formatTime(clip.end)} (
                      {Math.round(clip.end - clip.start)}s)
                    </span>
                  </div>
                  <span className="text-xs text-brand-400">Score: {clip.score}</span>
                </div>
                <p className="text-xs text-gray-500 line-clamp-2">{clip.text || clip.title}</p>
              </div>
            ))}
          </div>

          <button
            onClick={handleGenerate}
            disabled={clips.filter((c) => c.selected).length === 0}
            className="w-full bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 py-3 rounded-lg font-medium transition-all disabled:opacity-50"
          >
            Generate {clips.filter((c) => c.selected).length} Clips
          </button>
        </div>
      )}

      {/* Step: Generating */}
      {step === 'generating' && taskId && (
        <ProgressBar
          taskId={taskId}
          onComplete={onGenerationComplete}
          onError={(msg) => {
            setError(msg);
            setStep('select');
          }}
        />
      )}

      {/* Step: Done */}
      {step === 'done' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-green-400">
            Generated {resultVideos.length} clips!
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {resultVideos.map((v: any) => (
              <VideoPreview key={v.id} filename={v.file_path} title={v.title} />
            ))}
          </div>
          <button
            onClick={() => {
              setStep('upload');
              setClips([]);
              setResultVideos([]);
              setProjectId(null);
            }}
            className="text-sm text-brand-400 hover:text-brand-300"
          >
            Clip another video
          </button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}
    </div>
  );
}
