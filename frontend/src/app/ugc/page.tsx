'use client';

import { useEffect, useState, useCallback } from 'react';
import { getUGCTemplates, generateUGCVideo, getRedditVoices } from '@/lib/api';
import ProgressBar from '@/components/ProgressBar';
import VideoPreview from '@/components/VideoPreview';

export default function UGCPage() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [voices, setVoices] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('testimonial');
  const [productName, setProductName] = useState('');
  const [script, setScript] = useState('');
  const [voice, setVoice] = useState('en-US-JennyNeural');
  const [brandColor, setBrandColor] = useState('#FF6B35');
  const [keywords, setKeywords] = useState('');

  const [generating, setGenerating] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [resultVideo, setResultVideo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getUGCTemplates().then(setTemplates).catch(() => {});
    getRedditVoices()
      .then((v) => setVoices(v.slice(0, 20)))
      .catch(() => {});
  }, []);

  // Update script when template changes
  useEffect(() => {
    const tpl = templates.find((t) => t.id === selectedTemplate);
    if (tpl && !script) {
      setScript(tpl.script_template);
      setVoice(tpl.voice);
    }
  }, [selectedTemplate, templates]);

  const handleTemplateChange = (id: string) => {
    setSelectedTemplate(id);
    const tpl = templates.find((t) => t.id === id);
    if (tpl) {
      setScript(tpl.script_template);
      setVoice(tpl.voice);
    }
  };

  const handleGenerate = async () => {
    if (!productName.trim() || !script.trim()) return;
    setGenerating(true);
    setError(null);
    setResultVideo(null);

    try {
      const data = await generateUGCVideo({
        product_name: productName,
        script,
        voice,
        style: selectedTemplate,
        stock_keywords: keywords
          .split(',')
          .map((k) => k.trim())
          .filter(Boolean),
        brand_color: brandColor,
      });
      setTaskId(data.task_id);
    } catch (e: any) {
      setError(e.message || 'Generation failed');
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

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-1">AI UGC Creator</h1>
      <p className="text-gray-400 text-sm mb-6">
        Generate user-generated-content style videos for brands — testimonials, reviews, product showcases
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Templates */}
        <div className="space-y-2">
          <label className="text-sm text-gray-400 mb-1 block">Template</label>
          {templates.map((tpl) => (
            <div
              key={tpl.id}
              onClick={() => handleTemplateChange(tpl.id)}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                selectedTemplate === tpl.id
                  ? 'border-brand-500 bg-brand-500/10'
                  : 'border-gray-800 bg-gray-900/50 hover:border-gray-600'
              }`}
            >
              <h3 className="text-sm font-medium">{tpl.name}</h3>
              <p className="text-xs text-gray-500 mt-1">{tpl.description}</p>
            </div>
          ))}
        </div>

        {/* Right: Settings */}
        <div className="lg:col-span-2 space-y-4">
          {/* Product name */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Product Name</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="e.g. GlowSkin Serum"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>

          {/* Script */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">
              Script{' '}
              <span className="text-gray-600">(use {'{product}'} as placeholder)</span>
            </label>
            <textarea
              value={script}
              onChange={(e) => setScript(e.target.value)}
              rows={5}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm resize-none focus:border-brand-500 focus:outline-none"
            />
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
                <option value="en-US-JennyNeural">Jenny (Female)</option>
              )}
            </select>
          </div>

          {/* Brand color */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Brand Color</label>
            <div className="flex gap-2 items-center">
              <input
                type="color"
                value={brandColor}
                onChange={(e) => setBrandColor(e.target.value)}
                className="w-10 h-10 rounded border border-gray-700 cursor-pointer"
              />
              <input
                type="text"
                value={brandColor}
                onChange={(e) => setBrandColor(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm w-28"
              />
            </div>
          </div>

          {/* Stock keywords */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">
              Stock Footage Keywords <span className="text-gray-600">(comma separated)</span>
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="skincare, beauty, lifestyle"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>

          {/* Generate */}
          <button
            onClick={handleGenerate}
            disabled={generating || !productName.trim() || !script.trim()}
            className="w-full bg-gradient-to-r from-pink-500 to-violet-500 hover:from-pink-600 hover:to-violet-600 py-3 rounded-lg font-medium transition-all disabled:opacity-50"
          >
            {generating ? 'Generating UGC Video...' : 'Generate UGC Video'}
          </button>

          {taskId && generating && (
            <ProgressBar taskId={taskId} onComplete={onComplete} onError={onError} />
          )}

          {error && (
            <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
              {error}
            </div>
          )}

          {resultVideo && (
            <VideoPreview filename={resultVideo} title={`UGC: ${productName}`} />
          )}
        </div>
      </div>
    </div>
  );
}
