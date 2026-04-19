import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaGithub } from 'react-icons/fa';
import { ArrowRight, Loader2, PanelRightOpen, PanelRightClose } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { CodeDrawer } from './CodeDrawer';
import { apiClient } from '../api';
import type { Message, Chunk } from '../types';

interface WorkspaceProps {
  repoName: string;
}

export const Workspace: React.FC<WorkspaceProps> = ({ repoName }) => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'ai', content: `Successfully connected to \`${repoName}\`. What would you like to know?` }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // Drawer State
  const [activeChunk, setActiveChunk] = useState<Chunk | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    
    setIsTyping(true);
    try {
      const response = await apiClient.queryRepository({ query: userMsg.content, repo_name: repoName });
      const aiMsg: Message = { 
        id: (Date.now() + 1).toString(), 
        role: 'ai', 
        content: response.answer,
        chunks: response.chunks 
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'ai', content: "**Error:** Failed to reach RAG API." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleCitationClick = (chunk: Chunk) => {
    setActiveChunk(chunk);
    setIsDrawerOpen(true);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#FAFAFA] dark:bg-[#0A0A0A]">
      
      {/* Left Panel: Chat Interface */}
      <div className="flex flex-col flex-1 min-w-0 relative z-10 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
        
        <header className="flex items-center justify-between h-14 px-6 border-b border-black/5 dark:border-white/5 bg-white/70 dark:bg-[#0A0A0A]/70 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <FaGithub className="w-4 h-4 text-neutral-700 dark:text-neutral-300" />
            <span className="text-sm font-medium text-neutral-800 dark:text-neutral-200 font-mono tracking-tight">
              {repoName}
            </span>
          </div>
          
          <button 
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            disabled={!activeChunk}
            className={`p-1.5 rounded-lg transition-colors ${
              isDrawerOpen 
                ? 'bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400' 
                : 'text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800'
            } disabled:opacity-30 disabled:cursor-not-allowed`}
          >
            {isDrawerOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
          </button>
        </header>

        <main className="flex-1 overflow-y-auto px-6 pt-8 pb-32 scrollbar-thin">
          <div className="max-w-3xl mx-auto">
            {messages.map(msg => (
              <MessageBubble 
                key={msg.id} 
                message={msg} 
                onCiteClick={handleCitationClick}
              />
            ))}
            {isTyping && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex w-full mb-6">
                <div className="bg-white dark:bg-[#1C1C1E] border border-neutral-200 dark:border-neutral-800 rounded-2xl px-4 py-3 flex gap-2">
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                </div>
              </motion.div>
            )}
            <div ref={endOfMessagesRef} />
          </div>
        </main>

        {/* Input */}
        <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-[#FAFAFA] via-[#FAFAFA]/90 to-transparent dark:from-[#0A0A0A] dark:via-[#0A0A0A]/90 pt-10 pb-6 px-6">
          <div className="max-w-3xl mx-auto relative flex items-end p-2 bg-white dark:bg-[#1C1C1E] border border-neutral-200 dark:border-neutral-800 shadow-[0_8px_30px_rgb(0,0,0,0.08)] rounded-[2rem]">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask about the codebase..."
              rows={1}
              className="w-full max-h-48 py-3 pl-4 pr-12 text-sm bg-transparent border-none outline-none resize-none text-neutral-800 dark:text-neutral-200 placeholder:text-neutral-400 scrollbar-hide"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="absolute right-3 bottom-3 flex items-center justify-center w-8 h-8 transition-colors rounded-full bg-neutral-900 hover:bg-neutral-800 text-white dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200 disabled:opacity-50"
            >
              <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel: Sliding Drawer */}
      <AnimatePresence>
        {isDrawerOpen && activeChunk && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: '40vw', opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", bounce: 0, duration: 0.4 }}
            className="border-l border-neutral-200 dark:border-neutral-800 overflow-hidden flex-shrink-0"
          >
            <div className="w-[40vw] h-full min-w-[300px]">
              <CodeDrawer 
                repoName={repoName} 
                chunk={activeChunk} 
                onClose={() => setIsDrawerOpen(false)} 
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
    </div>
  );
};