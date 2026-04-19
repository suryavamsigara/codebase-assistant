import { useState, useEffect } from 'react';
import { BrowserRouter, useNavigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { ZeroState } from './components/ZeroState';
import { Workspace } from './components/Workspace';
import { Sidebar } from './components/Sidebar';
import { AuthModal } from './components/AuthModal';
import { apiClient } from './api';
import type { User, Conversation } from './types';
import { setCookie, removeCookie, getCookie, getOrCreateGuestSessionId } from './utils/session';

// We extract the main logic into a sub-component so we can use React Router hooks (useNavigate, useParams)
const AppLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  
  const [activeRepo, setActiveRepo] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Extract the conversation ID from the URL (e.g., /chat/12345 -> '12345')
  const urlMatch = location.pathname.match(/\/chat\/(.+)/);
  const activeConversationId = urlMatch ? urlMatch[1] : null;

  // 1. Initial Load & Auth Check
  useEffect(() => {
    const initApp = async () => {
      const token = getCookie('access_token');
      if (token) {
        try {
          const userData = await apiClient.getMe(); // Fetch real name from backend
          setUser(userData);
        } catch {
          removeCookie('access_token');
        }
      }

      // Fetch sidebar history based on user/guest
      const guestId = getOrCreateGuestSessionId();
      const history = await apiClient.getConversations(guestId);
      setConversations(history);
    };
    initApp();
  }, []);

  // 2. Sync activeRepo when the URL changes
  useEffect(() => {
    if (activeConversationId) {
      const conv = conversations.find(c => c.id === activeConversationId);
      if (conv) {
        setActiveRepo(conv.repo_name);
      }
    }
  }, [activeConversationId, conversations]);

  // Auth Handlers
  const handleAuthSuccess = async (userData: User, token: string) => {
    setUser(userData);
    setCookie('access_token', token, 30);
    
    // Re-fetch conversations for the newly logged-in user
    const guestId = getOrCreateGuestSessionId();
    const history = await apiClient.getConversations(guestId);
    setConversations(history);
  };

  const handleLogout = () => {
    setUser(null);
    setConversations([]); // Purge history from UI immediately
    removeCookie('access_token');
    setActiveRepo(null);
    navigate('/'); // Kick them back to the home screen
  };

  // Chat Handlers
  const handleNewChat = () => {
    setActiveRepo(null); 
    navigate('/'); 
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
    navigate(`/chat/${convId}`); // Change the URL dynamically
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
                navigate(`/chat/${conv.id}`); // Route via React Router
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
          {!activeRepo && !activeConversationId ? (
            <motion.div key="zero" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 w-full">
              <ZeroState 
                onIndexComplete={(repoName) => {
                  setActiveRepo(repoName);
                  // Stay on '/' until they send the first message, which triggers onConversationStarted
                }} 
              />
            </motion.div>
          ) : (
            <motion.div key="workspace" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 w-full flex">
              <Workspace 
                repoName={activeRepo || "Loading..."}
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
};

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}