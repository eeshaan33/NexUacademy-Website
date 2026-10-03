/**
 * Shared helpers for the Question Bank fixed-folder hierarchy.
 * Iterative flatten avoids recursive JSX which trips the craco visual-edits
 * babel plugin ("Maximum call stack size exceeded" during traversal).
 */
import React from 'react';
import {
  ChevronDown, ChevronRight, Folder, FolderOpen, FolderTree,
} from 'lucide-react';
import { Check } from 'lucide-react';

export function flattenTree(roots, expanded) {
  const out = [];
  const walk = (node, depth) => {
    out.push({ node, depth });
    if (!node.is_leaf && expanded.has(node.id) && node.children?.length) {
      for (const c of node.children) walk(c, depth + 1);
    }
  };
  (roots || []).forEach((r) => walk(r, 0));
  return out;
}

/* Single-select tree (used by AddQuestion + BrowseQuestionBank).
 * - `selectedId` highlights a leaf
 * - clicking a non-leaf toggles expansion
 * - clicking a leaf calls `onSelect(node)` */
export function QBFolderTree({ roots, selectedId, onSelect, expanded, toggleExpanded }) {
  const flat = flattenTree(roots, expanded);
  return (
    <div>
      {flat.map(({ node, depth }) => {
        const isOpen = expanded.has(node.id);
        if (node.is_leaf) {
          const sel = selectedId === node.id;
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => onSelect(node)}
              className={`w-full flex items-center gap-2 pr-3 py-1.5 text-sm rounded transition text-left ${
                sel ? 'bg-[#1B3A52] text-white' : 'text-slate-700 hover:bg-[#1B3A52]/5'
              }`}
              style={{ paddingLeft: (depth + 1) * 16 }}
              data-testid={`folder-${node.id}`}
            >
              <Folder className={`h-3.5 w-3.5 ${sel ? 'text-white' : 'text-amber-500'}`} />
              <span className="flex-1 truncate">{node.name}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${sel ? 'bg-white/20' : 'bg-slate-100 text-slate-500'}`}>
                {node.question_count || 0}
              </span>
            </button>
          );
        }
        return (
          <button
            key={node.id}
            type="button"
            onClick={() => toggleExpanded(node.id)}
            className="w-full flex items-center gap-2 py-1.5 pr-2 hover:bg-slate-100 rounded transition text-left"
            style={{ paddingLeft: depth * 16 + 8 }}
            data-testid={`folder-${node.id}`}
          >
            {isOpen
              ? <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
              : <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}
            {isOpen
              ? <FolderOpen className="h-4 w-4 text-amber-500" />
              : <FolderTree className="h-4 w-4 text-slate-400" />}
            <span className="font-medium text-slate-800 flex-1">{node.name}</span>
            <span className="text-[10px] text-slate-400">{node.question_count || 0}</span>
          </button>
        );
      })}
    </div>
  );
}

/* Multi-select tree (used by CreateTest bank picker).
 * - `selectedIds` holds an array of selected leaf ids
 * - toggling a leaf toggles its id in that array */
export function QBFolderMultiTree({ roots, selectedIds, toggleSel, expanded, toggleExpanded }) {
  const flat = flattenTree(roots, expanded);
  return (
    <div>
      {flat.map(({ node, depth }) => {
        const isOpen = expanded.has(node.id);
        if (node.is_leaf) {
          const sel = selectedIds.includes(node.id);
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => toggleSel(node.id)}
              className={`w-full flex items-center gap-2 py-1.5 pr-3 text-sm rounded transition text-left ${
                sel ? 'bg-emerald-500 text-white' : 'text-slate-700 hover:bg-emerald-50'
              }`}
              style={{ paddingLeft: (depth + 1) * 16 }}
              data-testid={`bank-folder-${node.id}`}
            >
              <div className={`h-4 w-4 rounded border flex items-center justify-center ${sel ? 'bg-white border-white' : 'border-slate-300'}`}>
                {sel && <Check className="h-3 w-3 text-emerald-600" />}
              </div>
              <Folder className={`h-3.5 w-3.5 ${sel ? 'text-white' : 'text-amber-500'}`} />
              <span className="flex-1 truncate">{node.name}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${sel ? 'bg-white/20' : 'bg-slate-100 text-slate-500'}`}>
                {node.question_count || 0}
              </span>
            </button>
          );
        }
        return (
          <button
            key={node.id}
            type="button"
            onClick={() => toggleExpanded(node.id)}
            className="w-full flex items-center gap-2 py-1.5 pr-2 hover:bg-slate-100 rounded transition text-left"
            style={{ paddingLeft: depth * 16 + 8 }}
          >
            {isOpen
              ? <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
              : <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}
            {isOpen
              ? <FolderOpen className="h-4 w-4 text-amber-500" />
              : <FolderTree className="h-4 w-4 text-slate-400" />}
            <span className="font-medium text-slate-800 flex-1">{node.name}</span>
            <span className="text-[10px] text-slate-400">{node.question_count || 0}</span>
          </button>
        );
      })}
    </div>
  );
}
