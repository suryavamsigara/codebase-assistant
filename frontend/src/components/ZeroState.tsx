import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaGithub } from 'react-icons/fa';
import { 
  ArrowRight, 
  Loader2, 
  Terminal,
  PanelLeftClose, 
  PanelLeftOpen, 
  UserCircle 
} from 'lucide-react';
import { apiClient } from '../api';
import type { User } from '../types';
import { Toast } from './Toast';

interface ZeroStateProps {
  onIndexComplete: (repoName: string) => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  user: User | null;
  onOpenAuth: () => void;
}

export const ZeroState: React.FC<ZeroStateProps> = ({ 
  onIndexComplete, 
  isSidebarOpen, 
  onToggleSidebar, 
  user, 
  onOpenAuth 
}) => {
  const [url, setUrl] = useState('');
  const [isIndexing, setIsIndexing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusText, setStatusText] = useState('Starting task...');

  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const extractRepoData = (input: string) => {
    let cleanUrl = input.trim();
    
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

    if (!cleanUrl.startsWith('http')) {
      cleanUrl = `https://${cleanUrl}`;
    }

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
      
      if (response.message === "Repo is already indexed.") {
        setIsIndexing(false);
        onIndexComplete(parsedData.repoName);
        return;
      }

      if (response.message === "Repo is currently being indexed.") {
        setStatusText('Attaching to ongoing index task...');
      } else {
        setStatusText('Cloning remote source...');
      }
      
      const pollInterval = setInterval(async () => {
        try {
          const { status } = await apiClient.checkTaskStatus(response.task_id);
          
          if (status === 'PROCESSING') {
            setStatusText('Generating embeddings via orchestrator...');
          } else if (status === 'SUCCESS' || status === 'COMPLETED') {
            clearInterval(pollInterval);
            setIsIndexing(false);
            onIndexComplete(parsedData.repoName);
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

    } catch (err: any) {
      setIsIndexing(false);
      
      if (err.message === '429') {
        setToastMessage("You're doing that too fast. Please wait a moment.");
      } else {
        setError("Failed to communicate with the indexing service.");
      }
    }
  };

  return (
    <div className="flex-1 w-full h-full flex flex-col items-center justify-center p-6 bg-[#FAFAFA] dark:bg-[#0A0A0A] relative overflow-hidden">
      <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
      
      {/* Floating Top Navigation */}
      <header className="absolute top-0 left-0 w-full flex items-center justify-between p-4 md:p-6 z-20 pointer-events-none">
        <div className="pointer-events-auto">
          <button 
            onClick={onToggleSidebar}
            className="p-2 text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200 transition-colors rounded-xl hover:bg-black/5 dark:hover:bg-white/10"
          >
            {isSidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
          </button>
        </div>

        <div className="pointer-events-auto">
          {!user ? (
            <button 
              onClick={onOpenAuth}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-200 bg-white/50 dark:bg-[#1C1C1E]/50 backdrop-blur-xl border border-black/5 dark:border-white/10 rounded-full hover:bg-white/80 dark:hover:bg-[#1C1C1E]/80 transition-all shadow-sm"
            >
              <UserCircle className="w-4 h-4" />
              Sign In
            </button>
          ) : (
            <div className="flex items-center justify-center w-9 h-9 rounded-full bg-gradient-to-tr from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-800/40 text-blue-600 dark:text-blue-400 font-medium shadow-sm border border-black/5 dark:border-white/10">
              {user.name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
      </header>

      {/* Background ambient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[250px] h-[250px] bg-blue-500/5 dark:bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.6, 1, 0.3, 1] }}
        className="relative w-full max-w-xl flex flex-col items-center z-10"
      >
        <div className="p-3 mb-8 bg-black/5 dark:bg-white/5 rounded-2xl border border-black/5 dark:border-white/5 shadow-sm">
          <Terminal className="w-6 h-6 text-neutral-700 dark:text-neutral-300" strokeWidth={1.5} />
        </div>
        
        <h1 className="mb-3 text-3xl font-medium tracking-tight text-neutral-900 dark:text-white">
          CodeLens
        </h1>
        <p className="mb-12 text-[15px] text-center text-neutral-500 dark:text-neutral-400">
          Understand any codebase instantly
        </p>
        
        <form onSubmit={handleSubmit} className="w-full">
          <div className="relative flex items-center p-2 bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-2xl border border-black/5 dark:border-white/10 shadow-[0_12px_40px_-10px_rgba(0,0,0,0.08)] rounded-[2rem] focus-within:ring-4 focus-within:ring-black/5 dark:focus-within:ring-white/5 transition-all">
            <div className="pl-4 text-neutral-400">
              <FaGithub className="w-[18px] h-[18px]" />
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              disabled={isIndexing}
              className="w-full py-3.5 pl-4 pr-14 text-[15px] bg-transparent border-none outline-none text-neutral-800 dark:text-neutral-200 placeholder:text-neutral-400"
            />
            <div className="absolute right-2.5">
              <button
                type="submit"
                disabled={!url.trim() || isIndexing}
                className="flex items-center justify-center w-10 h-10 text-white transition-all rounded-full bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {isIndexing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ArrowRight className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
          
          <div className="h-10 mt-4 flex items-center justify-center text-sm">
            <AnimatePresence mode="wait">
              {error ? (
                <motion.span 
                  key="error"
                  initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="text-red-500 font-medium"
                >
                  {error}
                </motion.span>
              ) : isIndexing ? (
                <motion.div 
                  key="indexing"
                  initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="flex items-center gap-2.5 text-neutral-500 dark:text-neutral-400"
                >
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                  <span>{statusText}</span>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>
        </form>

        <p className="mt-8 text-[13px] text-center text-neutral-400 dark:text-neutral-500 max-w-sm leading-relaxed">
          Indexing may take a moment for large repositories.
        </p>

      </motion.div>
    </div>
  );
};