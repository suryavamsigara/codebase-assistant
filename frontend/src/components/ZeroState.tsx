import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaGithub } from 'react-icons/fa';
import {
  ArrowRight, 
  Loader2, 
  Terminal, 
  Clock, 
  FolderGit2, 
  ChevronRight,
  Database
} from 'lucide-react';
import { apiClient } from '../api';

interface ZeroStateProps {
  onIndexComplete: (repoName: string) => void;
}

// Mock data for the expanded UI
const RECENT_WORKSPACES = [
  { name: 'facebook/react', time: '2 hours ago', size: '142 MB', status: 'ready' },
  { name: 'tiangolo/fastapi', time: 'Yesterday', size: '28 MB', status: 'ready' },
  { name: 'hwchase17/langchain', time: '3 days ago', size: '86 MB', status: 'archived' }
];

export const ZeroState: React.FC<ZeroStateProps> = ({ onIndexComplete }) => {
  const [url, setUrl] = useState('');
  const [isIndexing, setIsIndexing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusText, setStatusText] = useState('Starting task...');

  const extractRepoData = (input: string) => {
    let cleanUrl = input.trim();
    
    // 1. Handle raw "user/repo" shorthand
    if (!cleanUrl.startsWith('http') && !cleanUrl.includes('github.com')) {
      const parts = cleanUrl.split('/').filter(Boolean);
      if (parts.length === 2) {
        const owner = parts[0];
        const repo = parts[1].replace('.git', '');
        return { 
          repoName: `${owner}_${repo}`, 
          fullUrl: `https://github.com/${owner}/${repo}` 
        };
      }
    }

    // 2. Handle missing "https://" (e.g., github.com/user/repo)
    if (!cleanUrl.startsWith('http')) {
      cleanUrl = `https://${cleanUrl}`;
    }

    // 3. Standard parsing for valid URLs
    try {
      const parsed = new URL(cleanUrl);
      const parts = parsed.pathname.split('/').filter(Boolean);
      if (parts.length >= 2) {
        const owner = parts[parts.length - 2];
        const repo = parts[parts.length - 1].replace('.git', '');
        
        return { repoName: `${owner}_${repo}`, fullUrl: cleanUrl }; 
      }
    } catch {
      return null;
    }
    
    return null;
  };
const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); 
    if (!url.trim() || isIndexing) return;
    
    const parsedData = extractRepoData(url);
    if (!parsedData) {
      setError("Invalid format. Use a full GitHub URL or 'user/repo'.");
      return;
    }

    setIsIndexing(true);
    setError(null);
    setStatusText('Contacting orchestrator...');

    try {
      const response = await apiClient.indexRepository({ 
        github_url: parsedData.fullUrl, 
        repo_name: parsedData.repoName 
      });
      
      // Fast-track transition if the database already has it COMPLETED
      if (response.message === "Repo is already indexed.") {
        setIsIndexing(false);
        onIndexComplete(parsedData.repoName); // <-- Fixed here
        return;
      }

      // Update UI if it's piggybacking on an existing PENDING/PROCESSING task
      if (response.message === "Repo is currently being indexed.") {
        setStatusText('Attaching to ongoing index task...');
      } else {
        setStatusText('Cloning remote source...');
      }
      
      // Begin polling for both new and existing incomplete tasks
      const pollInterval = setInterval(async () => {
        try {
          const { status } = await apiClient.checkTaskStatus(response.task_id);
          
          if (status === 'PROCESSING') {
            setStatusText('Generating embeddings via orchestrator...');
          } else if (status === 'SUCCESS' || status === 'COMPLETED') {
            clearInterval(pollInterval);
            setIsIndexing(false);
            onIndexComplete(parsedData.repoName); // <-- Fixed here
          } else if (status === 'FAILED' || status === 'FAILURE') {
            clearInterval(pollInterval);
            setIsIndexing(false);
            setError("Indexing failed on the server.");
          }
        } catch (err) {
          clearInterval(pollInterval);
          setIsIndexing(false);
          setError("Lost connection to indexing service.");
        }
      }, 2000);

    } catch (err) {
      setIsIndexing(false);
      setError("Failed to communicate with the indexing service.");
    }
  };

  return (
    <div className="flex flex-col min-h-screen lg:flex-row bg-[#FAFAFA] dark:bg-[#0A0A0A]">
      
      {/* Left Canvas: Active Initialization */}
      <div className="flex flex-col justify-center flex-1 p-8 md:p-16 lg:p-24 xl:p-32 z-10 relative bg-white dark:bg-[#0A0A0A] border-r border-neutral-200 dark:border-neutral-900 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-md w-full mx-auto lg:mx-0"
        >
          <div className="flex items-center gap-3 mb-10 text-neutral-900 dark:text-white">
            <div className="p-3 bg-neutral-100 dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800">
              <Terminal className="w-6 h-6" strokeWidth={1.5} />
            </div>
            <span className="text-sm font-semibold tracking-widest uppercase text-neutral-400">RAG Orchestrator</span>
          </div>

          <h1 className="mb-4 text-4xl font-medium tracking-tight text-neutral-900 dark:text-white">
            Initialize Workspace
          </h1>
          <p className="mb-10 text-base leading-relaxed text-neutral-500 dark:text-neutral-400">
            Provide a GitHub repository URL. The orchestrator will clone the source, embed the chunks, and prepare the semantic index.
          </p>
          
          <form onSubmit={handleSubmit} className="relative">
            <div className="relative flex items-center overflow-hidden transition-all duration-300 bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-2xl focus-within:border-neutral-400 dark:focus-within:border-neutral-600 focus-within:ring-4 focus-within:ring-neutral-100 dark:focus-within:ring-neutral-800/50 shadow-sm">
              <div className="pl-4 text-neutral-400">
                <FaGithub className="w-5 h-5" />
              </div>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/user/repo"
                disabled={isIndexing}
                className="w-full py-4 pl-3 pr-16 text-base bg-transparent border-none outline-none text-neutral-800 dark:text-neutral-200 placeholder:text-neutral-400"
              />
              <button
                type="submit"
                disabled={!url.trim() || isIndexing}
                className="absolute right-2 p-2.5 text-white transition-all rounded-xl bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {isIndexing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ArrowRight className="w-4 h-4" />
                )}
              </button>
            </div>
            
            <AnimatePresence>
              {error && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 text-sm font-medium text-red-500"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
          </form>

          {/* Indexing Status Feedback */}
          <AnimatePresence>
            {isIndexing && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-4 mt-8 border bg-neutral-50 dark:bg-neutral-900/50 border-neutral-200 dark:border-neutral-800 rounded-2xl"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                  <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                    Processing Repository
                  </span>
                </div>
                <div className="pl-7">
                  <div className="text-xs text-neutral-500 flex justify-between">
                    <span>{statusText}</span>
                    <span className="text-blue-500 animate-pulse">Running</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Right Canvas: Context & History */}
      <div className="hidden lg:flex flex-col flex-1 p-8 md:p-16 xl:p-24 bg-[#FAFAFA] dark:bg-[#0A0A0A]/40 relative overflow-y-auto">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="max-w-xl w-full mx-auto"
        >
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">Recent Workspaces</h2>
            <button className="text-xs font-medium text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-300 transition-colors">
              View All
            </button>
          </div>

          <div className="grid gap-3">
            {RECENT_WORKSPACES.map((workspace, idx) => (
              <button 
                key={idx}
                onClick={() => onIndexComplete(workspace.name)} 
                className="group flex items-center justify-between p-4 bg-white dark:bg-neutral-900 border border-neutral-200/60 dark:border-neutral-800/60 rounded-2xl hover:border-neutral-300 dark:hover:border-neutral-600 transition-all shadow-sm hover:shadow-md text-left"
              >
                <div className="flex items-center gap-4">
                  <div className="p-2.5 bg-neutral-50 dark:bg-neutral-950 rounded-xl text-neutral-500 group-hover:text-neutral-900 dark:group-hover:text-neutral-200 transition-colors">
                    <FolderGit2 className="w-5 h-5" strokeWidth={1.5} />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 tracking-tight mb-0.5">
                      {workspace.name}
                    </h3>
                    <div className="flex items-center gap-3 text-xs text-neutral-500">
                      <span className="flex items-center gap-1.5"><Clock className="w-3 h-3" /> {workspace.time}</span>
                      <span className="flex items-center gap-1.5"><Database className="w-3 h-3" /> {workspace.size}</span>
                    </div>
                  </div>
                </div>
                <div className="text-neutral-300 dark:text-neutral-700 group-hover:text-neutral-900 dark:group-hover:text-neutral-300 transition-colors transform group-hover:translate-x-1 duration-200">
                  <ChevronRight className="w-5 h-5" />
                </div>
              </button>
            ))}
          </div>

          <div className="mt-12 p-6 bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100/50 dark:border-blue-900/30 rounded-2xl">
            <h4 className="text-xs font-semibold text-blue-800 dark:text-blue-400 uppercase tracking-wider mb-2">Pro Tip</h4>
            <p className="text-sm text-blue-900/70 dark:text-blue-300/70 leading-relaxed">
              Large repositories may take up to a minute to index. The orchestrator automatically chunks files by structural boundaries to maintain high semantic search accuracy.
            </p>
          </div>
        </motion.div>
      </div>

    </div>
  );
};