import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ToastProps {
  message: string | null;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ message, onClose }) => {
  useEffect(() => {
    if (message) {
      const timer = setTimeout(onClose, 4000);
      return () => clearTimeout(timer);
    }
  }, [message, onClose]);

  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95, filter: 'blur(4px)' }}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
          className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] pointer-events-none"
        >
          <div className="px-5 py-2.5 bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-xl border border-black/5 dark:border-white/10 shadow-[0_8px_30px_rgb(0,0,0,0.12)] rounded-full text-sm font-medium text-neutral-800 dark:text-neutral-200">
            {message}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};