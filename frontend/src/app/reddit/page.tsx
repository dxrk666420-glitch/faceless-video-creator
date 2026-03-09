'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  searchRedditStories,
  getRedditVoices,
  getSubreddits,
  generateRedditVideo,
  getStoryStyles,
  generateAIStory,
} from '@/lib/api';
import ProgressBar from '@/components/ProgressBar';
import VideoPreview from '@/components/VideoPreview';

type Tab = 'paste' | 'ai' | 'browse';

export default function RedditPage() {
  const [tab, setTab] = useState<Tab>('paste');
  const [voices, setVoices] = useState<any[]>([]);

  // --- Paste tab ---
  const [pasteTitle, setPasteTitle] = useState('');
  const [pasteText, setPasteText] = useState('');

  // --- AI Generate tab ---
  const [storyStyles, setStoryStyles] = useState<any[]>([]);
  const [aiStyle, setAiStyle] = useState('reddit_tifu');
  const [aiTopic, setAiTopic] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiTitle, setAiTitle] = useState('');
  const [aiText, setAiText] = useState('');

  // --- Browse tab ---
  const [stories, setStories] = useState<any[]>([]);
  const [subreddits, setSubreddits] = useState<string[]>([]);
  const [subreddit, setSubreddit] = useState('AskReddit');
  const [sort, setSort] = useState('hot');
  const [browseLoading, setBrowseLoading] = useState(false);

  // --- Shared: selected story for generation ---
  const [storyTitle, setStoryTitle] = useState('');
  const [storyText, setStoryText] = useState('');

  // --- Generation settings ---
  const [voice, setVoice] = useState('en-US-ChristopherNeural');
  const [bgCategory, setBgCategory] = useState('satisfying');
  const [highlightColor, setHighlightColor] = useState('#FFD700');

  // --- Generation state ---
  const [taskId, setTaskId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [resultVideo, setResultVideo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRedditVoices()
      .then((v) => setVoices(v.slice(0, 30)))
      .catch(() => {});
    getStoryStyles().then(setStoryStyles).catch(() => {});
    getSubreddits().then(setSubreddits).catch(() => {});
  }, []);

  // Sync paste fields to shared story
  useEffect(() => {
    if (tab === 'paste') {
      setStoryTitle(pasteTitle);
      setStoryText(pasteText);
    }
  }, [tab, pasteTitle, pasteText]);

  // --- AI Generate ---
  const handleAIGenerate = async () => {
    setAiLoading(true);
    setError(null);
    try {
      const data = await generateAIStory({ topic: aiTopic, style: aiStyle });
      setAiTitle(data.title);
      setAiText(data.story);
      setStoryTitle(data.title);
      setStoryText(data.story);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'AI generation failed');
    }
    setAiLoading(false);
  };

  // --- Browse ---
  const handleSearch = async () => {
    setBrowseLoading(true);
    try {
      const data = await searchRedditStories({ subreddit, sort, limit: 20 });
      setStories(data);
    } catch {
      setStories([]);
    }
    setBrowseLoading(false);
  };

  const selectBrowseStory = (story: any) => {
    setStoryTitle(story.title);
    setStoryText(story.selftext);
  };

  // --- Video generation ---
  const handleGenerate = async () => {
    if (!storyTitle.trim() || !storyText.trim()) return;
    setGenerating(true);
    setError(null);
    setResultVideo(null);

    try {
      const data = await generateRedditVideo({
        story_title: storyTitle,
        story_text: storyText,
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
    if (result?.file_path) setResultVideo(result.file_path);
  }, []);

  const onError = useCallback((msg: string) => {
    setGenerating(false);
    setError(msg);
  }, []);

  const hasStory = storyTitle.trim() && storyText.trim();

  return (
    <div className="max-w-6xl">
      <h1 className="text-2xl font-bold mb-1">Reddit Story Videos</h1>
      <p className="text-gray-400 text-sm mb-6">
        Paste your own story, generate one with AI, or browse Reddit — then turn it into a viral video
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Story input */}
        <div>
          {/* Tabs */}
          <div className="flex border-b border-gray-800 mb-4">
            {[
              { id: 'paste' as Tab, label: 'Paste Story' },
              { id: 'ai' as Tab, label: 'AI Generate' },
              { id: 'browse' as Tab, label: 'Browse Reddit' },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all -mb-[1px] ${
                  tab === t.id
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-gray-500 hover:text-gray-300'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab: Paste Story */}
          {tab === 'paste' && (
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Title</label>
                <input
                  type="text"
                  value={pasteTitle}
                  onChange={(e) => setPasteTitle(e.target.value)}
                  placeholder="TIFU by accidentally sending my boss a meme..."
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Story</label>
                <textarea
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                  placeholder="Paste your Reddit story, copypasta, or any text you want narrated..."
                  rows={12}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm resize-none focus:border-brand-500 focus:outline-none"
                />
              </div>
              <p className="text-xs text-gray-600">
                {pasteText.length} characters &middot;{' '}
                ~{Math.ceil(pasteText.split(/\s+/).filter(Boolean).length / 150)} min video
              </p>
            </div>
          )}

          {/* Tab: AI Generate */}
          {tab === 'ai' && (
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Story Style</label>
                <div className="grid grid-cols-2 gap-2">
                  {storyStyles.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setAiStyle(s.id)}
                      className={`px-3 py-2 rounded-lg text-sm text-left border transition-all ${
                        aiStyle === s.id
                          ? 'border-brand-500 bg-brand-500/20 text-brand-400'
                          : 'border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {s.name}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">
                  Topic <span className="text-gray-600">(optional — leave blank for random)</span>
                </label>
                <input
                  type="text"
                  value={aiTopic}
                  onChange={(e) => setAiTopic(e.target.value)}
                  placeholder="e.g. a job interview gone horribly wrong"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none"
                />
              </div>
              <button
                onClick={handleAIGenerate}
                disabled={aiLoading}
                className="w-full bg-gradient-to-r from-violet-500 to-indigo-500 hover:from-violet-600 hover:to-indigo-600 py-2.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
              >
                {aiLoading ? 'Generating Story...' : 'Generate Story with AI'}
              </button>

              {/* Show generated story */}
              {aiTitle && (
                <div className="p-4 bg-gray-900/50 border border-gray-800 rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-sm">{aiTitle}</h3>
                    <button
                      onClick={handleAIGenerate}
                      disabled={aiLoading}
                      className="text-xs text-brand-400 hover:text-brand-300"
                    >
                      Regenerate
                    </button>
                  </div>
                  <p className="text-sm text-gray-400 max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {aiText}
                  </p>
                  <p className="text-xs text-gray-600">
                    {aiText.length} characters &middot;{' '}
                    ~{Math.ceil(aiText.split(/\s+/).filter(Boolean).length / 150)} min video
                  </p>
                </div>
              )}

              <p className="text-xs text-gray-600">
                Powered by OpenRouter &middot; Requires OPENROUTER_API_KEY in backend .env
              </p>
            </div>
          )}

          {/* Tab: Browse Reddit */}
          {tab === 'browse' && (
            <div className="space-y-3">
              <div className="flex gap-2">
                <select
                  value={subreddit}
                  onChange={(e) => setSubreddit(e.target.value)}
                  className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm flex-1"
                >
                  {subreddits.map((s) => (
                    <option key={s} value={s}>r/{s}</option>
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
                  disabled={browseLoading}
                  className="bg-brand-500 hover:bg-brand-600 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {browseLoading ? '...' : 'Search'}
                </button>
              </div>

              <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2">
                {stories.map((story) => (
                  <div
                    key={story.id}
                    onClick={() => selectBrowseStory(story)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      storyTitle === story.title
                        ? 'border-brand-500 bg-brand-500/10'
                        : 'border-gray-800 bg-gray-900/50 hover:border-gray-600'
                    }`}
                  >
                    <h3 className="text-sm font-medium mb-1 line-clamp-2">{story.title}</h3>
                    <p className="text-xs text-gray-500 line-clamp-2">{story.selftext}</p>
                    <div className="flex gap-3 mt-2 text-xs text-gray-600">
                      <span>r/{story.subreddit}</span>
                      <span>{story.score?.toLocaleString()} pts</span>
                    </div>
                  </div>
                ))}
                {stories.length === 0 && (
                  <p className="text-sm text-gray-600 text-center py-8">
                    Click Search to browse stories (requires Reddit API keys)
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right: Settings + Generate */}
        <div>
          {hasStory ? (
            <div className="space-y-4">
              {/* Story preview */}
              <div className="p-4 bg-gray-900/50 border border-gray-800 rounded-lg">
                <h3 className="font-medium mb-2 text-sm">{storyTitle}</h3>
                <p className="text-sm text-gray-400 max-h-32 overflow-y-auto whitespace-pre-wrap">
                  {storyText}
                </p>
              </div>

              {/* Voice */}
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

              {/* Background */}
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

              {/* Generate */}
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-600 hover:to-purple-600 py-3 rounded-lg font-medium transition-all disabled:opacity-50"
              >
                {generating ? 'Generating Video...' : 'Generate Video'}
              </button>

              {taskId && generating && (
                <ProgressBar taskId={taskId} onComplete={onComplete} onError={onError} />
              )}

              {error && (
                <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
                  {error}
                </div>
              )}

              {resultVideo && <VideoPreview filename={resultVideo} title={storyTitle} />}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-gray-600 text-sm border border-gray-800 rounded-lg border-dashed gap-2">
              <span>No story selected yet</span>
              <span className="text-xs text-gray-700">
                Paste a story, generate one with AI, or pick one from Reddit
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
