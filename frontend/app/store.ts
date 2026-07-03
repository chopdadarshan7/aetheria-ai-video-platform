/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from 'zustand';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

export interface User {
  id: number;
  username: string;
  email: string;
  credits: number;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: number;
  filename: string;
  original_name: string;
  mime_type: string;
  file_size: number;
  storage_path: string;
  owner_id: number;
  project_id: number | null;
  created_at: string;
}

export interface RenderJob {
  id: number;
  job_type: string;
  status: string;
  progress: number;
  prompt: string;
  negative_prompt: string | null;
  aspect_ratio: string;
  duration: number;
  cost: number;
  steps: number;
  cfg_scale: number;
  seed: number | null;
  motion_strength: number;
  fps: number;
  model_version: string | null;
  input_asset_id: number | null;
  result_url: string | null;
  thumbnail_url: string | null;
  gif_url: string | null;
  metadata_url: string | null;
  error_message: string | null;
  user_id: number;
  project_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface ModelInfo {
  id: string;
  repo_id: string;
  description: string;
  type: string;
  loaded: boolean;
  active: boolean;
  cached: boolean;
}

// Phase 3 — Storyboard & Timeline interfaces
export interface Shot {
  id: number;
  name: string;
  order: number;
  scene_id: number;
  prompt: string;
  negative_prompt: string | null;
  aspect_ratio: string;
  duration: number;
  steps: number;
  cfg_scale: number;
  seed: number | null;
  motion_strength: number;
  fps: number;
  model_version: string | null;
  camera_path: string | null;
  motion_brush: string | null;
  render_job_id: number | null;
}

export interface Scene {
  id: number;
  name: string;
  order: number;
  storyboard_id: number;
  shots: Shot[];
}

export interface TimelineItem {
  id: number;
  layer_id: number;
  shot_id: number | null;
  asset_id: number | null;
  start_time: number;
  duration: number;
  transition_in: string | null;
  transition_out: string | null;
}

export interface Layer {
  id: number;
  timeline_id: number;
  name: string;
  order: number;
  layer_type: string;
  items: TimelineItem[];
}

export interface Timeline {
  id: number;
  storyboard_id: number;
  layers: Layer[];
}

export interface Storyboard {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  project_id: number | null;
  status: string;
  progress: number;
  result_url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  scenes: Scene[];
  timeline?: Timeline;
}

// Phase 4 — Audio Intelligence interfaces
export interface VoiceProfile {
  id: number;
  name: string;
  language: string;
  embedding_path: string | null;
  owner_id: number;
  created_at: string;
}

export interface Subtitle {
  id: number;
  text: string;
  start_time: number;
  end_time: number;
  storyboard_id: number | null;
  render_job_id: number | null;
}

export interface AudioJob {
  id: number;
  job_type: string;
  prompt: string | null;
  voice_profile_id: number | null;
  status: string;
  progress: number;
  result_url: string | null;
  error_message: string | null;
  user_id: number;
  created_at: string;
  updated_at: string;
}

// MLOps & SaaS Interfaces
export interface Dataset {
  id: number;
  name: string;
  storage_path: string;
  status: string;
  auto_captions: string | null;
  owner_id: number;
  created_at: string;
}

export interface FineTuningJob {
  id: number;
  model_name: string;
  status: string;
  progress: number;
  epochs: number;
  learning_rate: number;
  dataset_id: number;
  result_model_path: string | null;
  metrics: string | null;
  owner_id: number;
  created_at: string;
}

export interface Team {
  id: number;
  name: string;
  owner_id: number;
  created_at: string;
}

export interface ApiKey {
  id: number;
  key_hash: string;
  name: string;
  user_id: number;
  created_at: string;
}

export interface CreditTransaction {
  id: number;
  amount: number;
  transaction_type: string;
  description: string | null;
  user_id: number;
  created_at: string;
}

interface AppState {
  token: string | null;
  user: User | null;
  projects: Project[];
  activeProject: Project | null;
  assets: Asset[];
  renders: RenderJob[];
  models: ModelInfo[];
  storyboards: Storyboard[];
  activeStoryboard: Storyboard | null;
  
