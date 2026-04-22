import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, ArrowRight, Loader2 } from 'lucide-react';
import { FaGithub } from 'react-icons/fa';
import { MessageBubble } from './MessageBubble';
import { CodeDrawer } from './CodeDrawer';
import { apiClient } from '../api';
import type { Message, Chunk } from '../types';
import { generateId, getOrCreateGuestSessionId, getCookie } from '../utils/session';
import { Toast } from './Toast';

const API_BASE = 'http://localhost:8000/api/v1';

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

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  
  // Streaming & Loading States
  const [isTyping, setIsTyping] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  
  const [activeChunk, setActiveChunk] = useState<Chunk | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isStreamingRef = useRef(false);

  useEffect(() => {
    if (conversationId) {
      apiClient.getMessages(conversationId).then(history => {
        if (isStreamingRef.current) return;

        if (history.length > 0) {
          setMessages(history);
        } else {
          setMessages([{ id: 'init', role: 'ai', content: `Successfully connected to \`${repoName}\`. What would you like to know?` }]);
        }
      });
    } else {
      setMessages([{ id: 'init', role: 'ai', content: `Successfully connected to \`${repoName}\`. What would you like to know?` }]);
    }
  }, [conversationId, repoName]);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, statusMessage]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    
    const userText = input.trim();
    const userMsgId = Date.now().toString();
    const aiMsgId = (Date.now() + 1).toString();
    
    const userMsg: Message = { id: userMsgId, role: 'user', content: userText };
    // Pre-inject the AI message so we can stream tokens into it
    const aiMsg: Message = { id: aiMsgId, role: 'ai', content: '' };
    
    setMessages(prev => [...prev, userMsg, aiMsg]);
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    
    setIsTyping(true);
    isStreamingRef.current = true;
    setStatusMessage("Initializing...");
    
    const currentConvId = conversationId || generateId();
    const guestId = getOrCreateGuestSessionId();
    const token = getCookie('access_token');

    if (!conversationId) {
      onConversationStarted(currentConvId, userText);
    }

    try {
      const response = await fetch(`${API_BASE}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          query: userText,
          repo_name: repoName,
          conversation_id: currentConvId,
          guest_session_id: guestId
        })
      });

      if (response.status === 429) {
        // Remove user's message from UI
        setMessages(prev => prev.filter(m => m.id !== userMsgId && m.id !== aiMsgId));

        // Restore user's text to the input field
        setInput(userText);

        // Trigger notification
        setToastMessage("You're doing that too fast. Please wait a moment.");

        return
      }

      if (!response.body) throw new Error("No readable stream");

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let buffer = '';
      let currentContent = '';
      let currentChunks: Chunk[] = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        // Decode and append to buffer to ensure we don't slice JSON mid-string
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        
        // Keep the last incomplete part in the buffer for the next chunk
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (part.startsWith('data: ')) {
            const jsonStr = part.replace(/^data:\s*/, '');
            if (!jsonStr.trim() || jsonStr === '[DONE]') continue;

            try {
              const data = JSON.parse(jsonStr);

              if (data.type === 'status') {
                setStatusMessage(data.message);
              } 
              else if (data.type === 'citations') {
                // Map the cited chunks and assign an ID based on array index
                currentChunks = (data.chunks || []).map((c: any, i: number) => ({ ...c, id: i }));
                
                // Attach chunks to the AI message
                setMessages(prev => prev.map(m => 
                  m.id === aiMsgId ? { ...m, chunks: currentChunks } : m
                ));

                // UX Requirement: Instantly pop open the drawer for the first citation
                if (currentChunks.length > 0) {
                  setActiveChunk(currentChunks[0]);
                  setIsDrawerOpen(true);
                }
              } 
              else if (data.type === 'token') {
                currentContent += data.content;
                // Append token to create the typewriter effect
                setMessages(prev => prev.map(m => 
                  m.id === aiMsgId ? { ...m, content: currentContent } : m
                ));
              } 
              else if (data.type === 'done') {
                setStatusMessage(null);
                setIsTyping(false);
              }
            } catch (e) {
              console.error("Stream parse error:", e, "Raw string:", jsonStr);
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => prev.map(m => 
        m.id === aiMsgId ? { ...m, content: "**Error:** Stream disconnected." } : m
      ));
    } finally {
      setIsTyping(false);
      setStatusMessage(null);
      isStreamingRef.current = false;
    }
  };

  return (
    <div className="flex flex-1 w-full h-full overflow-hidden bg-[#FAFAFA] dark:bg-[#0A0A0A]">
      <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
      <div className="flex flex-col flex-1 min-w-0 relative z-10">
        
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

        <main className="flex-1 overflow-y-auto px-6 pt-8 pb-32 scrollbar-thin">
          <div className="max-w-3xl mx-auto">
            {messages.map(msg => {
              // Hide the pre-injected AI bubble if it hasn't received any tokens or chunks yet
              if (msg.role === 'ai' && !msg.content && (!msg.chunks || msg.chunks.length === 0)) return null;
              
              return (
                <MessageBubble 
                  key={msg.id} 
                  message={msg} 
                  onCiteClick={(chunk) => { setActiveChunk(chunk); setIsDrawerOpen(true); }} 
                />
              );
            })}
            
            {/* The Animated Status Pill */}
            <AnimatePresence>
              {statusMessage && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0, scale: 0.95, filter: 'blur(4px)' }} 
                  className="flex w-full mb-6"
                >
                  <div className="bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-2xl px-4 py-2.5 shadow-sm flex items-center gap-3">
                    <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                    
                    {/* Mode="wait" allows the previous text to exit before the new text enters */}
                    <AnimatePresence mode="wait">
                      <motion.span
                        key={statusMessage}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        transition={{ duration: 0.2 }}
                        className="text-xs font-medium text-neutral-600 dark:text-neutral-300 tracking-wide"
                      >
                        {statusMessage}
                      </motion.span>
                    </AnimatePresence>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

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
              className="w-full max-h-48 py-3 pl-4 pr-12 text-sm bg-transparent border-none outline-none resize-none text-neutral-800 dark:text-neutral-200 placeholder:text-neutral-400 scrollbar-thin"
            />
            <button onClick={handleSend} disabled={!input.trim() || isTyping} className="absolute right-3 bottom-3 flex items-center justify-center w-8 h-8 transition-colors rounded-full bg-neutral-900 hover:bg-neutral-800 text-white dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200 disabled:opacity-50">
              <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </div>

      {/* Code Drawer Panel */}
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