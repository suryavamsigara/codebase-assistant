import React from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import type { Message, Chunk } from '../types';

interface MessageBubbleProps {
  message: Message;
  onCiteClick: (chunk: Chunk) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onCiteClick }) => {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[95%] md:max-w-[100%] rounded-2xl px-5 py-3.5 text-[0.95rem] leading-relaxed ${
          isUser
            ? 'bg-gray-800 text-white shadow-sm' 
            : 'bg-white dark:bg-[#1C1C1E] border border-neutral-200 dark:border-neutral-800 text-neutral-800 dark:text-neutral-200 shadow-sm'
        }`}
      >
        <ReactMarkdown
          components={{
            a: ({ node, href, children, ...props }) => {
              if (href && href.startsWith('#chunk-')) {
                const chunkIndex = parseInt(href.replace('#chunk-', ''), 10);
                // Look up the actual chunk from the message's chunks array
                const targetChunk = message.chunks?.find(c => c.id === chunkIndex);
                
                return (
                  <button 
                    onClick={() => targetChunk && onCiteClick(targetChunk)}
                    className="inline-flex items-center gap-1 px-1.5 py-0.5 mx-0.5 text-xs font-mono font-medium text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-md hover:bg-blue-100 dark:hover:bg-blue-500/30 transition-colors cursor-pointer"
                  >
                    {children}
                  </button>
                );
              }
              return <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline" {...props}>{children}</a>;
            }
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
    </motion.div>
  );
};