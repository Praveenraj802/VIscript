import axios, { AxiosError } from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization Bearer token to all outgoing requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('visualiq_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global response interceptor for 401 Unauthorized handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('visualiq_token');
      localStorage.removeItem('visualiq_user');
      window.dispatchEvent(new CustomEvent('visualiq:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface LoginResponseData {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface QueryResponseData {
  question: string;
  answer: string;
  sources: string[];
  provider?: string;
  latency_ms?: number;
}

export interface JobStatusData {
  job_id: string;
  status: 'pending' | 'extracting' | 'analyzing' | 'synthesizing' | 'storing' | 'done' | 'failed';
  message?: string;
  frame_count: number;
  analyzed_count: number;
  error?: string;
}

export interface CameraData {
  id: string;
  name: string;
  location?: string;
  status: string;
  stream_url?: string;
}

export interface TranscriptData {
  id: string;
  camera_id: string;
  camera_name?: string;
  period_start: string;
  period_end: string;
  narrative: string;
  event_count: number;
  events?: any[];
  created_at?: string;
}

export interface AlertData {
  id: string;
  camera_id: string;
  camera_name?: string;
  event_id?: string;
  time?: string;
  activity?: string;
  anomaly_score: number;
  anomaly_reason?: string;
  resolved: boolean;
  created_at?: string;
}

export interface EventData {
  time: string;
  camera_id: string;
  people_count: number;
  activity: string;
  objects: string[];
  anomaly_score: number;
  anomaly_reason?: string;
  location_zone: string;
  faces_visible: boolean;
  frame_path?: string;
}

export const apiClient = {
  // Authentication
  login: async (email: string, password: string): Promise<LoginResponseData> => {
    const res = await api.post<LoginResponseData>('/api/auth/login', { email, password });
    if (res.data?.access_token) {
      localStorage.setItem('visualiq_token', res.data.access_token);
      localStorage.setItem('visualiq_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },

  register: async (
    email: string,
    password: string,
    name?: string,
    role?: string
  ): Promise<LoginResponseData> => {
    const res = await api.post<LoginResponseData>('/api/auth/register', { email, password, name, role });
    if (res.data?.access_token) {
      localStorage.setItem('visualiq_token', res.data.access_token);
      localStorage.setItem('visualiq_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },

  getMe: async (): Promise<UserProfile> => {
    const res = await api.get<UserProfile>('/api/auth/me');
    return res.data;
  },

  logout: () => {
    localStorage.removeItem('visualiq_token');
    localStorage.removeItem('visualiq_user');
  },

  getCurrentUser: (): UserProfile | null => {
    const stored = localStorage.getItem('visualiq_user');
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  // Cameras
  getCameras: async (): Promise<CameraData[]> => {
    try {
      const res = await api.get('/api/cameras');
      return Array.isArray(res.data) ? res.data : [];
    } catch (err) {
      console.error('API getCameras error:', err);
      throw err;
    }
  },

  addCamera: async (data: { name: string; location?: string; stream_url?: string; id?: string }): Promise<CameraData> => {
    const res = await api.post<CameraData>('/api/cameras', data);
    return res.data;
  },

  deleteCamera: async (cameraId: string): Promise<{ status: string }> => {
    const res = await api.delete(`/api/cameras/${cameraId}`);
    return res.data;
  },

  getStreamHealth: async (): Promise<Record<string, any>> => {
    const res = await api.get('/api/cameras/health');
    return res.data;
  },

  transcribeLiveCamera: async (cameraId: string): Promise<{ status: string; event: EventData }> => {
    const res = await api.post(`/api/cameras/${cameraId}/transcribe`);
    return res.data;
  },

  toggleLiveTranscription: async (cameraId: string, enabled: boolean): Promise<{ status: string; transcription_enabled: boolean }> => {
    const res = await api.post(`/api/cameras/${cameraId}/toggle-transcription`, null, {
      params: { enabled }
    });
    return res.data;
  },

  // Transcripts
  getTranscripts: async (camera_id?: string): Promise<TranscriptData[]> => {
    try {
      const res = await api.get('/api/transcripts', {
        params: camera_id ? { camera_id } : {},
      });
      return Array.isArray(res.data) ? res.data : [];
    } catch (err) {
      console.error('API getTranscripts error:', err);
      throw err;
    }
  },

  // Raw Events for Timeline
  getEvents: async (camera_id?: string): Promise<EventData[]> => {
    try {
      const res = await api.get('/api/events', {
        params: camera_id ? { camera_id } : {},
      });
      return Array.isArray(res.data) ? res.data : [];
    } catch (err) {
      console.error('API getEvents error:', err);
      throw err;
    }
  },

  // Alerts
  getAlerts: async (camera_id?: string): Promise<AlertData[]> => {
    try {
      const res = await api.get('/api/alerts', {
        params: camera_id ? { camera_id } : {},
      });
      return Array.isArray(res.data) ? res.data : [];
    } catch (err) {
      console.error('API getAlerts error:', err);
      throw err;
    }
  },

  resolveAlert: async (alert_id: string): Promise<{ status: string }> => {
    const res = await api.post(`/api/alerts/${alert_id}/resolve`);
    return res.data;
  },

  // RAG Natural Language Query
  askQuery: async (question: string, camera_id?: string): Promise<QueryResponseData> => {
    const res = await api.post('/api/query', { question, camera_id });
    return res.data;
  },

  // Video Upload
  uploadVideo: async (
    file: File,
    camera_id: string,
    onProgress?: (percent: number) => void
  ): Promise<JobStatusData> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('camera_id', camera_id);

    const res = await api.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return res.data;
  },

  // Job Status Polling
  getJobStatus: async (job_id: string): Promise<JobStatusData> => {
    const res = await api.get(`/api/job/${job_id}`);
    return res.data;
  },

  // Daily Security Digest
  generateDigest: async () => {
    const res = await api.post('/api/digest');
    return res.data;
  },
};
