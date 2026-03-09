'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  searchRedditStories,
  getRedditVoices,
  getSubreddits,
  generateRedditVideo,
} from '@/lib/api';
import ProgressBar from '@/components/ProgressBar';
import VideoPreview from '@/components/VideoPreview';

export default function RedditPage() {
  const [stories, setStories] = useState<any[]>([]);
  const [voices, setVoices] = useState<any[]>([]);
  const [subreddits, setSubreddits] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // Search params
  const [subreddit, setSubreddit] = useState('AskReddit');
  const [sort, setSort] = useState('hot');

  // Selected story
  const [selectedStory, setSelectedStory] = useState<any>(null);

  // Generation settings
  const [voice, setVoice] = useState('en-US-ChristopherNeural');
  const [bgCategory, setBgCategory] = useState('satisfying');
  const [highlightColor, setHighlightColor] = useState('#FFD700');

  // Generation state
  const [taskId, setTaskId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [resultVideo, setResultVideo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSubreddits().then(setSubreddits).catch(() => {});
    getRedditVoices()
      .then((v) => setVoices(v.slice(0, 30)))
      .catch(() => {});
    handleSearch();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await searchRedditStories({ subreddit, sort, limit: 20 });
      setStories(data);
    } catch {
      setStories([]);
    }
    setLoading(false);
  };

  const handleGenerate = async () => {
    if (!selectedStory) return;
    setGenerating(true);
    setError(null);
    setResultVideo(null);

    try {
      const data = await generateRedditVideo({
        story_title: selectedStory.title,
        story_text: selectedStory.selftext,
        voice,
        background_category: bgCategory,
        highlight_color: highlightColor,
      });
      setTaskId(data.task_id);
    } catch (e: any) {
      setError(e.message || 'Failed to start generation');
      setGenerating(false);
    }
  };

  const onComplete = useCallback((result: any) => {
    setGenerating(false);
    if (result?.file_path) {
      setResultVideo(result.file_path);
    }
  }, []);

  const onError = useCallback((msg: string) => {
    setGenerating(false);
    setError(msg);
  }, []);

  return (
    <div className="max-w-6xl">
      <h1 className="text-2xl font-bold mb-1">Reddit Story Videos</h1>
      <p className="text-gray-400 text-sm mb-6">
        Turn viral Reddit stories into engaging narrated videos with word-by-word captions
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Story browser */}
        <div>
          {/* Search bar */}
          <div className="flex gap-2 mb-4">
            <select
              value={subreddit}
              onChange={(e) => setSubreddit(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm flex-1"
            >
              {subreddits.map((s) => (
                <option key={s} value={s}>
                  r/{s}
                </option>
              ))}
            </select>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm"
            >
              <option value="hot">Hot</option>
              <option value="top">Top</option>
              <option value="new">New</option>
            </select>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="bg-brand-500 hover:bg-brand-600 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Search'}
            </button>
          </div>

          {/* Story list */}
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
            {stories.map((story) => (
              <div
                key={story.id}
                onClick={() => setSelectedStory(story)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedStory?.id === story.id
                    ? 'border-brand-500 bg-brand-500/10'
                    : 'border-gray-800 bg-gray-900/50 hover:border-gray-600'
                }`}
              >
                <h3 className="text-sm font-medium mb-1 line-clamp-2">{story.title}</h3>
                <p className="text-xs text-gray-500 line-clamp-2">{story.selftext}</p>
                <div className="flex gap-3 mt-2 text-xs text-gray-600">
                  <span>r/{story.subreddit}</span>
                  <span>{story.score?.toLocaleString()} pts</span>
                  <span>{story.num_comments?.toLocaleString()} comments</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Settings + Generate */}
        <div>
          {selectedStory ? (
            <div className="space-y-4">
              <div className="p-4 bg-gray-900/50 border border-gray-800 rounded-lg">
                <h3 className="font-medium mb-2">{selectedStory.title}</h3>
                <p className="text-sm text-gray-400 max-h-40 overflow-y-auto">
                  {selectedStory.selftext}
                </p>
              </div>

              {/* Voice selection */}
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Voice</label>
                <select
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm"
                >
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name} ({v.gender})
                    </option>
                  ))}
                  {voices.length === 0 && (
                    <option value="en-US-ChristopherNeural">Christopher (Male)</option>
                  )}
                </select>
              </div>

              {/* Background category */}
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Background Style</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'minecraft', label: 'Minecraft' },
                    { id: 'subway_surfers', label: 'Subway Surfers' },
                    { id: 'satisfying', label: 'Satisfying' },
                  ].map((bg) => (
                    <button
                      key={bg.id}
                      onClick={() => setBgCategory(bg.id)}
                      className={`px-3 py-2 rounded-lg text-sm border transition-all ${
                        bgCategory === bg.id
                          ? 'border-brand-500 bg-brand-500/20 text-brand-400'
                          : 'border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {bg.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Highlight color */}
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Caption Highlight Color</label>
                <div className="flex gap-2">
                  {['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#FF69B4'].map((color) => (
                    <button
                      key={color}
                      onClick={() => setHighlightColor(color)}
                      className={`w-8 h-8 rounded-full border-2 transition-all ${
                        highlightColor === color ? 'border-white scale-110' : 'border-transparent'
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>

              {/* Generate button */}
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-600 hover:to-purple-600 py-3 rounded-lg font-medium transition-all disabled:opacity-50"
              >
                {generating ? 'Generating...' : 'Generate Video'}
              </button>

              {/* Progress */}
              {taskId && generating && (
                <ProgressBar taskId={taskId} onComplete={onComplete} onError={onError} />
              )}

              {/* Error */}
              {error && (
                <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
                  {error}
                </div>
              )}

              {/* Result */}
              {resultVideo && <VideoPreview filename={resultVideo} title={selectedStory.title} />}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-600 text-sm border border-gray-800 rounded-lg border-dashed">
              Select a story from the left to get started
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
