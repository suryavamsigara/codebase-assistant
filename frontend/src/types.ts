export type Role = 'user' | 'ai';

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

export interface IndexRequest {
  github_url: string;
  repo_name: string;
}

export interface IndexResponse {
  task_id: string;
  repo_name: string;
  message: string;
}

export interface StatusResponse {
  task_id: string;
  status: string; // e.g., 'PENDING', 'SUCCESS', 'FAILURE'
}

export interface QueryRequest {
  query: string;
  repo_name: string;
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