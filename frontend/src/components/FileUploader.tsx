'use client';

import { useCallback, useState } from 'react';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  label?: string;
}

export default function FileUploader({
  onFileSelect,
  accept = 'video/*',
  label = 'Drag and drop a video file, or click to browse',
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) {
        setFileName(file.name);
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        setFileName(file.name);
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
        isDragging
          ? 'border-brand-500 bg-brand-500/10'
          : 'border-gray-700 hover:border-gray-500 bg-gray-900/50'
      }`}
    >
      <input
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
        id="file-upload"
      />
      <label htmlFor="file-upload" className="cursor-pointer">
        <svg
          className="mx-auto w-12 h-12 text-gray-500 mb-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        {fileName ? (
          <p className="text-brand-400 font-medium">{fileName}</p>
        ) : (
          <p className="text-gray-400 text-sm">{label}</p>
        )}
      </label>
    </div>
  );
}
