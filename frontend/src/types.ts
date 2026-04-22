export type Role = 'user' | 'ai';

export interface User {
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user?: User; // Login might not return user based on your snippet, but register does
}

export interface Chunk {
  id: number;
  file_path: string;
  start_line: number;
  end_line: number;
  type?: string;
  name?: string;
  language: string;
  code: string;
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  chunks?: Chunk[];
}

export interface Conversation {
  id: string;
  repo_name: string;
  created_at: string;
  preview_text?: string; // show the first message in the sidebar
  name: string;
}

export interface IndexRequest {
  github_url: string;
  repo_name: string;
}

export interface IndexResponse {
  task_id: string;
  repo_name: string;
  message: string;
  estimated_seconds?: number;
}

export interface StatusResponse {
  task_id: string;
  status: string; // e.g., 'PENDING', 'SUCCESS', 'FAILURE'
}

export interface QueryRequest {
  query: string;
  repo_name: string;
  conversation_id: string;
  guest_session_id: string;
}

export interface RawQueryResponse {
  answer: string;
  repo_name: string;
  cited_chunks: Omit<Chunk, 'id'>[]; 
}

export interface NormalizedQueryResponse {
  answer: string;
  repo_name: string;
  chunks: Chunk[];
}