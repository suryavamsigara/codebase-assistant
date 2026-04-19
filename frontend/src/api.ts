import type { 
  IndexRequest, 
  IndexResponse, 
  StatusResponse, 
  QueryRequest, 
  RawQueryResponse,
  NormalizedQueryResponse
} from './types';

const API_BASE = 'http://localhost:8000';

export const apiClient = {
  async indexRepository(payload: IndexRequest): Promise<IndexResponse> {
    const res = await fetch(`${API_BASE}/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
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
    const res = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error('Failed to query repository');
    }

    const data: RawQueryResponse = await res.json();

    // Normalize the data for the UI
    return {
      answer: data.answer,
      repo_name: data.repo_name,
      // Map 'cited_chunks' to 'chunks' and inject the array index as the 'id'
      chunks: (data.cited_chunks || []).map((chunk, index) => ({
        ...chunk,
        id: index // This ensures [app.py](#chunk-0) matches id: 0
      }))
    };
  },

  async getFileContent(repoName: string, filePath: string): Promise<string> {
    const params = new URLSearchParams({
      repo_name: repoName,
      file_path: filePath,
    });
    
    const res = await fetch(`${API_BASE}/file?${params.toString()}`, {
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
    const res = await fetch(`${API_BASE}/repos`);
    if (!res.ok) throw new Error('Failed to fetch repositories');
    return res.json();
  }
};