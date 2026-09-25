import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, ChevronDown, FolderTree, Folder, Plus, Search, X, Loader2, Library, Youtube, Film } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../../utils/api';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Card, CardContent } from '../../../components/ui/card';
import { setPageTitle } from '../../../utils/pageTitle';

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
              <span className="text-xs bg-amber-100 text-amber-700 rounded-full px-2 py-0.5">
                {question.difficulty}
              </span>
            )}
            <span className="text-xs text-slate-500">+{question.marks} / {question.negative_marks}</span>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded"><X className="h-4 w-4" /></button>
        </div>
        <div className="p-5 space-y-4">
          {question.question_text && (
            <div className="text-slate-800 whitespace-pre-wrap">{question.question_text}</div>
          )}
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
              {question.answer_range && (
                <div className="text-xs text-emerald-700 mt-1">
                  Accepted range: {question.answer_range.min} … {question.answer_range.max}
                </div>
              )}
            </div>
          )}
          {question.teacher_note && (
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <div className="text-xs uppercase font-semibold text-slate-500 mb-1">Solution / Hint</div>
              <div className="text-sm text-slate-700 whitespace-pre-wrap">{question.teacher_note}</div>
            </div>
          )}
          {question.solution_youtube_url && (
            <a
              href={question.solution_youtube_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 hover:bg-red-700 text-white px-4 py-2 text-sm font-medium transition-colors"
              data-testid="qbank-solution-youtube-btn"
            >
              <Youtube className="h-4 w-4" /> Go to YouTube
            </a>
          )}
          {question.solution_media_url && (
            <div className="rounded-lg border border-slate-200 overflow-hidden bg-slate-50" data-testid="qbank-solution-media">
              <div className="text-xs uppercase font-semibold text-slate-500 px-3 py-2 flex items-center gap-1.5 border-b border-slate-200 bg-white">
                <Film className="h-3.5 w-3.5" /> Solution {question.solution_media_type}
              </div>
              {question.solution_media_type === 'video' ? (
                <video src={question.solution_media_url} controls className="w-full max-h-72 bg-black" />
              ) : (
                <img src={question.solution_media_url} alt="solution" className="w-full max-h-72 object-contain" />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QuestionCard({ q, onOpen }) {
  const preview = (q.question_text || '(image only)').slice(0, 90);
  return (
    <button
      type="button"
      onClick={() => onOpen(q)}
      className="w-full text-left flex items-center gap-3 p-3 rounded-lg border border-slate-200 bg-white hover:border-[#1B3A52]/40 hover:shadow-sm transition-all"
      data-testid={`qbank-q-${q.id}`}
    >
      {q.question_image_url ? (
        <img src={q.question_image_url} alt="q" className="w-12 h-12 rounded object-cover border border-slate-200" />
      ) : (
        <div className="w-12 h-12 rounded bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-300 text-xs">Q</div>
      )}
      <div className="flex-1 min-w-0">
        <div className="text-sm text-slate-700 truncate">{preview}{q.question_text?.length > 90 ? '…' : ''}</div>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="text-[10px] bg-[#1B3A52]/10 text-[#1B3A52] rounded px-1.5 py-0.5 font-semibold">
            {q.question_type.replace(/_/g, ' ')}
          </span>
          {q.difficulty && (
            <span className="text-[10px] bg-amber-100 text-amber-700 rounded px-1.5 py-0.5">{q.difficulty}</span>
          )}
          <span className="text-[10px] text-slate-400">+{q.marks} / {q.negative_marks}</span>
        </div>
      </div>
    </button>
  );
}

export default function BrowseQuestionBank() {
  const [tree, setTree] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedTopics, setExpandedTopics] = useState(new Set());
  const [expandedSubs, setExpandedSubs] = useState(new Set());
  const [subQuestions, setSubQuestions] = useState({}); // sub_id → questions[]
  const [openQ, setOpenQ] = useState(null);

  useEffect(() => { setPageTitle('Question Bank'); load(); }, []);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/teacher/question-bank/tree');
      setTree(data.tree || []);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load question bank');
    } finally { setLoading(false); }
  };

  const toggleTopic = (id) => setExpandedTopics((p) => {
    const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n;
  });

  const toggleSub = async (sub) => {
    const key = sub.id;
    setExpandedSubs((p) => {
      const n = new Set(p); n.has(key) ? n.delete(key) : n.add(key); return n;
    });
    if (!subQuestions[key]) {
      try {
        const { data } = await api.get('/teacher/question-bank', { params: { subtopic_id: key } });
        setSubQuestions((prev) => ({ ...prev, [key]: data.questions || [] }));
      } catch (e) { toast.error('Failed to load questions'); }
    }
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return tree;
    return tree
      .map((t) => {
        const topicHit = t.name.toLowerCase().includes(q) || (t.subject || '').toLowerCase().includes(q);
        const subs = (t.subtopics || []).filter((s) => topicHit || s.name.toLowerCase().includes(q));
        if (!topicHit && subs.length === 0) return null;
        return { ...t, subtopics: topicHit ? t.subtopics : subs };
      })
      .filter(Boolean);
  }, [tree, search]);

  const totalQuestions = tree.reduce((s, t) => s + (t.question_count || 0), 0);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6" data-testid="qbank-browse-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg" style={{ backgroundColor: `${NAVY}12` }}>
            <Library className="h-5 w-5" style={{ color: NAVY }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: NAVY }}>Question Bank</h1>
            <p className="text-sm text-slate-500">
              {totalQuestions} questions across {tree.length} topic{tree.length === 1 ? '' : 's'}
            </p>
          </div>
        </div>
        <Button asChild className="bg-[#1B3A52] hover:bg-[#2B4A62] text-white" data-testid="qbank-add-new">
          <Link to="/teacher/question-bank/new"><Plus className="h-4 w-4 mr-1.5" /> Add New Question</Link>
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Search topics, subtopics, subjects…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
          data-testid="qbank-search"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading…
        </div>
      ) : filtered.length === 0 ? (
        <Card className="border-dashed border-2 border-slate-200">
          <CardContent className="py-16 flex flex-col items-center text-center gap-3">
            <FolderTree className="h-10 w-10 text-slate-300" />
            <h3 className="text-lg font-semibold text-slate-700">
              {tree.length === 0 ? 'No topics yet' : 'No matches'}
            </h3>
            <p className="text-sm text-slate-500 max-w-sm">
              {tree.length === 0
                ? 'Add your first question — topics and subtopics are created as you go.'
                : 'Try a different search.'}
            </p>
            {tree.length === 0 && (
              <Button asChild className="bg-[#1B3A52] hover:bg-[#2B4A62] text-white mt-2">
                <Link to="/teacher/question-bank/new"><Plus className="h-4 w-4 mr-1.5" />Add your first question</Link>
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {filtered.map((topic) => {
            const openT = expandedTopics.has(topic.id) || !!search.trim();
            return (
              <Card key={topic.id} className="border-slate-200 shadow-sm overflow-hidden">
                <button
                  type="button"
                  onClick={() => toggleTopic(topic.id)}
                  className="w-full flex items-center gap-3 p-4 hover:bg-slate-50 transition-colors text-left"
                  data-testid={`qbank-topic-${topic.id}`}
                >
                  {openT ? <ChevronDown className="h-4 w-4 text-slate-500" /> : <ChevronRight className="h-4 w-4 text-slate-500" />}
                  <FolderTree className="h-5 w-5" style={{ color: NAVY }} />
                  <div className="flex-1">
                    <div className="font-semibold text-slate-800">{topic.name}</div>
                    {topic.subject && <div className="text-xs text-slate-500">{topic.subject}</div>}
                  </div>
                  <span className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                    {topic.question_count || 0} question{topic.question_count === 1 ? '' : 's'}
                  </span>
                </button>
                {openT && (
                  <div className="border-t border-slate-100 bg-slate-50/40 p-3 space-y-2">
                    {(topic.subtopics || []).length === 0 && (
                      <div className="text-xs text-slate-400 italic pl-8">No subtopics yet</div>
                    )}
                    {(topic.subtopics || []).map((sub) => {
                      const openS = expandedSubs.has(sub.id);
                      return (
                        <div key={sub.id} className="rounded-lg bg-white border border-slate-200">
                          <button
                            type="button"
                            onClick={() => toggleSub(sub)}
                            className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 transition-colors text-left"
                            data-testid={`qbank-subtopic-${sub.id}`}
                          >
                            {openS ? <ChevronDown className="h-4 w-4 text-slate-500" /> : <ChevronRight className="h-4 w-4 text-slate-500" />}
                            <Folder className="h-4 w-4 text-slate-400" />
                            <div className="flex-1 text-sm text-slate-700">{sub.name}</div>
                            <span className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                              {sub.question_count || 0}
                            </span>
                          </button>
                          {openS && (
                            <div className="border-t border-slate-100 p-3 space-y-2">
                              {(subQuestions[sub.id] || []).length === 0 && (
                                <div className="text-xs text-slate-400 italic">No questions yet</div>
                              )}
                              {(subQuestions[sub.id] || []).map((q) => (
                                <QuestionCard key={q.id} q={q} onOpen={setOpenQ} />
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      <QuestionModal question={openQ} onClose={() => setOpenQ(null)} />
    </div>
  );
}
