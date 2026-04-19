import { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ZeroState } from './components/ZeroState';
import { Workspace } from './components/Workspace';
import { Sidebar } from './components/Sidebar';
import { AuthModal } from './components/AuthModal';
import { apiClient } from './api';
import type { User, Conversation } from './types';
import { setCookie, removeCookie, getCookie, getOrCreateGuestSessionId } from './utils/session';

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  
  const [activeRepo, setActiveRepo] = useState<string | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Initial Load: Auth Check & History Fetch
  useEffect(() => {
    const initApp = async () => {
      // 1. Check if logged in (mocking user fetch via token existence for now)
      const token = getCookie('access_token');
      if (token) {
        // Ideally: const userData = await apiClient.getMe();
        setUser({ name: 'Developer', email: 'dev@example.com' }); 
      }

      // 2. Fetch sidebar history
      const guestId = getOrCreateGuestSessionId();
      const history = await apiClient.getConversations(guestId);
      setConversations(history);
      
      // Optional: Auto-load the most recent conversation
      if (history.length > 0) {
        setActiveRepo(history[0].repo_name);
        setActiveConversationId(history[0].id);
      }
    };
    initApp();
  }, []);

  const handleAuthSuccess = (userData: User, token: string) => {
    setUser(userData);
    setCookie('access_token', token, 30); // Save token securely in cookies for 30 days
  };

  const handleLogout = () => {
    setUser(null);
    removeCookie('access_token');
  };

  const handleNewChat = () => {
    setActiveConversationId(null);
    setActiveRepo(null); // Going back to ZeroState to pick a repo
  };

  const handleConversationStarted = (convId: string, previewText: string) => {
    if (!activeRepo) return;
    
    const newConv: Conversation = {
      id: convId,
      repo_name: activeRepo,
      created_at: new Date().toISOString(),
      preview_text: previewText
    };
    
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(convId);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#FAFAFA] dark:bg-[#0A0A0A] font-sans text-neutral-900 dark:text-neutral-100 selection:bg-blue-200 dark:selection:bg-blue-900">
      
      {/* Persistent Left Sidebar */}
      <AnimatePresence initial={false}>
        {isSidebarOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 256, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", bounce: 0, duration: 0.4 }}
            className="flex-shrink-0 z-30"
          >
            <Sidebar 
              user={user}
              activeConversationId={activeConversationId}
              conversations={conversations}
              onSelectConversation={(conv) => {
                setActiveRepo(conv.repo_name);
                setActiveConversationId(conv.id);
              }}
              onNewChat={handleNewChat}
              onOpenAuth={() => setIsAuthModalOpen(true)}
              onLogout={handleLogout}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Routing Area */}
      <div className="flex-1 min-w-0 relative z-10 flex">
        <AnimatePresence mode="wait">
          {!activeRepo ? (
            <motion.div key="zero" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 w-full">
              <ZeroState 
                onIndexComplete={(repoName) => {
                  setActiveRepo(repoName);
                  setActiveConversationId(null); // Ready for a new chat
                }} 
              />
            </motion.div>
          ) : (
            <motion.div key="workspace" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 w-full flex">
              <Workspace 
                repoName={activeRepo}
                conversationId={activeConversationId}
                isSidebarOpen={isSidebarOpen}
                onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
                onConversationStarted={handleConversationStarted}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={handleAuthSuccess}
      />
    </div>
  );
}