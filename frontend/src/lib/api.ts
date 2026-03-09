import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
});

// --- Projects ---
export async function getProjects() {
  const { data } = await api.get('/projects');
  return data;
}

export async function getProject(id: number) {
  const { data } = await api.get(`/projects/${id}`);
  return data;
}

export async function deleteProject(id: number) {
  const { data } = await api.delete(`/projects/${id}`);
  return data;
}

// --- Reddit ---
export async function searchRedditStories(params: {
  subreddit?: string;
  sort?: string;
  limit?: number;
  time_filter?: string;
}) {
  const { data } = await api.get('/reddit/search', { params });
  return data;
}

export async function getRedditVoices() {
  const { data } = await api.get('/reddit/voices');
  return data;
}

export async function getSubreddits() {
  const { data } = await api.get('/reddit/subreddits');
  return data;
}

export async function generateRedditVideo(params: {
  story_title: string;
  story_text: string;
  voice?: string;
  background_category?: string;
  font_size?: number;
  font_color?: string;
  highlight_color?: string;
}) {
  const { data } = await api.post('/reddit/generate', params);
  return data;
}

// --- Sora ---
export async function generateSoraVideo(params: {
  prompt: string;
  duration?: number;
  aspect_ratio?: string;
}) {
  const { data } = await api.post('/sora/generate', params);
  return data;
}

// --- Clipper ---
export async function uploadVideo(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/clipper/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  });
  return data;
}

export async function analyzeVideo(projectId: number) {
  const { data } = await api.post(`/clipper/analyze/${projectId}`);
  return data;
}

export async function generateClips(
  projectId: number,
  params: {
    clips: { start: number; end: number; title: string }[];
    add_captions?: boolean;
    aspect_ratio?: string;
  }
) {
  const { data } = await api.post(`/clipper/generate/${projectId}`, params);
  return data;
}

// --- UGC ---
export async function getUGCTemplates() {
  const { data } = await api.get('/ugc/templates');
  return data;
}

export async function generateUGCVideo(params: {
  product_name: string;
  script: string;
  voice?: string;
  style?: string;
  stock_keywords?: string[];
  brand_color?: string;
}) {
  const { data } = await api.post('/ugc/generate', params);
  return data;
}

// --- Jobs ---
export async function getJobStatus(taskId: string) {
  const { data } = await api.get(`/jobs/${taskId}`);
  return data;
}

// --- Health ---
export async function getHealth() {
  const { data } = await api.get('/health');
  return data;
}

export function getMediaUrl(filename: string) {
  return `/api/media/${filename}`;
}

export default api;