  // Audio state
  voices: VoiceProfile[];
  subtitles: Subtitle[];
  audioJobs: AudioJob[];

  // MLOps & SaaS state
  datasets: Dataset[];
  fineTuningJobs: FineTuningJob[];
  teams: Team[];
  apiKeys: ApiKey[];
  creditTransactions: CreditTransaction[];
  copilotMessages: Array<{ role: 'user' | 'assistant'; text: string; payload?: any }>;
  
  loading: boolean;
  error: string | null;
  wsConnected: boolean;
  
  // Auth actions
  setToken: (token: string | null) => void;
  logout: () => void;
  fetchUser: () => Promise<void>;
  
  // Projects actions
  fetchProjects: () => Promise<void>;
  setActiveProject: (project: Project | null) => void;
  createProject: (name: string, description?: string) => Promise<Project>;
  deleteProject: (projectId: number) => Promise<void>;
  
  // Assets actions
  fetchAssets: (projectId?: number) => Promise<void>;
  uploadAsset: (file: File, projectId?: number) => Promise<Asset>;
  
  // Renders actions
  fetchRenders: (projectId?: number) => Promise<void>;
  triggerRender: (params: {
    job_type: string;
    prompt: string;
    negative_prompt?: string;
    aspect_ratio?: string;
    duration?: number;
    steps?: number;
    cfg_scale?: number;
    seed?: number;
    motion_strength?: number;
    fps?: number;
    model_version?: string;
    project_id?: number;
    input_asset_id?: number;
  }) => Promise<RenderJob>;
  pollRender: (jobId: number) => Promise<RenderJob>;
  cancelRender: (jobId: number) => Promise<void>;
  retryRender: (jobId: number) => Promise<void>;
  
  // Model management actions
  fetchModels: () => Promise<void>;
  downloadModel: (modelId: string) => Promise<void>;
  switchModel: (modelId: string) => Promise<void>;
  deleteModel: (modelId: string) => Promise<void>;

  // Storyboard & Timeline actions
  fetchStoryboards: (projectId?: number) => Promise<void>;
  fetchStoryboardDetails: (storyboardId: number) => Promise<Storyboard>;
  createStoryboard: (name: string, description?: string, projectId?: number) => Promise<Storyboard>;
  deleteStoryboard: (storyboardId: number) => Promise<void>;
  triggerStoryboardRender: (storyboardId: number) => Promise<Storyboard>;
  createScene: (storyboardId: number, name: string, order?: number) => Promise<Scene>;
  deleteScene: (sceneId: number) => Promise<void>;
  createShot: (sceneId: number, shot: Omit<Shot, 'id' | 'scene_id' | 'render_job_id'>) => Promise<Shot>;
  deleteShot: (shotId: number) => Promise<void>;
  addTimelineItem: (layerId: number, item: Omit<TimelineItem, 'id' | 'layer_id'>) => Promise<TimelineItem>;
  deleteTimelineItem: (itemId: number) => Promise<void>;

  // Audio actions
  fetchVoices: () => Promise<void>;
  createVoice: (name: string, language?: string) => Promise<VoiceProfile>;
  deleteVoice: (voiceId: number) => Promise<void>;
  triggerAudioJob: (params: { job_type: string; prompt?: string; voice_profile_id?: number }) => Promise<AudioJob>;
  fetchSubtitles: (storyboardId?: number) => Promise<void>;
  createSubtitle: (sub: Omit<Subtitle, 'id'>) => Promise<Subtitle>;
  deleteSubtitle: (subId: number) => Promise<void>;

  // MLOps & SaaS API calls
  fetchDatasets: () => Promise<void>;
  createDataset: (name: string, storagePath: string) => Promise<Dataset>;
  triggerFineTuning: (params: { model_name: string; dataset_id: number; epochs?: number; learning_rate?: number }) => Promise<FineTuningJob>;
  fetchFineTuningJobs: () => Promise<void>;
  fetchBillingTransactions: () => Promise<void>;
  checkoutPlan: (plan: string) => Promise<string>;
  triggerWebhookDeposit: (amount: number) => Promise<void>;
  fetchTeams: () => Promise<void>;
  createTeam: (name: string) => Promise<Team>;
  fetchApiKeys: () => Promise<void>;
  createApiKey: (name: string) => Promise<ApiKey>;
  sendCopilotMessage: (text: string) => Promise<void>;
  estimateRenderCost: (duration: number, steps: number) => Promise<any>;

