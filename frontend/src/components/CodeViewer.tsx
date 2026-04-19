import React, { useEffect, useRef } from 'react';
import type { Chunk } from '../types';

interface CodeViewerProps {
  chunks: Chunk[];
  activeChunkId: number | null;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({ chunks, activeChunkId }) => {
  const chunkRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (activeChunkId !== null) {
        const index = chunks.findIndex(c => c.id === activeChunkId);
        if (index !== -1) {
            chunkRefs.current[index]?.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
            });
        }
    }
  }, [activeChunkId]);

  if (chunks.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-neutral-500 font-mono text-sm">
        Waiting for context...
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 scrollbar-hide">
      {chunks.map((chunk, index) => {
        // Find if this chunk ID matches the active one
        const isActive = activeChunkId === chunk.id;

        return (
          <div 
            key={chunk.id} 
            ref={(el) => {
                chunkRefs.current[index] = el;
            }}
            className={`
              rounded-xl border transition-all duration-500 ease-in-out overflow-hidden bg-[#121214]
              ${isActive 
                ? 'border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.15)] ring-1 ring-blue-500/20 opacity-100' 
                : 'border-white/10 opacity-50 hover:opacity-80'}
            `}
          >
            {/* File Header */}
            <div className="bg-white/5 px-4 py-2.5 border-b border-white/5 flex justify-between items-center text-xs text-white/60 font-mono">
              <span className="text-white/90">{chunk.file_path}</span>
              <span className="bg-white/10 px-2 py-0.5 rounded-md">Lines {chunk.start_line}-{chunk.end_line}</span>
            </div>
            
            {/* The Code */}
            <div className={`p-4 font-mono text-[13px] leading-relaxed overflow-x-auto ${isActive ? 'bg-blue-500/[0.02]' : 'bg-transparent'}`}>
               <pre>
                 <code className="text-neutral-300">{chunk.code}</code>
               </pre>
            </div>
          </div>
        );
      })}
    </div>
  );
};