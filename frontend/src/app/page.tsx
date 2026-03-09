'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getProjects, getHealth } from '@/lib/api';

const features = [
  {
    href: '/reddit',
    title: 'Reddit Story Videos',
    desc: 'Turn viral Reddit stories into engaging narrated videos with captivating backgrounds and word-by-word captions',
    gradient: 'from-orange-500 to-red-500',
    icon: '🎙️',
  },
  {
    href: '/sora',
    title: 'AI Video Generator',
    desc: 'Generate stunning videos from text prompts using OpenAI Sora — cinematic quality, any style',
    gradient: 'from-purple-500 to-blue-500',
    icon: '🎬',
  },
  {
    href: '/clipper',
    title: 'Auto Video Clipper',
    desc: 'Upload long-form videos and let AI find the best moments, auto-clip to vertical with captions',
    gradient: 'from-green-500 to-teal-500',
    icon: '✂️',
  },
  {
    href: '/ugc',
    title: 'AI UGC Creator',
    desc: 'Generate user-generated-content style videos for brands — testimonials, reviews, showcases',
    gradient: 'from-pink-500 to-violet-500',
    icon: '🛍️',
  },
];

export default function Dashboard() {
  const [projects, setProjects] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    getProjects().then(setProjects).catch(() => {});
    getHealth().then(setHealth).catch(() => {});
  }, []);

  const recentProjects = projects.slice(0, 5);

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Faceless Video Creator</h1>
        <p className="text-gray-400">
          Create viral content for TikTok, YouTube Shorts, and Instagram Reels — no face required
        </p>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        {features.map((f) => (
          <Link
            key={f.href}
            href={f.href}
            className="group relative overflow-hidden rounded-xl border border-gray-800 bg-gray-900/50 p-6 hover:border-gray-600 transition-all"
          >
            <div
              className={`absolute inset-0 bg-gradient-to-br ${f.gradient} opacity-5 group-hover:opacity-10 transition-opacity`}
            />
            <div className="relative">
              <div className="text-2xl mb-3">{f.icon}</div>
              <h2 className="text-lg font-semibold mb-1">{f.title}</h2>
              <p className="text-sm text-gray-400">{f.desc}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* API Status */}
      {health && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3">API Connections</h2>
          <div className="flex flex-wrap gap-3">
            {Object.entries(health.features as Record<string, boolean>).map(
              ([key, connected]) => (
                <div
                  key={key}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${
                    connected
                      ? 'border-green-800 bg-green-900/30 text-green-400'
                      : 'border-gray-700 bg-gray-800/50 text-gray-500'
                  }`}
                >
                  <span className={`inline-block w-2 h-2 rounded-full mr-2 ${connected ? 'bg-green-400' : 'bg-gray-600'}`} />
                  {key}
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* Recent projects */}
      {recentProjects.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Recent Projects</h2>
            <Link href="/projects" className="text-sm text-brand-400 hover:text-brand-300">
              View all
            </Link>
          </div>
          <div className="space-y-2">
            {recentProjects.map((p: any) => (
              <Link
                key={p.id}
                href={`/projects`}
                className="flex items-center justify-between p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors"
              >
                <div>
                  <span className="text-sm font-medium">{p.name}</span>
                  <span className="ml-3 text-xs text-gray-500">{p.type}</span>
                </div>
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    p.status === 'completed'
                      ? 'bg-green-900/50 text-green-400'
                      : p.status === 'failed'
                        ? 'bg-red-900/50 text-red-400'
                        : 'bg-yellow-900/50 text-yellow-400'
                  }`}
                >
                  {p.status}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