  // WebSockets action
  initWebsocket: () => void;
}

let socket: WebSocket | null = null;

export const useStore = create<AppState>((set, get) => {
  let initialToken = null;
  if (typeof window !== 'undefined') {
    initialToken = localStorage.getItem('auth_token');
  }

  return {
    token: initialToken,
    user: null,
    projects: [],
    activeProject: null,
    assets: [],
    renders: [],
    models: [],
    storyboards: [],
    activeStoryboard: null,
    
    voices: [],
    subtitles: [],
    audioJobs: [],

    datasets: [],
    fineTuningJobs: [],
    teams: [],
    apiKeys: [],
    creditTransactions: [],
    copilotMessages: [
      { role: 'assistant', text: "Hello! I am your AI Copilot. I can refine prompts, suggest shot layout angles, and compute rendering VRAM costs. How can I assist you today?" }
    ],
    
    loading: false,
    error: null,
    wsConnected: false,

    setToken: (token) => {
      if (token) {
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
      set({ token });
    },

    logout: () => {
      localStorage.removeItem('auth_token');
      if (socket) {
        socket.close();
        socket = null;
      }
      set({ token: null, user: null, projects: [], activeProject: null, assets: [], renders: [], storyboards: [], activeStoryboard: null, voices: [], subtitles: [], audioJobs: [], datasets: [], fineTuningJobs: [], teams: [], apiKeys: [], creditTransactions: [], wsConnected: false });
    },

    fetchUser: async () => {
      const { token } = get();
      if (!token) return;
      let res: Response | null = null;
      try {
        set({ loading: true, error: null });
        res = await fetch(`${API_BASE_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch user');
        const user = await res.json();
        set({ user, loading: false });
        get().initWebsocket();
      } catch (err: any) {
        set({ error: err.message, loading: false });
        if (err.message.includes('Unauthorized') || res?.status === 401) {
          get().logout();
        }
      }
    },

    fetchProjects: async () => {
      const { token } = get();
      if (!token) return;
      try {
        set({ loading: true, error: null });
        const res = await fetch(`${API_BASE_URL}/projects`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch projects');
        const projects = await res.json();
        set({ projects, loading: false });
        if (projects.length > 0 && !get().activeProject) {
          set({ activeProject: projects[0] });
        }
      } catch (err: any) {
        set({ error: err.message, loading: false });
      }
    },

    setActiveProject: (activeProject) => set({ activeProject }),

    createProject: async (name, description = '') => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        set({ loading: true, error: null });
        const res = await fetch(`${API_BASE_URL}/projects`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ name, description })
        });
        if (!res.ok) throw new Error('Failed to create project');
        const newProj = await res.json();
        set((state) => ({
          projects: [...state.projects, newProj],
          activeProject: newProj,
          loading: false
        }));
        return newProj;
      } catch (err: any) {
        set({ error: err.message, loading: false });
        throw err;
      }
    },

    deleteProject: async (projectId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        set({ loading: true, error: null });
        const res = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to delete project');
        set((state) => {
          const updatedProjects = state.projects.filter(p => p.id !== projectId);
          const nextActive = state.activeProject?.id === projectId 
            ? (updatedProjects[0] || null)
            : state.activeProject;
          return {
            projects: updatedProjects,
            activeProject: nextActive,
            loading: false
          };
        });
      } catch (err: any) {
        set({ error: err.message, loading: false });
        throw err;
      }
    },

    fetchAssets: async (projectId) => {
      const { token } = get();
      if (!token) return;
      try {
        set({ loading: true, error: null });
        let url = `${API_BASE_URL}/assets`;
        if (projectId) url += `?project_id=${projectId}`;
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch assets');
        const assets = await res.json();
        set({ assets, loading: false });
      } catch (err: any) {
        set({ error: err.message, loading: false });
      }
    },

    uploadAsset: async (file, projectId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        set({ loading: true, error: null });
        const formData = new FormData();
        formData.append('file', file);
        if (projectId) {
          formData.append('project_id', projectId.toString());
        }

        const res = await fetch(`${API_BASE_URL}/assets/upload`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`
          },
          body: formData
        });
        if (!res.ok) throw new Error('Failed to upload asset');
        const newAsset = await res.json();
        set((state) => ({
          assets: [newAsset, ...state.assets],
          loading: false
        }));
        return newAsset;
      } catch (err: any) {
        set({ error: err.message, loading: false });
        throw err;
      }
    },

    fetchRenders: async (projectId) => {
      const { token } = get();
      if (!token) return;
      try {
        let url = `${API_BASE_URL}/renders`;
        if (projectId) url += `?project_id=${projectId}`;
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch renders');
        const renders = await res.json();
        set({ renders: renders.reverse(), loading: false });
      } catch (err: any) {
        set({ error: err.message, loading: false });
      }
    },

    triggerRender: async (params) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        set({ loading: true, error: null });
        const res = await fetch(`${API_BASE_URL}/renders/trigger`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(params)
        });
        if (!res.ok) {
          const detail = await res.json();
          throw new Error(detail?.detail || 'Failed to trigger render');
        }
        const newJob = await res.json();
        set((state) => ({
          renders: [newJob, ...state.renders],
          loading: false
        }));
        return newJob;
      } catch (err: any) {
        set({ error: err.message, loading: false });
        throw err;
      }
    },

    pollRender: async (jobId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      const res = await fetch(`${API_BASE_URL}/renders/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to check render status');
      const job = await res.json();
      set((state) => ({
        renders: state.renders.map(r => r.id === jobId ? job : r)
      }));
      if (job.status === 'SUCCESS' && get().user) {
        get().fetchUser();
      }
      return job;
    },

    cancelRender: async (jobId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/renders/${jobId}/cancel`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to cancel render job.');
        const updatedJob = await res.json();
        set((state) => ({
          renders: state.renders.map(r => r.id === jobId ? updatedJob : r)
        }));
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    retryRender: async (jobId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/renders/${jobId}/retry`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to retry render job.');
        const updatedJob = await res.json();
        set((state) => ({
          renders: state.renders.map(r => r.id === jobId ? updatedJob : r)
        }));
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    fetchModels: async () => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/models`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch installed AI models.');
        const models = await res.json();
        set({ models });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    downloadModel: async (modelId) => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/models/download`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ model_id: modelId })
        });
        if (!res.ok) throw new Error('Failed loading model downloader.');
        const updated = await res.json();
        set((state) => ({
          models: state.models.map(m => m.id === modelId ? updated : m)
        }));
        setTimeout(() => get().fetchModels(), 5000);
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    switchModel: async (modelId) => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/models/switch`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ model_id: modelId })
        });
        if (!res.ok) throw new Error('Failed switching pipeline model.');
        const updated = await res.json();
        set((state) => ({
          models: state.models.map(m => m.id === modelId ? updated : m)
        }));
        get().fetchModels();
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    deleteModel: async (modelId) => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/models/${modelId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed deleting cached model files.');
        get().fetchModels();
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    // Storyboard & Timeline API Calls
    fetchStoryboards: async (projectId) => {
      const { token } = get();
      if (!token) return;
      try {
        let url = `${API_BASE_URL}/storyboards`;
        if (projectId) url += `?project_id=${projectId}`;
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed fetching storyboards');
        const storyboards = await res.json();
        set({ storyboards: storyboards.reverse() });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    fetchStoryboardDetails: async (storyboardId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      const res = await fetch(`${API_BASE_URL}/storyboards/${storyboardId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed fetching storyboard details');
      const activeStoryboard = await res.json();
      
      const timeRes = await fetch(`${API_BASE_URL}/storyboards/${storyboardId}/timeline`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (timeRes.ok) {
        activeStoryboard.timeline = await timeRes.json();
      }
      
      set({ activeStoryboard });
      return activeStoryboard;
    },

    createStoryboard: async (name, description = '', projectId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/storyboards`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ name, description, project_id: projectId })
        });
        if (!res.ok) throw new Error('Failed to create storyboard');
        const newSb = await res.json();
        set((state) => ({
          storyboards: [newSb, ...state.storyboards],
          activeStoryboard: newSb
        }));
        return newSb;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    deleteStoryboard: async (storyboardId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/storyboards/${storyboardId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to delete storyboard');
        set((state) => ({
          storyboards: state.storyboards.filter(s => s.id !== storyboardId),
          activeStoryboard: state.activeStoryboard?.id === storyboardId ? null : state.activeStoryboard
        }));
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    triggerStoryboardRender: async (storyboardId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/storyboards/${storyboardId}/render`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to trigger storyboard rendering');
        const updated = await res.json();
        set((state) => ({
          storyboards: state.storyboards.map(s => s.id === storyboardId ? updated : s),
          activeStoryboard: state.activeStoryboard?.id === storyboardId ? updated : state.activeStoryboard
        }));
        return updated;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    createScene: async (storyboardId, name, order = 0) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/storyboards/${storyboardId}/scenes`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ name, order })
        });
        if (!res.ok) throw new Error('Failed creating scene');
        const newScene = await res.json();
        await get().fetchStoryboardDetails(storyboardId);
        return newScene;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    deleteScene: async (sceneId) => {
      const { token, activeStoryboard } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/scenes/${sceneId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed deleting scene');
        if (activeStoryboard) {
          await get().fetchStoryboardDetails(activeStoryboard.id);
        }
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    createShot: async (sceneId, shot) => {
      const { token, activeStoryboard } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/scenes/${sceneId}/shots`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(shot)
        });
        if (!res.ok) throw new Error('Failed creating shot');
        const newShot = await res.json();
        if (activeStoryboard) {
          await get().fetchStoryboardDetails(activeStoryboard.id);
        }
        return newShot;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    deleteShot: async (shotId) => {
      const { token, activeStoryboard } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/shots/${shotId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed deleting shot');
        if (activeStoryboard) {
          await get().fetchStoryboardDetails(activeStoryboard.id);
        }
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    addTimelineItem: async (layerId, item) => {
      const { token, activeStoryboard } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/layers/${layerId}/items`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(item)
        });
        if (!res.ok) throw new Error('Failed adding timeline item');
        const newItem = await res.json();
        if (activeStoryboard) {
          await get().fetchStoryboardDetails(activeStoryboard.id);
        }
        return newItem;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    deleteTimelineItem: async (itemId) => {
      const { token, activeStoryboard } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/timeline-items/${itemId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed deleting timeline item');
        if (activeStoryboard) {
          await get().fetchStoryboardDetails(activeStoryboard.id);
        }
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    fetchVoices: async () => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/audio/voices`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed fetching voices');
        const voices = await res.json();
        set({ voices });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    createVoice: async (name, language = 'en') => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/audio/voices`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ name, language })
        });
        if (!res.ok) throw new Error('Failed to create voice profile');
        const newVoice = await res.json();
        set((state) => ({ voices: [...state.voices, newVoice] }));
        return newVoice;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    deleteVoice: async (voiceId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/audio/voices/${voiceId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to delete voice profile');
        set((state) => ({ voices: state.voices.filter(v => v.id !== voiceId) }));
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    triggerAudioJob: async (params) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/audio/jobs`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(params)
        });
        if (!res.ok) throw new Error('Failed triggering audio processing');
        const newJob = await res.json();
        set((state) => ({ audioJobs: [newJob, ...state.audioJobs] }));
        return newJob;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    fetchSubtitles: async (storyboardId) => {
      const { token } = get();
      if (!token) return;
      try {
        let url = `${API_BASE_URL}/audio/subtitles`;
        if (storyboardId) url += `?storyboard_id=${storyboardId}`;
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed fetching subtitles');
        const subtitles = await res.json();
        set({ subtitles });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    createSubtitle: async (sub) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/audio/subtitles`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(sub)
        });
        if (!res.ok) throw new Error('Failed creating subtitle');
        const newSub = await res.json();
        set((state) => ({ subtitles: [...state.subtitles, newSub] }));
        return newSub;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    deleteSubtitle: async (subId) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/audio/subtitles/${subId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed deleting subtitle');
        set((state) => ({ subtitles: state.subtitles.filter(s => s.id !== subId) }));
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    // MLOps & SaaS API Store Actions
    fetchDatasets: async () => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/mlops/datasets`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed fetching datasets');
        const datasets = await res.json();
        set({ datasets });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    createDataset: async (name, storagePath) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/mlops/datasets`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ name, storage_path: storagePath })
        });
        if (!res.ok) throw new Error('Failed to register dataset');
        const newDataset = await res.json();
        set((state) => ({ datasets: [...state.datasets, newDataset] }));
        return newDataset;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    triggerFineTuning: async (params) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/mlops/train`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(params)
        });
        if (!res.ok) throw new Error('Failed triggering fine-tuning run');
        const newJob = await res.json();
        set((state) => ({ fineTuningJobs: [newJob, ...state.fineTuningJobs] }));
        return newJob;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    fetchFineTuningJobs: async () => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/mlops/train`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed fetching fine tuning jobs');
        const jobs = await res.json();
        set({ fineTuningJobs: jobs.reverse() });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    fetchBillingTransactions: async () => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/saas/billing/transactions`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed fetching transactions history');
        const txs = await res.json();
        set({ creditTransactions: txs });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    checkoutPlan: async (plan) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      const res = await fetch(`${API_BASE_URL}/saas/billing/checkout?plan=${plan}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed checkout creation');
      const data = await res.json();
      return data.checkout_url;
    },

    triggerWebhookDeposit: async (amount) => {
      const { token, user } = get();
      if (!token || !user) return;
      try {
        const res = await fetch(`${API_BASE_URL}/saas/billing/webhook?user_id=${user.id}&amount=${amount}`, {
          method: 'POST'
        });
        if (!res.ok) throw new Error('Webhook deposit trigger failed');
        await get().fetchUser();
        await get().fetchBillingTransactions();
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    fetchTeams: async () => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/saas/teams`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed fetching teams');
        const teams = await res.json();
        set({ teams });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    createTeam: async (name) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/saas/teams`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ name })
        });
        if (!res.ok) throw new Error('Failed to create team');
        const newTeam = await res.json();
        set((state) => ({ teams: [...state.teams, newTeam] }));
        return newTeam;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    fetchApiKeys: async () => {
      const { token } = get();
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/saas/apikeys`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed fetching api keys');
        const keys = await res.json();
        set({ apiKeys: keys });
      } catch (err: any) {
        set({ error: err.message });
      }
    },

    createApiKey: async (name) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      try {
        const res = await fetch(`${API_BASE_URL}/saas/apikeys`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ name })
        });
        if (!res.ok) throw new Error('Failed creating API Key');
        const newKey = await res.json();
        set((state) => ({ apiKeys: [...state.apiKeys, newKey] }));
        return newKey;
      } catch (err: any) {
        set({ error: err.message });
        throw err;
      }
    },

    sendCopilotMessage: async (text) => {
      const { token } = get();
      if (!token) return;
      
      // Append user prompt first
      set((state) => ({
        copilotMessages: [...state.copilotMessages, { role: 'user', text }]
      }));

      try {
        const res = await fetch(`${API_BASE_URL}/copilot/chat?prompt=${encodeURIComponent(text)}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Copilot dialogue failed');
        const guidance = await res.json();
        
        const answer = `Based on your request, I recommend utilizing the **${guidance.recommended_model}** model preset. Camera panning advice: "${guidance.camera_path_recommendation}". Enhanced prompt generated: "${guidance.enhanced_prompt}"`;
        
        set((state) => ({
          copilotMessages: [...state.copilotMessages, { role: 'assistant', text: answer, payload: guidance }]
        }));
      } catch (err: any) {
        set((state) => ({
          copilotMessages: [...state.copilotMessages, { role: 'assistant', text: `Error processing copilot advice: ${err.message}` }]
        }));
      }
    },

    estimateRenderCost: async (duration, steps) => {
      const { token } = get();
      if (!token) throw new Error('Unauthorized');
      const res = await fetch(`${API_BASE_URL}/copilot/estimate?duration=${duration}&steps=${steps}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to estimate rendering cost');
      return res.json();
    },

    initWebsocket: () => {
      const { user, token } = get();
      if (!user || !token) return;

      if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        return;
      }

      console.log(`Opening WebSockets channel for user ID: ${user.id}`);
      socket = new WebSocket(`${WS_BASE_URL}/renders/ws/${user.id}`);

      socket.onopen = () => {
        set({ wsConnected: true });
        console.log('WebSocket connection established.');
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'pong') return;

          const { job_id, storyboard_id, audio_job_id, fine_tuning_job_id, progress, status, result_url, metrics, thumbnail_url, gif_url, metadata_url, error_message } = data;
          
          // MLOps fine-tuning job update
          if (fine_tuning_job_id) {
            set((state) => ({
              fineTuningJobs: state.fineTuningJobs.map(j => {
                if (j.id === fine_tuning_job_id) {
                  return {
                    ...j,
                    progress,
                    status,
                    metrics: metrics || j.metrics,
                    updated_at: new Date().toISOString()
                  };
                }
                return j;
              })
            }));
            
            if (status === 'SUCCESS' || status === 'FAILED') {
               get().fetchUser();
            }
            return;
          }

          // If audio job updates
          if (audio_job_id) {
            set((state) => ({
              audioJobs: state.audioJobs.map(j => {
                if (j.id === audio_job_id) {
                  return {
                    ...j,
                    progress,
                    status,
                    result_url: result_url || j.result_url,
                    error_message: error_message || j.error_message,
                    updated_at: new Date().toISOString()
                  };
                }
                return j;
              })
            }));
            
            if (status === 'SUCCESS' || status === 'FAILED') {
               get().fetchUser();
            }
            return;
          }

          // If storyboard rendering update
          if (storyboard_id) {
            set((state) => {
              const currentSb = state.activeStoryboard;
              const updatedActive = (currentSb && currentSb.id === storyboard_id)
                ? {
                    ...currentSb,
                    progress,
                    status,
                    result_url: result_url || currentSb.result_url,
                    error_message: error_message || currentSb.error_message,
                    updated_at: new Date().toISOString()
                  }
                : currentSb;

              return {
                storyboards: state.storyboards.map(s => {
                  if (s.id === storyboard_id) {
                    return {
                      ...s,
                      progress,
                      status,
                      result_url: result_url || s.result_url,
                      error_message: error_message || s.error_message,
                      updated_at: new Date().toISOString()
                    };
                  }
                  return s;
                }),
                activeStoryboard: updatedActive
              };
            });
            
            if (status === 'SUCCESS' || status === 'FAILED') {
               get().fetchUser();
            }
            return;
          }

          // If standard job update
          set((state) => ({
            renders: state.renders.map(r => {
              if (r.id === job_id) {
                return {
                  ...r,
                  progress,
                  status,
                  result_url: result_url || r.result_url,
                  thumbnail_url: thumbnail_url || r.thumbnail_url,
                  gif_url: gif_url || r.gif_url,
                  metadata_url: metadata_url || r.metadata_url,
                  error_message: error_message || r.error_message,
                  updated_at: new Date().toISOString()
                };
              }
              return r;
            })
          }));

          if (status === 'SUCCESS' || status === 'FAILED' || status === 'CANCELLED') {
            get().fetchUser();
            if (get().activeProject) {
              get().fetchAssets(get().activeProject!.id);
            }
          }
        } catch (e) {
          console.error('Error parsing WS event packet', e);
        }
      };

      socket.onclose = () => {
        set({ wsConnected: false });
        console.warn('WebSocket channel closed. Reconnecting in 5 seconds...');
        setTimeout(() => get().initWebsocket(), 5000);
      };

      socket.onerror = (err) => {
        console.error('WebSocket connection error:', err);
        if (socket) socket.close();
      };
    }
  };
});
