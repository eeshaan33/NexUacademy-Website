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

export default function JEEMainInterface() {
  const { attemptId } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [marked, setMarked] = useState(new Set());
  const [visited, setVisited] = useState(new Set([0]));
  const [timeLeft, setTimeLeft] = useState(0);
  const [subject, setSubject] = useState('');
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const autoSaveRef = useRef(null);
  const timerRef = useRef(null);
  const startTime = useRef(Date.now());

  useEffect(() => { setPageTitle('JEE Main Test'); loadTest(); }, []);

  const loadTest = async () => {
    try {
      const loc = window.history.state?.usr;
      if (loc?.test && loc?.attempt) {
        setTest(loc.test); setAttempt(loc.attempt);
        setTimeLeft(loc.test.duration * 60);
        if (loc.test.questions?.[0]?.subject) setSubject(loc.test.questions[0].subject);
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
      setTimeLeft(prev => {
        if (prev <= 1) { handleSubmit(true); return 0; }
        return prev - 1;
      });
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
    clearInterval(timerRef.current);
    clearInterval(autoSaveRef.current);
    try {
      const qs = test.questions || [];
      const ansArr = qs.map(q => ({
        question_number: q.question_number,
        selected_answer: answers[q.question_number] ?? null,
        time_taken: 0, flagged: marked.has(q.question_number - 1),
      }));
      const timeSpent = Math.floor((Date.now() - startTime.current) / 1000);
      const { data } = await api.post(`/student/tests/attempts/${attempt.attempt_id}/submit`, {
        answers: ansArr, time_spent: timeSpent, autoSubmitted: auto,
      });
      if (auto) alert('Time up! Test auto-submitted.');
      navigate(`/test-results/${data.attempt.attempt_id}`, { replace: true });
    } catch (e) { alert('Submit failed. Please try again.'); }
  };

  const formatTime = (s) => {
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  };

  const goToQ = (idx) => { setCurrentQ(idx); setVisited(v => new Set(v).add(idx)); };

  const getStatus = (idx) => {
    const qn = (test?.questions?.[idx]?.question_number);
    const hasAns = answers[qn] !== undefined && answers[qn] !== null && answers[qn] !== '';
    const isMarked = marked.has(idx);
    const isVisited = visited.has(idx);
    if (hasAns && isMarked) return 'answered-marked';
    if (hasAns) return 'answered';
    if (isMarked) return 'marked';
    if (isVisited) return 'not-answered';
    return 'not-visited';
  };

  const statusColors = {
    'not-visited': 'bg-gray-200 text-gray-800',
    'not-answered': 'bg-red-500 text-white',
    'answered': 'bg-green-500 text-white',
    'marked': 'bg-orange-500 text-white',
    'answered-marked': 'bg-purple-600 text-white',
  };

  if (!test || !attempt) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center"><div className="animate-spin h-12 w-12 border-b-2 border-orange-600 rounded-full mx-auto" /><p className="mt-4 text-gray-600">Loading test...</p></div>
    </div>
  );

  const questions = test.questions || [];
  const q = questions[currentQ];
  const subjects = [...new Set(questions.map(q => q.subject).filter(Boolean))];
  const subjectQs = subject ? questions.filter(qu => qu.subject === subject) : questions;

  const stats = { answered: 0, notAnswered: 0, marked: 0, notVisited: 0 };
  questions.forEach((_, i) => {
    const s = getStatus(i); if (s === 'answered' || s === 'answered-marked') stats.answered++;
    else if (s === 'not-answered') stats.notAnswered++;
    else if (s === 'marked') stats.marked++;
    else stats.notVisited++;
  });

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col" data-testid="jee-main-interface">
      {/* HEADER */}
      <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white shadow-lg flex-shrink-0">
        <div className="px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/nexuacademy-logo.png" alt="NU" className="h-10 brightness-0 invert" />
            <div>
              <div className="text-lg font-bold">{test.test_name}</div>
              <div className="text-xs opacity-80">{test.exam_type?.replace('_', ' ')} | {test.subject}</div>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-xs opacity-80">Candidate</div>
              <div className="font-semibold text-sm">{attempt.student_name}</div>
            </div>
            <div className={`text-2xl font-bold px-4 py-1 rounded-lg ${timeLeft < 300 ? 'bg-red-700 animate-pulse' : 'bg-blue-600'}`}>
              <Clock className="inline h-5 w-5 mr-1 -mt-0.5" />{formatTime(timeLeft)}
            </div>
          </div>
        </div>
        {/* Subject Tabs */}
        {subjects.length > 1 && (
          <div className="flex gap-1 px-4 pb-1">
            {subjects.map(s => (
              <button key={s} onClick={() => { setSubject(s); const idx = questions.findIndex(q => q.subject === s); if (idx >= 0) goToQ(idx); }}
                className={`px-5 py-1.5 font-semibold text-sm rounded-t-lg transition-all ${subject === s ? 'bg-white text-orange-600' : 'bg-orange-700/50 hover:bg-orange-700'}`}>
                {s.toUpperCase()}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* MAIN */}
      <div className="flex flex-1 overflow-hidden">
        {/* Question Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-white">
          {q && (<>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-lg font-bold" style={{ color: '#1B3A52' }}>Question {q.question_number}</span>
              <span className="text-xs px-2 py-0.5 bg-orange-50 text-orange-700 rounded">+{q.marks} / {q.negative_marks}</span>
              <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{q.question_type?.replace(/_/g, ' ')}</span>
            </div>
            <div className="text-base leading-relaxed mb-6">{renderMath(q.question_text)}</div>
            {q.question_image_url && <img src={q.question_image_url.startsWith('/') ? `${BACKEND}${q.question_image_url}` : q.question_image_url} alt="Question" className="max-w-full border rounded-lg mb-6" />}

            {/* MCQ */}
            {q.question_type?.startsWith('MCQ') && (
              <div className="space-y-3">
                {['A', 'B', 'C', 'D'].map(opt => {
                  const optData = q.options?.[opt];
                  if (!optData?.text && !optData?.imageUrl) return null;
                  const isSelected = q.question_type === 'MCQ_Single'
                    ? answers[q.question_number] === opt
                    : (answers[q.question_number] || []).includes?.(opt);
                  return (
                    <label key={opt} className={`flex items-start gap-3 p-4 border-2 rounded-xl cursor-pointer transition-all ${isSelected ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}>
                      <input type={q.question_type === 'MCQ_Single' ? 'radio' : 'checkbox'} checked={!!isSelected}
                        onChange={() => {
                          const qn = q.question_number;
                          if (q.question_type === 'MCQ_Single') { setAnswers({ ...answers, [qn]: opt }); }
                          else {
                            const cur = answers[qn] || [];
                            setAnswers({ ...answers, [qn]: cur.includes(opt) ? cur.filter(a => a !== opt) : [...cur, opt] });
                          }
                        }} className="mt-1 w-5 h-5" />
                      <div className="flex-1">
                        <span className="font-semibold mr-2">({opt})</span>
                        {optData?.text && <span>{renderMath(optData.text)}</span>}
                        {optData?.imageUrl && <img src={optData.imageUrl.startsWith('/') ? `${BACKEND}${optData.imageUrl}` : optData.imageUrl} alt={opt} className="mt-2 max-w-xs border rounded" />}
                      </div>
                    </label>
                  );
                })}
              </div>
            )}

            {/* Numerical */}
            {q.question_type?.startsWith('Numerical') && (
              <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-6">
                <label className="block text-sm font-medium mb-2">Enter answer ({q.question_type === 'Numerical_Integer' ? 'Integer' : 'Decimal'}):</label>
                <input type="number" step={q.question_type === 'Numerical_Decimal' ? '0.01' : '1'}
                  value={answers[q.question_number] ?? ''}
                  onChange={e => setAnswers({ ...answers, [q.question_number]: e.target.value })}
                  className="w-full max-w-md px-4 py-3 text-lg border-2 border-amber-400 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none"
                  placeholder="Type your answer" />
              </div>
            )}

            {/* Actions */}
            <div className="mt-8 flex flex-wrap gap-3">
              <button onClick={() => { goToQ(Math.min(questions.length - 1, currentQ + 1)); }}
                className="px-5 py-2.5 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition">SAVE & NEXT</button>
              <button onClick={() => { setMarked(m => { const n = new Set(m); n.add(currentQ); return n; }); goToQ(Math.min(questions.length - 1, currentQ + 1)); }}
                className="px-5 py-2.5 bg-orange-500 text-white rounded-lg font-semibold hover:bg-orange-600 transition">SAVE & MARK FOR REVIEW</button>
              <button onClick={() => { const qn = q.question_number; const a = { ...answers }; delete a[qn]; setAnswers(a); }}
                className="px-5 py-2.5 bg-gray-500 text-white rounded-lg font-semibold hover:bg-gray-600 transition">CLEAR RESPONSE</button>
              <button onClick={() => { setMarked(m => { const n = new Set(m); if (n.has(currentQ)) n.delete(currentQ); else n.add(currentQ); return n; }); goToQ(Math.min(questions.length - 1, currentQ + 1)); }}
                className="px-5 py-2.5 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition">MARK FOR REVIEW & NEXT</button>
            </div>

            {/* Nav */}
            <div className="mt-6 flex justify-between border-t pt-4">
              <button disabled={currentQ === 0} onClick={() => goToQ(currentQ - 1)} className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-40">
                <ChevronLeft className="inline h-4 w-4" /> BACK</button>
              <button disabled={currentQ === questions.length - 1} onClick={() => goToQ(currentQ + 1)} className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-40">
                NEXT <ChevronRight className="inline h-4 w-4" /></button>
            </div>

            <div className="mt-6 text-center">
              <button onClick={() => setShowSubmitModal(true)} className="px-10 py-3 bg-green-600 text-white text-lg rounded-xl font-bold hover:bg-green-700 shadow-lg transition" data-testid="submit-test-btn">
                SUBMIT TEST
              </button>
            </div>
          </>)}
        </div>

        {/* Question Palette */}
        <div className="w-72 bg-white border-l p-4 overflow-y-auto flex-shrink-0">
          <h3 className="font-bold text-sm mb-3">Question Palette</h3>
          <div className="grid grid-cols-2 gap-1.5 mb-4 text-[10px]">
            <div className="flex items-center gap-1"><div className="w-6 h-6 bg-gray-200 rounded text-center leading-6 font-bold text-[10px]">{stats.notVisited}</div>Not Visited</div>
            <div className="flex items-center gap-1"><div className="w-6 h-6 bg-red-500 text-white rounded text-center leading-6 font-bold text-[10px]">{stats.notAnswered}</div>Not Answered</div>
            <div className="flex items-center gap-1"><div className="w-6 h-6 bg-green-500 text-white rounded text-center leading-6 font-bold text-[10px]">{stats.answered}</div>Answered</div>
            <div className="flex items-center gap-1"><div className="w-6 h-6 bg-orange-500 text-white rounded text-center leading-6 font-bold text-[10px]">{stats.marked}</div>Marked Review</div>
          </div>
          <div className="grid grid-cols-5 gap-1.5">
            {questions.map((_, i) => (
              <button key={i} onClick={() => goToQ(i)}
                className={`aspect-square rounded text-xs font-bold transition-all ${statusColors[getStatus(i)]} ${currentQ === i ? 'ring-2 ring-blue-400 ring-offset-1' : ''}`}>
                {i + 1}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Submit Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="flex items-center gap-3 mb-4"><AlertTriangle className="h-8 w-8 text-orange-500" /><h3 className="text-xl font-bold">Submit Test?</h3></div>
            <div className="space-y-2 mb-6 text-sm">
              <div className="flex justify-between p-2 bg-green-50 rounded"><span>Answered</span><strong>{stats.answered}</strong></div>
              <div className="flex justify-between p-2 bg-red-50 rounded"><span>Not Answered</span><strong>{stats.notAnswered}</strong></div>
              <div className="flex justify-between p-2 bg-orange-50 rounded"><span>Marked for Review</span><strong>{stats.marked}</strong></div>
              <div className="flex justify-between p-2 bg-gray-50 rounded"><span>Not Visited</span><strong>{stats.notVisited}</strong></div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setShowSubmitModal(false)} className="flex-1 px-4 py-2.5 border rounded-lg font-semibold hover:bg-gray-50">Go Back</button>
              <button onClick={() => handleSubmit(false)} className="flex-1 px-4 py-2.5 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700" data-testid="confirm-submit">Confirm Submit</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
