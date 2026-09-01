import React from 'react';

/**
 * Minimal, dependency-free branded loader shown while a lazy route chunk
 * is being fetched. Kept below 1KB so it does not fatten the shell bundle.
 */
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-white" data-testid="page-loader">
    <div className="flex flex-col items-center gap-3">
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 rounded-full border-2 border-amber-200" />
        <div className="absolute inset-0 rounded-full border-2 border-amber-500 border-t-transparent animate-spin" />
      </div>
      <p className="text-xs uppercase tracking-widest text-slate-400">Loading</p>
    </div>
  </div>
);

export default PageLoader;
