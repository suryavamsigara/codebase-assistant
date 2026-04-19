import { useState } from 'react';
import { AnimatePresence } from 'motion/react';
import { ZeroState } from './components/ZeroState';
import { Workspace } from './components/Workspace';

export default function App() {
  const [activeRepoName, setActiveRepoName] = useState<string | null>(null);

  return (
    <div className="min-h-screen font-sans selection:bg-neutral-200 dark:selection:bg-neutral-800 antialiased text-neutral-900 dark:text-neutral-100">
      <AnimatePresence mode="wait">
        {!activeRepoName ? (
          <ZeroState 
            key="zero" 
            onIndexComplete={(repoName) => setActiveRepoName(repoName)} 
          />
        ) : (
          <Workspace 
            key="workspace" 
            repoName={activeRepoName} 
            onReset={() => setActiveRepoName(null)} 
          />
        )}
      </AnimatePresence>
    </div>
  );
}