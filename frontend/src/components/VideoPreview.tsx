'use client';

import { getMediaUrl } from '@/lib/api';

interface VideoPreviewProps {
  filename: string;
  title?: string;
}

export default function VideoPreview({ filename, title }: VideoPreviewProps) {
  return (
    <div className="rounded-xl overflow-hidden bg-gray-900 border border-gray-800">
      {title && (
        <div className="px-4 py-2 border-b border-gray-800">
          <h3 className="text-sm font-medium text-gray-300 truncate">{title}</h3>
        </div>
      )}
      <video
        src={getMediaUrl(filename)}
        controls
        className="w-full aspect-[9/16] max-h-[500px] object-contain bg-black"
      />
      <div className="px-4 py-2 border-t border-gray-800 flex gap-2">
        <a
          href={getMediaUrl(filename)}
          download={filename}
          className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
        >
          Download
        </a>
      </div>
    </div>
  );
}
