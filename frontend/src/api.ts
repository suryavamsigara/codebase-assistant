import type { 
  User,
  IndexRequest, 
  IndexResponse, 
  StatusResponse, 
  QueryRequest, 
  RawQueryResponse,
  NormalizedQueryResponse,
  AuthResponse,
  Message,
  Conversation,
} from './types';
import { getCookie } from './utils/session';

const API_BASE = 'http://localhost:8000/api/v1';

const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const token = getCookie('access_token');
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  return fetch(url, { ...options, headers });
};

export const apiClient = {
  async getMe(): Promise<User> {
    const res = await fetchWithAuth(`${API_BASE}/auth/users/me`);
    if (!res.ok) {
      throw new Error('Not authenticated');
    }
    return res.json();
  },

  async register(name: string, email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });
    
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Registration failed');
    }
    return res.json();
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    // FastAPI OAuth2PasswordRequestForm requires URL-encoded data, mapping email to 'username'
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });
    
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Login failed');
    }
    return res.json();
  },

  async getConversations(guestSessionId: string): Promise<Conversation[]> {
    const res = await fetchWithAuth(`${API_BASE}/conversations?guest_session_id=${guestSessionId}`);
    if (!res.ok) return []; // Fallback to empty if endpoint doesn't exist yet
    return res.json();
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    const res = await fetchWithAuth(`${API_BASE}/conversations/${conversationId}/messages`);
    if (!res.ok) return []; 
    
    const data = await res.json();
    // Assuming backend returns { role, content, cited_chunks }
    return data.map((msg: any) => ({
      id: msg.id.toString(),
      role: msg.role,
      content: msg.content,
      chunks: (msg.cited_chunks || []).map((chunk: any, i: number) => ({ ...chunk, id: i }))
    }));
  },

  async deleteConversation(conversationId: string, guestSessionId: string): Promise<void> {
    const res = await fetchWithAuth(`${API_BASE}/conversations/${conversationId}?guest_session_id=${guestSessionId}`, {
      method: 'DELETE',
    });

    if (!res.ok) {
      throw new Error('Failed to delete conversation');
    }
  },

  async indexRepository(payload: IndexRequest): Promise<IndexResponse> {
    const res = await fetch(`${API_BASE}/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.status === 429) {
      throw new Error('429');
    }
    if (res.status === 400) throw new Error('400');
    if (!res.ok) throw new Error('Failed to start indexing');
    return res.json();
  },

  async checkTaskStatus(taskId: string): Promise<StatusResponse> {
    const res = await fetch(`${API_BASE}/index/status/${taskId}`);
    if (!res.ok) {
      throw new Error('Failed to fetch status');
    }
    return res.json();
  },

  async queryRepository(payload: QueryRequest): Promise<NormalizedQueryResponse> {
    const res = await fetchWithAuth(`${API_BASE}/query/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!res.ok) throw new Error('Failed to query repository');
    const data: RawQueryResponse = await res.json();
    
    return {
      answer: data.answer,
      repo_name: data.repo_name,
      chunks: (data.cited_chunks || []).map((chunk, index) => ({ ...chunk, id: index }))
    };
  },

  async getFileContent(repoName: string, filePath: string): Promise<string> {
    const params = new URLSearchParams({
      repo_name: repoName,
      file_path: filePath,
    });
    
    const res = await fetch(`${API_BASE}/query/file?${params.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    
    if (!res.ok) {
      throw new Error('Failed to fetch file content');
    }
    
    const data = await res.json();
    // The backend returns { repo_name, file_path, content }
    return data.content; 
  },

  async listRepositories(): Promise<{ repos: string[] }> {
    const res = await fetch(`${API_BASE}/index/repos`);
    if (!res.ok) throw new Error('Failed to fetch repositories');
    return res.json();
  }
};