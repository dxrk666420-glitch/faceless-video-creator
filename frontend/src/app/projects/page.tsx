'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getProjects, deleteProject, getProject } from '@/lib/api';
import VideoPreview from '@/components/VideoPreview';

const typeColors: Record<string, string> = {
  reddit: 'bg-orange-900/50 text-orange-400',
  sora: 'bg-purple-900/50 text-purple-400',
  clipper: 'bg-green-900/50 text-green-400',
  ugc: 'bg-pink-900/50 text-pink-400',
};

const statusColors: Record<string, string> = {
  completed: 'bg-green-900/50 text-green-400',
  failed: 'bg-red-900/50 text-red-400',
  processing: 'bg-yellow-900/50 text-yellow-400',
  pending: 'bg-gray-800 text-gray-400',
  uploaded: 'bg-blue-900/50 text-blue-400',
  analyzed: 'bg-teal-900/50 text-teal-400',
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [expandedProject, setExpandedProject] = useState<any>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = () => {
    getProjects().then(setProjects).catch(() => {});
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this project and all its videos?')) return;
    await deleteProject(id);
    loadProjects();
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedProject(null);
    }
  };

  const handleExpand = async (id: number) => {
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedProject(null);
      return;
    }
    setExpandedId(id);
    try {
      const data = await getProject(id);
      setExpandedProject(data);
    } catch {
      setExpandedProject(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold mb-1">All Projects</h1>
      <p className="text-gray-400 text-sm mb-6">
        View and manage all your video generation projects
      </p>

      {projects.length === 0 ? (
        <div className="text-center py-16 text-gray-600">
          <p className="text-lg mb-2">No projects yet</p>
          <p className="text-sm">
            Go to{' '}
            <Link href="/reddit" className="text-brand-400 hover:underline">
              Reddit Stories
            </Link>
            ,{' '}
            <Link href="/sora" className="text-brand-400 hover:underline">
              Sora
            </Link>
            ,{' '}
            <Link href="/clipper" className="text-brand-400 hover:underline">
              Clipper
            </Link>
            , or{' '}
            <Link href="/ugc" className="text-brand-400 hover:underline">
              UGC Creator
            </Link>{' '}
            to create your first video
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {projects.map((p: any) => (
            <div key={p.id}>
              <div
                className="flex items-center justify-between p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors cursor-pointer"
                onClick={() => handleExpand(p.id)}
              >
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-1 rounded ${typeColors[p.type] || 'bg-gray-800 text-gray-400'}`}>
                    {p.type}
                  </span>
                  <span className="text-sm font-medium">{p.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-600">{formatDate(p.created_at)}</span>
                  <span className={`text-xs px-2 py-1 rounded ${statusColors[p.status] || ''}`}>
                    {p.status}
                  </span>
                  {p.video_count > 0 && (
                    <span className="text-xs text-gray-500">{p.video_count} video(s)</span>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(p.id);
                    }}
                    className="text-gray-600 hover:text-red-400 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Expanded view */}
              {expandedId === p.id && expandedProject && (
                <div className="ml-4 mt-2 p-4 border border-gray-800 rounded-lg bg-gray-900/30 space-y-4">
                  {expandedProject.error_message && (
                    <div className="text-sm text-red-400">
                      Error: {expandedProject.error_message}
                    </div>
                  )}
                  {expandedProject.videos?.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {expandedProject.videos.map((v: any) => (
                        <VideoPreview key={v.id} filename={v.file_path} title={v.title} />
                      ))}
                    </div>
                  )}
                  {expandedProject.videos?.length === 0 && (
                    <p className="text-sm text-gray-500">No videos generated yet</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
