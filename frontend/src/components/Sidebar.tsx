import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, UserCircle, LogOut, Trash2 } from 'lucide-react';
import { FaGithub } from 'react-icons/fa';
import type { User, Conversation } from '../types';

interface SidebarProps {
  user: User | null;
  activeConversationId: string | null;
  conversations: Conversation[];
  onSelectConversation: (conv: Conversation) => void;
  onDeleteConversation: (id: string) => void;
  onNewChat: () => void;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  user, activeConversationId, conversations, onSelectConversation, onDeleteConversation, onNewChat, onOpenAuth, onLogout 
}) => {
  
  const groupedConversations = conversations.reduce((acc, conv) => {
    if (!acc[conv.repo_name]) acc[conv.repo_name] = [];
    acc[conv.repo_name].push(conv);
    return acc;
  }, {} as Record<string, Conversation[]>);

  return (
    <div className="flex flex-col h-full w-64 bg-white/50 dark:bg-[#1C1C1E]/80 backdrop-blur-xl border-r border-black/5 dark:border-white/5 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
      <div className="p-4">
        <button 
          onClick={onNewChat}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-200 bg-black/5 hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-6 scrollbar-thin">
        {Object.entries(groupedConversations).map(([repoName, convs]) => (
          <div key={repoName} className="px-2">
            <div className="flex items-center gap-2 mb-2 text-xs font-mono font-medium text-neutral-400 dark:text-neutral-500 uppercase tracking-wider">
              <FaGithub className="w-3 h-3" />
              {repoName.split('/').pop()}
            </div>
            
            <div className="space-y-0.5">
              <AnimatePresence initial={false}>
                {convs.map(conv => {
                  const isActive = activeConversationId === conv.id;
                  return (
                    <motion.div
                      key={conv.id}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0, overflow: 'hidden' }}
                      transition={{ duration: 0.2, ease: "easeInOut" }}
                      className={`group relative flex items-center w-full rounded-md transition-colors ${
                        isActive
                          ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400'
                          : 'text-neutral-800 dark:text-white/90 hover:bg-black/5 dark:hover:bg-white/5'
                      }`}
                    >
                      <button
                        onClick={() => onSelectConversation(conv)}
                        className="flex flex-1 items-center gap-2 text-left px-3 py-2 text-sm truncate"
                      >
                        <span className="truncate font-medium pr-6">
                          {conv.name || 'New Conversation'}
                        </span>
                      </button>

                      {/* The Hover-Triggered Trash Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation(); // Prevents triggering the select conversation click
                          onDeleteConversation(conv.id);
                        }}
                        className="absolute right-1.5 p-1.5 opacity-0 group-hover:opacity-100 transition-all rounded-md text-neutral-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10"
                        title="Delete Chat"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-black/5 dark:border-white/5">
        {user ? (
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-tr from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-800/40 text-blue-600 dark:text-blue-400 font-medium text-xs flex-shrink-0">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <span className="text-sm font-medium text-neutral-700 dark:text-neutral-200 truncate">
                {user.name}
              </span>
            </div>
            <button onClick={onLogout} className="p-1.5 text-neutral-400 hover:text-red-500 transition-colors rounded-md hover:bg-red-50 dark:hover:bg-red-500/10 flex-shrink-0">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button onClick={onOpenAuth} className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-200 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg transition-colors">
            <UserCircle className="w-5 h-5 text-neutral-400" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </div>
  );
};