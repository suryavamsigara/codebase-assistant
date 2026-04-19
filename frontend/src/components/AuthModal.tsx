import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2 } from 'lucide-react';
import { apiClient } from '../api';
import type { User } from '../types';

interface AuthModalProps {
  onSuccess: (user: User, token: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onSuccess }) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Read auth state from the URL
  const queryParams = new URLSearchParams(location.search);
  const authType = queryParams.get('auth'); // 'login' | 'register' | null
  
  const isOpen = authType === 'login' || authType === 'register';
  const isLogin = authType !== 'register'; // Default to login if not explicitly 'register'

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });

  // Clear errors when toggling modes
  useEffect(() => {
    setError(null);
  }, [authType]);

  const handleClose = () => {
    // Strip the ?auth= param to close the modal while staying on the current page
    navigate(location.pathname);
  };

  const handleToggleMode = () => {
    const newMode = isLogin ? 'register' : 'login';
    navigate(`${location.pathname}?auth=${newMode}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isLogin) {
        const res = await apiClient.login(formData.email, formData.password);
        onSuccess({ name: formData.email.split('@')[0], email: formData.email }, res.access_token);
      } else {
        const res = await apiClient.register(formData.name, formData.email, formData.password);
        onSuccess(res.user!, res.access_token);
      }
      handleClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0"
            onClick={handleClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative w-full max-w-sm p-8 bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-2xl border border-black/5 dark:border-white/10 rounded-[2rem] shadow-2xl"
          >
            <button 
              onClick={handleClose}
              className="absolute top-4 right-4 p-1.5 text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200 transition-colors rounded-full hover:bg-black/5 dark:hover:bg-white/10"
            >
              <X className="w-4 h-4" />
            </button>

            <h2 className="text-xl font-medium tracking-tight text-neutral-900 dark:text-white mb-6">
              {isLogin ? 'Sign In' : 'Create Account'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <AnimatePresence mode="popLayout">
                {!isLogin && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <input
                      type="text"
                      placeholder="Name"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-2.5 text-sm bg-black/5 dark:bg-white/5 border border-transparent rounded-xl focus:bg-transparent focus:border-blue-500/30 focus:ring-4 focus:ring-blue-500/10 text-neutral-900 dark:text-white placeholder:text-neutral-500 outline-none transition-all"
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              <input
                type="email"
                placeholder="Email address"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2.5 text-sm bg-black/5 dark:bg-white/5 border border-transparent rounded-xl focus:bg-transparent focus:border-blue-500/30 focus:ring-4 focus:ring-blue-500/10 text-neutral-900 dark:text-white placeholder:text-neutral-500 outline-none transition-all"
              />
              
              <input
                type="password"
                placeholder="Password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-2.5 text-sm bg-black/5 dark:bg-white/5 border border-transparent rounded-xl focus:bg-transparent focus:border-blue-500/30 focus:ring-4 focus:ring-blue-500/10 text-neutral-900 dark:text-white placeholder:text-neutral-500 outline-none transition-all"
              />

              {error && <p className="text-xs text-red-500 font-medium">{error}</p>}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 mt-2 text-sm font-medium text-white bg-neutral-900 dark:bg-white dark:text-neutral-900 rounded-xl hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors disabled:opacity-50 flex justify-center items-center h-10"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (isLogin ? 'Sign In' : 'Continue')}
              </button>
            </form>

            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={handleToggleMode}
                className="text-xs text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-300 transition-colors"
              >
                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};