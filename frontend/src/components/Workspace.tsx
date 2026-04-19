import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, ArrowRight, Loader2 } from 'lucide-react';
import { FaGithub } from 'react-icons/fa';
import { MessageBubble } from './MessageBubble';
import { CodeDrawer } from './CodeDrawer';
import { apiClient } from '../api';
import type { Message, Chunk } from '../types';
import { generateId, getOrCreateGuestSessionId } from '../utils/session';

interface WorkspaceProps {
  repoName: string;
  conversationId: string | null;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  onConversationStarted: (convId: string, previewText: string) => void;
}

export const Workspace: React.FC<WorkspaceProps> = ({ 
  repoName, conversationId, isSidebarOpen, onToggleSidebar, onConversationStarted 
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [activeChunk, setActiveChunk] = useState<Chunk | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load messages when conversationId changes
  useEffect(() => {
    if (conversationId) {
      apiClient.getMessages(conversationId).then(history => {
        if (history.length > 0) {
          setMessages(history);
        } else {
          setMessages([{ id: 'init', role: 'ai', content: `Successfully connected to \`${repoName}\`. What would you like to know?` }]);
        }
      });
    } else {
      // New Chat scenario
      setMessages([{ id: 'init', role: 'ai', content: `Successfully connected to \`${repoName}\`. What would you like to know?` }]);
    }
  }, [conversationId, repoName]);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    
    const userText = input.trim();
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: userText };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setIsTyping(true);
    
    // Crucial: Determine the ID. If it's a new chat, generate one now.
    const currentConvId = conversationId || generateId();
    const guestId = getOrCreateGuestSessionId();

    try {
      const response = await apiClient.queryRepository({ 
        query: userText, 
        repo_name: repoName,
        conversation_id: currentConvId,
        guest_session_id: guestId
      });
      
      const aiMsg: Message = { 
        id: (Date.now() + 1).toString(), 
        role: 'ai', 
        content: response.answer,
        chunks: response.chunks 
      };
      
      setMessages(prev => [...prev, aiMsg]);

      // If this was a new chat, notify the parent (App.tsx) to update the sidebar
      if (!conversationId) {
        onConversationStarted(currentConvId, userText);
      }

    } catch (error) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'ai', content: "**Error:** Failed to reach RAG API." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    // RESTORED: Horizontal flex container for the entire workspace
    <div className="flex flex-1 w-full h-full overflow-hidden bg-[#FAFAFA] dark:bg-[#0A0A0A]">
      
      {/* LEFT PANE: Main Chat Area */}
      {/* flex-1 allows this to shrink when the drawer opens */}
      <div className="flex flex-col flex-1 min-w-0 relative z-10">
        
        {/* Header */}
        <header className="flex items-center justify-between h-14 px-4 border-b border-black/5 dark:border-white/5 bg-white/70 dark:bg-[#0A0A0A]/70 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <button onClick={onToggleSidebar} className="p-1.5 text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200 transition-colors rounded-lg hover:bg-black/5 dark:hover:bg-white/10">
              {isSidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
            </button>
            <div className="h-4 w-px bg-neutral-200 dark:bg-neutral-800 mx-1" />
            <FaGithub className="w-4 h-4 text-neutral-700 dark:text-neutral-300" />
            <span className="text-sm font-medium text-neutral-800 dark:text-neutral-200 font-mono tracking-tight">
              {repoName}
            </span>
          </div>
          
          <button onClick={() => setIsDrawerOpen(!isDrawerOpen)} disabled={!activeChunk} className={`p-1.5 rounded-lg transition-colors ${isDrawerOpen ? 'bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400' : 'text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800'} disabled:opacity-30 disabled:cursor-not-allowed`}>
            {isDrawerOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
          </button>
        </header>

        {/* Main Chat Feed */}
        <main className="flex-1 overflow-y-auto px-6 pt-8 pb-32 scrollbar-thin">
          <div className="max-w-3xl mx-auto">
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} onCiteClick={(chunk) => { setActiveChunk(chunk); setIsDrawerOpen(true); }} />
            ))}
            {isTyping && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex w-full mb-6">
                <div className="bg-white dark:bg-[#1C1C1E] border border-neutral-200 dark:border-neutral-800 rounded-2xl px-4 py-3 flex gap-2 shadow-sm">
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                </div>
              </motion.div>
            )}
            <div ref={endOfMessagesRef} />
          </div>
        </main>

        {/* Input Dock */}
        <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-[#FAFAFA] via-[#FAFAFA]/90 to-transparent dark:from-[#0A0A0A] dark:via-[#0A0A0A]/90 pt-10 pb-6 px-6 pointer-events-none">
          <div className="max-w-3xl mx-auto relative flex items-end p-2 bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-2xl border border-black/5 dark:border-white/10 shadow-[0_8px_30px_rgb(0,0,0,0.08)] rounded-[2rem] pointer-events-auto">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                if (textareaRef.current) {
                  textareaRef.current.style.height = 'auto';
                  textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
                }
              }}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask about the codebase..."
              rows={1}
              className="w-full max-h-48 py-3 pl-4 pr-12 text-sm bg-transparent border-none outline-none resize-none text-neutral-800 dark:text-neutral-200 placeholder:text-neutral-400 scrollbar-hide"
            />
            <button onClick={handleSend} disabled={!input.trim() || isTyping} className="absolute right-3 bottom-3 flex items-center justify-center w-8 h-8 transition-colors rounded-full bg-neutral-900 hover:bg-neutral-800 text-white dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200 disabled:opacity-50">
              <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT PANE: Sliding Code Drawer */}
      {/* flex-shrink-0 ensures it doesn't get crushed by the chat container */}
      <AnimatePresence initial={false}>
        {isDrawerOpen && activeChunk && (
          <motion.div 
            initial={{ width: 0, opacity: 0 }} 
            animate={{ width: '40vw', opacity: 1 }} 
            exit={{ width: 0, opacity: 0 }} 
            transition={{ type: "spring", bounce: 0, duration: 0.4 }} 
            className="border-l border-neutral-200 dark:border-neutral-800 overflow-hidden bg-[#0A0A0C] z-20 flex-shrink-0"
          >
            <div className="w-[40vw] h-full min-w-[320px]">
              <CodeDrawer repoName={repoName} chunk={activeChunk} onClose={() => setIsDrawerOpen(false)} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};