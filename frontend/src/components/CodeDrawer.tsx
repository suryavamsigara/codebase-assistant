import React, { useEffect, useState, useRef } from 'react';
import { X, Loader2, FileCode2 } from 'lucide-react';
import { apiClient } from '../api';
import type { Chunk } from '../types';

interface CodeDrawerProps {
  repoName: string;
  chunk: Chunk;
  onClose: () => void;
}

export const CodeDrawer: React.FC<CodeDrawerProps> = ({ repoName, chunk, onClose }) => {
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setFileContent(null);

    apiClient.getFileContent(repoName, chunk.file_path)
      .then(content => {
        if (isMounted) {
          setFileContent(content);
          setIsLoading(false);
          
          // Slight delay to ensure the DOM has painted the lines before scrolling
          setTimeout(() => {
            scrollRef.current?.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'center' 
            });
          }, 150);
        }
      })
      .catch(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => { isMounted = false; };
  }, [repoName, chunk.file_path, chunk.start_line]);

  const lines = fileContent ? fileContent.split('\n') : [];

  return (
    <div className="flex flex-col h-full bg-[#FAFAFA] dark:bg-[#0A0A0A]">
      {/* Drawer Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between h-14 px-4 bg-white/70 dark:bg-neutral-950/70 backdrop-blur-xl border-b border-black/5 dark:border-white/5">
        <div className="flex items-center gap-2 overflow-hidden">
          <FileCode2 className="w-4 h-4 text-neutral-400 flex-shrink-0" />
          <span className="text-xs font-mono font-medium text-neutral-800 dark:text-neutral-200 truncate">
            {chunk.file_path}
          </span>
        </div>
        <button 
          onClick={onClose}
          className="p-1.5 text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors flex-shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      </header>

      {/* File Content */}
      <main className="flex-1 overflow-auto bg-white dark:bg-[#0E0E10] py-4 scrollbar-thin">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-neutral-400">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
        ) : (
          <div className="font-mono text-[13px] leading-[1.6]">
            {lines.map((line, index) => {
              const lineNum = index + 1;
              const isHighlighted = lineNum >= chunk.start_line && lineNum <= chunk.end_line;
              const isFirstHighlightLine = lineNum === chunk.start_line;

              return (
                <div 
                  key={lineNum}
                  ref={isFirstHighlightLine ? scrollRef : null}
                  className={`flex px-4 ${
                    isHighlighted 
                      ? 'bg-blue-500/10 dark:bg-blue-500/20 border-l-2 border-blue-500 text-blue-900 dark:text-blue-100' 
                      : 'border-l-2 border-transparent text-neutral-600 dark:text-neutral-400 hover:bg-black/5 dark:hover:bg-white/5'
                  }`}
                >
                  <span className="w-10 flex-shrink-0 text-right pr-4 text-neutral-400 dark:text-neutral-600 select-none">
                    {lineNum}
                  </span>
                  <span className="whitespace-pre">
                    {line || ' '}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};