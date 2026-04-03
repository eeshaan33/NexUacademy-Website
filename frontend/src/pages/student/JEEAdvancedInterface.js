import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Clock, AlertTriangle } from 'lucide-react';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

const BACKEND = process.env.REACT_APP_BACKEND_URL;

function renderMath(text) {
  if (!text) return text;
  const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[^$]+?\$)/g);
  return parts.map((part, i) => {
    if (part.startsWith('$$') && part.endsWith('$$')) {
      try { return <BlockMath key={i} math={part.slice(2, -2)} />; } catch { return part; }
    } else if (part.startsWith('$') && part.endsWith('$')) {
      try { return <InlineMath key={i} math={part.slice(1, -1)} />; } catch { return part; }
    }
    return <span key={i}>{part}</span>;
  });
}

export default function JEEAdvancedInterface() {
  const { attemptId } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [marked, setMarked] = useState(new Set());
  const [visited, setVisited] = useState(new Set([0]));
  const [timeLeft, setTimeLeft] = useState(0);
  const [currentSection, setCurrentSection] = useState('');
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const timerRef = useRef(null);
  const autoSaveRef = useRef(null);
  const startTime = useRef(Date.now());

  useEffect(() => { setPageTitle('JEE Advanced Test'); loadTest(); }, []);

  const loadTest = () => {
    try {
      const loc = window.history.state?.usr;
      if (loc?.test && loc?.attempt) {
        setTest(loc.test); setAttempt(loc.attempt);
        setTimeLeft(loc.test.duration * 60);
        const subjects = [...new Set((loc.test.questions || []).map(q => q.subject).filter(Boolean))];
        if (subjects.length) setCurrentSection(subjects[0]);
        if (loc.attempt.saved_answers?.length) {
          const ans = {};
          loc.attempt.saved_answers.forEach(a => { ans[a.question_number] = a.selected_answer; });
          setAnswers(ans);
        }
      }
    } catch {}
  };

  useEffect(() => {
    if (!test) return;
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => { if (prev <= 1) { handleSubmit(true); return 0; } return prev - 1; });
    }, 1000);
    autoSaveRef.current = setInterval(() => autoSave(), 30000);
    return () => { clearInterval(timerRef.current); clearInterval(autoSaveRef.current); };
  }, [test]);

  const autoSave = useCallback(async () => {
    if (!attempt) return;
    try {
      const ansArr = Object.entries(answers).map(([qn, a]) => ({ question_number: parseInt(qn), selected_answer: a }));
      await api.put(`/student/tests/attempts/${attempt.attempt_id}/autosave`, { answers: ansArr });
    } catch {}
  }, [attempt, answers]);

  const handleSubmit = async (auto = false) => {
    clearInterval(timerRef.current); clearInterval(autoSaveRef.current);
    try {
      const qs = test.questions || [];
      const ansArr = qs.map(q => ({
        question_number: q.question_number, selected_answer: answers[q.question_number] ?? null,
        time_taken: 0, flagged: marked.has(q.question_number - 1),
      }));
      const { data } = await api.post(`/student/tests/attempts/${attempt.attempt_id}/submit`, {
        answers: ansArr, time_spent: Math.floor((Date.now() - startTime.current) / 1000), autoSubmitted: auto,
      });
      if (auto) alert('Time up! Auto-submitted.');
      navigate(`/test-results/${data.attempt.attempt_id}`, { replace: true });
    } catch { alert('Submit failed.'); }
  };

  const formatTime = (s) => `${String(Math.floor(s / 3600)).padStart(2, '0')}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  const goToQ = (idx) => { setCurrentQ(idx); setVisited(v => new Set(v).add(idx)); };

  const getStatus = (idx) => {
    const qn = test?.questions?.[idx]?.question_number;
    const hasAns = answers[qn] !== undefined && answers[qn] !== null && answers[qn] !== '';
    const isMarked = marked.has(idx);
    if (hasAns && isMarked) return 'answered-marked';
    if (hasAns) return 'answered';
    if (isMarked) return 'marked';
    if (visited.has(idx)) return 'not-answered';
    return 'not-visited';
  };

  const statusColors = {
    'not-visited': 'bg-slate-200 text-slate-700',
    'not-answered': 'bg-red-500 text-white',
    'answered': 'bg-emerald-500 text-white',
    'marked': 'bg-amber-500 text-white',
    'answered-marked': 'bg-violet-600 text-white',
  };

  if (!test || !attempt) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="text-center"><div className="animate-spin h-12 w-12 border-b-2 border-blue-400 rounded-full mx-auto" /><p className="mt-4 text-slate-400">Loading test...</p></div>
    </div>
  );

  const questions = test.questions || [];
  const q = questions[currentQ];
  const sections = [...new Set(questions.map(q => q.subject).filter(Boolean))];
  const sectionQs = questions.filter(qu => qu.subject === currentSection);
  const sectionQIndices = questions.reduce((acc, qu, i) => { if (qu.subject === currentSection) acc.push(i); return acc; }, []);

  const stats = { answered: 0, notAnswered: 0, marked: 0, notVisited: 0 };
  questions.forEach((_, i) => {
    const s = getStatus(i);
    if (s === 'answered' || s === 'answered-marked') stats.answered++;
    else if (s === 'not-answered') stats.notAnswered++;
    else if (s === 'marked') stats.marked++;
    else stats.notVisited++;
  });

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col" data-testid="jee-advanced-interface">
      {/* HEADER - Blue theme */}
      <div className="bg-gradient-to-r from-blue-800 to-indigo-900 text-white shadow-lg flex-shrink-0">
        <div className="px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/nexuacademy-logo.png" alt="NU" className="h-10 brightness-0 invert" />
            <div>
              <div className="text-lg font-bold tracking-wide">{test.test_name}</div>
              <div className="text-xs opacity-70">JEE Advanced Pattern | {test.subject}</div>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right"><div className="text-xs opacity-70">Candidate</div><div className="font-semibold text-sm">{attempt.student_name}</div></div>
            <div className={`text-xl font-mono font-bold px-4 py-1.5 rounded-lg ${timeLeft < 300 ? 'bg-red-600 animate-pulse' : 'bg-blue-600'}`}>
              <Clock className="inline h-4 w-4 mr-1 -mt-0.5" />{formatTime(timeLeft)}
            </div>
          </div>
        </div>
        {/* Section Tabs */}
        <div className="flex gap-0.5 px-4 pb-0">
          {sections.map((s, i) => (
            <button key={s} onClick={() => { setCurrentSection(s); const idx = questions.findIndex(q => q.subject === s); if (idx >= 0) goToQ(idx); }}
              className={`px-5 py-2 text-sm font-semibold rounded-t-lg transition-all ${currentSection === s ? 'bg-white text-blue-800' : 'bg-blue-700/40 hover:bg-blue-700/60 text-white/80'}`}>
              {s} {i === 0 ? '- Sec A' : i === 1 ? '- Sec B' : `- Sec ${String.fromCharCode(65 + i)}`}
            </button>
          ))}
        </div>
      </div>

      {/* MAIN */}
      <div className="flex flex-1 overflow-hidden">
        {/* Question Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-white">
          {q && (<>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-lg font-bold text-blue-900">Question {q.question_number}</span>
              <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full font-medium">+{q.marks} / {q.negative_marks}</span>
              <span className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full font-medium">{q.question_type?.replace(/_/g, ' ')}</span>
              {q.question_type === 'MCQ_Multiple' && <span className="text-xs px-2 py-0.5 bg-amber-50 text-amber-700 rounded-full">One or More Correct</span>}
            </div>
            <div className="text-base leading-relaxed mb-6">{renderMath(q.question_text)}</div>
            {q.question_image_url && <img src={q.question_image_url.startsWith('/') ? `${BACKEND}${q.question_image_url}` : q.question_image_url} alt="Question" className="max-w-full border rounded-lg mb-6" />}

            {q.question_type?.startsWith('MCQ') && (
              <div className="space-y-3">
                {['A', 'B', 'C', 'D'].map(opt => {
                  const optData = q.options?.[opt];
                  if (!optData?.text && !optData?.imageUrl) return null;
                  const isSelected = q.question_type === 'MCQ_Single' ? answers[q.question_number] === opt : (answers[q.question_number] || []).includes?.(opt);
                  return (
                    <label key={opt} className={`flex items-start gap-3 p-4 border-2 rounded-xl cursor-pointer transition-all ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}`}>
                      <input type={q.question_type === 'MCQ_Single' ? 'radio' : 'checkbox'} checked={!!isSelected}
                        onChange={() => {
                          const qn = q.question_number;
                          if (q.question_type === 'MCQ_Single') { setAnswers({ ...answers, [qn]: opt }); }
                          else { const cur = answers[qn] || []; setAnswers({ ...answers, [qn]: cur.includes(opt) ? cur.filter(a => a !== opt) : [...cur, opt] }); }
                        }} className="mt-1 w-5 h-5 accent-blue-600" />
                      <div className="flex-1">
                        <span className="font-semibold mr-2 text-blue-900">({opt})</span>
                        {optData?.text && <span>{renderMath(optData.text)}</span>}
                        {optData?.imageUrl && <img src={optData.imageUrl.startsWith('/') ? `${BACKEND}${optData.imageUrl}` : optData.imageUrl} alt={opt} className="mt-2 max-w-xs border rounded" />}
                      </div>
                    </label>
                  );
                })}
              </div>
            )}

            {q.question_type?.startsWith('Numerical') && (
              <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
                <label className="block text-sm font-medium mb-2 text-blue-900">Enter answer ({q.question_type === 'Numerical_Integer' ? 'Integer' : 'Decimal up to 2 places'}):</label>
                <input type="number" step={q.question_type === 'Numerical_Decimal' ? '0.01' : '1'}
                  value={answers[q.question_number] ?? ''} onChange={e => setAnswers({ ...answers, [q.question_number]: e.target.value })}
                  className="w-full max-w-md px-4 py-3 text-lg border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Type answer" />
              </div>
            )}

            {/* Actions */}
            <div className="mt-8 flex flex-wrap gap-3">
              <button onClick={() => goToQ(Math.min(questions.length - 1, currentQ + 1))} className="px-5 py-2.5 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700">SAVE & NEXT</button>
              <button onClick={() => { setMarked(m => { const n = new Set(m); n.add(currentQ); return n; }); goToQ(Math.min(questions.length - 1, currentQ + 1)); }}
                className="px-5 py-2.5 bg-amber-500 text-white rounded-lg font-semibold hover:bg-amber-600">MARK FOR REVIEW & NEXT</button>
              <button onClick={() => { const a = { ...answers }; delete a[q.question_number]; setAnswers(a); }}
                className="px-5 py-2.5 bg-slate-500 text-white rounded-lg font-semibold hover:bg-slate-600">CLEAR</button>
            </div>
            <div className="mt-6 flex justify-between border-t pt-4">
              <button disabled={currentQ === 0} onClick={() => goToQ(currentQ - 1)} className="px-4 py-2 border rounded-lg hover:bg-slate-50 disabled:opacity-40"><ChevronLeft className="inline h-4 w-4" /> BACK</button>
              <button disabled={currentQ === questions.length - 1} onClick={() => goToQ(currentQ + 1)} className="px-4 py-2 border rounded-lg hover:bg-slate-50 disabled:opacity-40">NEXT <ChevronRight className="inline h-4 w-4" /></button>
            </div>
            <div className="mt-6 text-center">
              <button onClick={() => setShowSubmitModal(true)} className="px-10 py-3 bg-blue-700 text-white text-lg rounded-xl font-bold hover:bg-blue-800 shadow-lg" data-testid="submit-test-btn">SUBMIT TEST</button>
            </div>
          </>)}
        </div>

        {/* Right Panel */}
        <div className="w-72 bg-slate-50 border-l p-4 overflow-y-auto flex-shrink-0">
          <h3 className="font-bold text-sm text-blue-900 mb-3">Question Navigator</h3>
          <div className="grid grid-cols-2 gap-1 mb-4 text-[10px]">
            <div className="flex items-center gap-1"><div className="w-5 h-5 bg-slate-200 rounded text-center leading-5 font-bold">{stats.notVisited}</div>Not Visited</div>
            <div className="flex items-center gap-1"><div className="w-5 h-5 bg-red-500 text-white rounded text-center leading-5 font-bold">{stats.notAnswered}</div>Not Answered</div>
            <div className="flex items-center gap-1"><div className="w-5 h-5 bg-emerald-500 text-white rounded text-center leading-5 font-bold">{stats.answered}</div>Answered</div>
            <div className="flex items-center gap-1"><div className="w-5 h-5 bg-amber-500 text-white rounded text-center leading-5 font-bold">{stats.marked}</div>Review</div>
          </div>

          {sections.map(sec => (
            <div key={sec} className="mb-4">
              <h4 className="text-xs font-bold text-blue-800 mb-2 uppercase tracking-wider">{sec}</h4>
              <div className="grid grid-cols-5 gap-1">
                {questions.map((qu, i) => qu.subject !== sec ? null : (
                  <button key={i} onClick={() => { setCurrentSection(sec); goToQ(i); }}
                    className={`aspect-square rounded text-xs font-bold transition-all ${statusColors[getStatus(i)]} ${currentQ === i ? 'ring-2 ring-blue-400 ring-offset-1' : ''}`}>
                    {i + 1}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Submit Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="flex items-center gap-3 mb-4"><AlertTriangle className="h-8 w-8 text-amber-500" /><h3 className="text-xl font-bold text-blue-900">Submit Test?</h3></div>
            <div className="space-y-2 mb-6 text-sm">
              <div className="flex justify-between p-2 bg-emerald-50 rounded"><span>Answered</span><strong>{stats.answered}</strong></div>
              <div className="flex justify-between p-2 bg-red-50 rounded"><span>Not Answered</span><strong>{stats.notAnswered}</strong></div>
              <div className="flex justify-between p-2 bg-amber-50 rounded"><span>Marked for Review</span><strong>{stats.marked}</strong></div>
              <div className="flex justify-between p-2 bg-slate-50 rounded"><span>Not Visited</span><strong>{stats.notVisited}</strong></div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setShowSubmitModal(false)} className="flex-1 px-4 py-2.5 border rounded-lg font-semibold hover:bg-slate-50">Go Back</button>
              <button onClick={() => handleSubmit(false)} className="flex-1 px-4 py-2.5 bg-blue-700 text-white rounded-lg font-semibold hover:bg-blue-800" data-testid="confirm-submit">Confirm Submit</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
