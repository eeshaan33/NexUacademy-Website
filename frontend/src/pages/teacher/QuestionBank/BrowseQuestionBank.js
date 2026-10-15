import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FolderTree, Plus, Loader2, Library, Youtube, Film, X,
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../../../utils/api';
import { Button } from '../../../components/ui/button';
import { Card, CardContent } from '../../../components/ui/card';
import { setPageTitle } from '../../../utils/pageTitle';
import { QBFolderTree } from '../../../components/QBFolderTree';

const NAVY = '#1B3A52';

function QuestionModal({ question, onClose }) {
  if (!question) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()} data-testid="qbank-question-modal">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white">
          <div className="flex items-center gap-2">
            <span className="text-xs bg-[#1B3A52]/10 text-[#1B3A52] font-semibold rounded-full px-2 py-0.5">
              {question.question_type.replace(/_/g, ' ')}
            </span>
            {question.difficulty && (
              <span className="text-xs bg-amber-100 text-amber-700 rounded-full px-2 py-0.5">{question.difficulty}</span>
            )}
            <span className="text-xs text-slate-500">+{question.marks} / {question.negative_marks}</span>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded"><X className="h-4 w-4" /></button>
        </div>
        <div className="p-5 space-y-4">
          {question.question_text && <div className="text-slate-800 whitespace-pre-wrap">{question.question_text}</div>}
          {question.question_image_url && (
            <img src={question.question_image_url} alt="question" className="max-h-64 rounded border" />
          )}
          {question.question_type.startsWith('MCQ') && (
            <div className="space-y-2">
              {['A', 'B', 'C', 'D'].map((k) => {
                const opt = (question.options || {})[k] || {};
                const correct = (question.correct_answers || []).includes(k);
                return (
                  <div key={k} className={`p-3 rounded-lg border-2 ${correct ? 'border-emerald-500 bg-emerald-50/40' : 'border-slate-200'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold" style={{ color: NAVY }}>{k}.</span>
                      {correct && <span className="text-[10px] uppercase font-semibold text-emerald-600">Correct</span>}
                    </div>
                    {opt.text && <div className="text-sm text-slate-700">{opt.text}</div>}
                    {opt.imageUrl && <img src={opt.imageUrl} alt={k} className="mt-2 max-h-32 rounded border" />}
                  </div>
                );
              })}
            </div>
          )}
          {question.question_type.startsWith('Numerical') && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
              <div className="text-xs text-emerald-700 uppercase font-semibold">Correct answer</div>
              <div className="text-lg font-bold text-emerald-800">{question.numerical_answer}</div>
            </div>
          )}
          {question.teacher_note && (
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <div className="text-xs uppercase font-semibold text-slate-500 mb-1">Solution / Hint</div>
              <div className="text-sm text-slate-700 whitespace-pre-wrap">{question.teacher_note}</div>
            </div>
          )}
          {question.solution_youtube_url && (
            <a href={question.solution_youtube_url} target="_blank" rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 hover:bg-red-700 text-white px-4 py-2 text-sm font-medium transition-colors"
              data-testid="qbank-solution-youtube-btn">
              <Youtube className="h-4 w-4" /> Watch on YouTube
            </a>
          )}
          {question.solution_media_url && (
            <div className="rounded-lg border border-slate-200 overflow-hidden bg-slate-50">
              <div className="text-xs uppercase font-semibold text-slate-500 px-3 py-2 flex items-center gap-1.5 border-b border-slate-200 bg-white">
                <Film className="h-3.5 w-3.5" /> Solution {question.solution_media_type}
              </div>
              {question.solution_media_type === 'video'
                ? <video src={question.solution_media_url} controls className="w-full max-h-72 bg-black" />
                : <img src={question.solution_media_url} alt="solution" className="w-full max-h-72 object-contain" />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QuestionCard({ q, onOpen }) {
  const preview = (q.question_text || '(image only)').slice(0, 110);
  return (
    <button type="button" onClick={() => onOpen(q)}
      className="w-full text-left flex items-center gap-3 p-3 rounded-lg border border-slate-200 bg-white hover:border-[#1B3A52]/40 hover:shadow-sm transition-all"
      data-testid={`qbank-q-${q.id}`}
    >
      {q.question_image_url
        ? <img src={q.question_image_url} alt="q" className="w-12 h-12 rounded object-cover border border-slate-200" />
        : <div className="w-12 h-12 rounded bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-300 text-xs">Q</div>}
      <div className="flex-1 min-w-0">
        <div className="text-sm text-slate-700 truncate">{preview}{q.question_text?.length > 110 ? '…' : ''}</div>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="text-[10px] bg-[#1B3A52]/10 text-[#1B3A52] rounded px-1.5 py-0.5 font-semibold">
            {q.question_type.replace(/_/g, ' ')}
          </span>
          {q.difficulty && <span className="text-[10px] bg-amber-100 text-amber-700 rounded px-1.5 py-0.5">{q.difficulty}</span>}
          <span className="text-[10px] text-slate-400">+{q.marks} / {q.negative_marks}</span>
        </div>
      </div>
    </button>
  );
}

function FolderNode(/* moved into components/QBFolderTree — babel plugin
   choked on recursive JSX in this file. */) {}

export default function BrowseQuestionBank() {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [qLoading, setQLoading] = useState(false);
  const [openQ, setOpenQ] = useState(null);

  useEffect(() => { setPageTitle('Question Bank'); loadFolders(); }, []);

  const loadFolders = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/teacher/qb/folders');
      setFolders(data.folders || []);
      // Expand roots by default so the user sees the hierarchy
      setExpandedIds(new Set((data.folders || []).map((r) => r.id)));
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load folders');
    } finally { setLoading(false); }
  };

  const toggleExpanded = (id) => setExpandedIds((p) => {
    const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n;
  });

  const onSelectFolder = async (folder) => {
    setSelectedFolder(folder);
    setQLoading(true);
    try {
      const { data } = await api.get('/teacher/question-bank', { params: { folder_id: folder.id } });
      setQuestions(data.questions || []);
    } catch (e) {
      toast.error('Failed to load questions');
    } finally { setQLoading(false); }
  };

  const totalQuestions = useMemo(() => {
    let n = 0;
    const walk = (node) => {
      if (node.is_leaf) n += node.question_count || 0;
      (node.children || []).forEach(walk);
    };
    folders.forEach(walk);
    return n;
  }, [folders]);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6" data-testid="qbank-browse-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg" style={{ backgroundColor: `${NAVY}12` }}>
            <Library className="h-5 w-5" style={{ color: NAVY }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: NAVY }}>Question Bank</h1>
            <p className="text-sm text-slate-500">
              {totalQuestions} question{totalQuestions === 1 ? '' : 's'} across the fixed PYQ / Non-PYQ hierarchy
            </p>
          </div>
        </div>
        <Button asChild className="bg-[#1B3A52] hover:bg-[#2B4A62] text-white" data-testid="qbank-add-new">
          <Link to="/teacher/question-bank/new"><Plus className="h-4 w-4 mr-1.5" /> Add New Question</Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        <Card className="border-slate-200 shadow-sm h-fit lg:sticky lg:top-4">
          <CardContent className="p-3">
            <div className="text-xs uppercase font-semibold text-slate-500 mb-2 px-2">Folders</div>
            {loading
              ? <div className="flex items-center text-slate-400 p-3 text-sm"><Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading…</div>
              : (
                <div className="max-h-[70vh] overflow-y-auto">
                  <QBFolderTree
                    roots={folders}
                    expanded={expandedIds}
                    toggleExpanded={toggleExpanded}
                    selectedId={selectedFolder?.id}
                    onSelect={onSelectFolder}
                  />
                </div>
              )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {!selectedFolder ? (
            <Card className="border-dashed border-2 border-slate-200">
              <CardContent className="py-16 flex flex-col items-center text-center gap-3">
                <FolderTree className="h-10 w-10 text-slate-300" />
                <h3 className="text-lg font-semibold text-slate-700">Pick a folder</h3>
                <p className="text-sm text-slate-500 max-w-sm">
                  Expand a category on the left and click a leaf folder (Physics / Chemistry / Maths …) to see its questions.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <div className="text-xs text-slate-400">{selectedFolder.path.split('/').slice(0, -1).join(' › ') || 'Root'}</div>
                  <h2 className="text-xl font-bold text-slate-800">{selectedFolder.name}</h2>
                </div>
                <span className="text-xs bg-slate-100 text-slate-600 rounded-full px-3 py-1">
                  {questions.length} question{questions.length === 1 ? '' : 's'}
                </span>
              </div>
              {qLoading ? (
                <div className="flex items-center text-slate-400 p-6 text-sm"><Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading…</div>
              ) : questions.length === 0 ? (
                <Card className="border-dashed border-2 border-slate-200">
                  <CardContent className="py-12 flex flex-col items-center text-center gap-3">
                    <h3 className="text-base font-semibold text-slate-700">No questions yet in this folder</h3>
                    <Button asChild className="bg-[#1B3A52] hover:bg-[#2B4A62] text-white">
                      <Link to="/teacher/question-bank/new">
                        <Plus className="h-4 w-4 mr-1.5" /> Add first question
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 gap-2">
                  {questions.map((q) => <QuestionCard key={q.id} q={q} onOpen={setOpenQ} />)}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <QuestionModal question={openQ} onClose={() => setOpenQ(null)} />
    </div>
  );
}
