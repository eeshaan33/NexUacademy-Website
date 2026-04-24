import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Award, Lock, ChevronRight, ArrowLeft } from 'lucide-react';
import api from '../utils/api';

const BACKEND = process.env.REACT_APP_BACKEND_URL;

const FALLBACK = [
  {
    id: 1,
    number: 34,
    subject: 'Chemistry',
    chapter: 'Chemical Bonding and Molecular Structure',
    topic: 'Dry Ice Sublimation',
    difficulty: 'Medium',
    type: 'Multiple Correct',
    year: 2023,
    examType: 'JEE Advanced',
    imageUrl: null,
    questionText:
      'A 2 g piece of "dry ice" is dropped in a 5 L glass vessel containing air at 1 atm and 25°C and the vessel is sealed. After some time, dry ice disappeared. (Assume that the temperature is kept constant throughout.) Identify the correct statement(s).',
    options: [
      '(a) Partial pressure of oxygen increases with respect to its initial value in air.',
      '(b) Partial pressure of CO₂ increases with respect to its initial value in air.',
      '(c) Total pressure of the vessel increases with respect to its initial value in air.',
      '(d) Disappearance of dry ice is due to the evaporation process.',
    ],
  },
  {
    id: 2,
    number: 32,
    subject: 'Chemistry',
    chapter: 'Solutions',
    topic: "Vapour Pressure and Raoult's Law",
    difficulty: 'Hard',
    type: 'Single Correct',
    year: 2023,
    examType: 'JEE Advanced',
    imageUrl: null,
    questionText:
      'A closed vessel with rigid walls contains 1.0 mol of component M (vapour pressure p*M): 0.9 mol liquid and 0.1 mol vapor. 0.1 mol of component N (vapour pressure p*N) is added slowly to maintain equilibrium conditions. Assume M and N form an ideal solution. The total pressure at the end of the addition will:',
    options: [
      '(a) decrease if p*M < p*N',
      '(b) decrease irrespective of relation between p*M and p*N',
      '(c) increase if p*M < p*N',
      '(d) increase irrespective of relation between p*M and p*N',
    ],
  },
];

const diffColors = {
  Easy: 'bg-emerald-100 text-emerald-700',
  Medium: 'bg-amber-100 text-amber-700',
  Hard: 'bg-red-100 text-red-700',
};

const SampleQuestions = () => {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState(FALLBACK);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/questions/samples', { params: { limit: 2 } });
        const fetched = (data?.samples || []).map((q, i) => ({
          id: q.question_id || i,
          number: 100 + i + 1,
          subject: q.subject,
          chapter: q.chapter,
          topic: q.topic,
          difficulty: q.difficulty || 'Medium',
          type: q.questionType === 'Multiple' ? 'Multiple Correct' : 'Single Correct',
          year: q.year,
          examType: q.exam_type?.replace('_', ' '),
          imageUrl: q.question_image_url
            ? (q.question_image_url.startsWith('/') ? `${BACKEND}${q.question_image_url}` : q.question_image_url)
            : null,
          questionText: q.question_text || q.questionText,
          options: ['A', 'B', 'C', 'D'].map((k) => q.options?.[k] ? `(${k.toLowerCase()}) ${q.options[k]}` : null).filter(Boolean),
        }));
        if (fetched.length >= 2) setQuestions(fetched);
        else if (fetched.length === 1) setQuestions([fetched[0], FALLBACK[0]]);
      } catch { /* fall back to hardcoded */ }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50" data-testid="sample-questions-page">
      <div className="bg-gradient-to-r from-indigo-700 to-purple-700 text-white py-12 px-4">
        <div className="max-w-5xl mx-auto">
          <Link to="/" className="inline-flex items-center gap-1 text-white/80 hover:text-white text-sm mb-3">
            <ArrowLeft className="w-4 h-4" /> Back to home
          </Link>
          <div className="flex items-center gap-3 mb-2">
            <BookOpen className="w-9 h-9" />
            <h1 className="text-3xl md:text-4xl font-extrabold">Sample Questions</h1>
          </div>
          <p className="text-white/90">JEE Advanced 2023 · Sample from our premium question bank</p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 -mt-6">
        <div className="bg-white rounded-2xl shadow-lg p-5 border-l-4 border-indigo-600 flex items-start gap-3">
          <Award className="w-6 h-6 text-indigo-600 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-slate-900">Real JEE Advanced questions</div>
            <p className="text-slate-600 text-sm">These are actual questions from our bank. Sign up to unlock detailed solutions and 10,000+ more.</p>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
        {questions.map((q) => (
          <div key={q.id} className="bg-white rounded-2xl shadow-lg overflow-hidden" data-testid={`sample-q${q.number}`}>
            <div className="bg-gradient-to-r from-slate-50 to-indigo-50 p-5 border-b">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 bg-indigo-600 text-white rounded-full text-xs font-semibold">Q{q.number}</span>
                <span className="px-2.5 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">{q.subject}</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${diffColors[q.difficulty]}`}>{q.difficulty}</span>
                <span className="px-2.5 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">{q.type}</span>
                <span className="ml-auto text-xs text-slate-500">{q.examType} · {q.year}</span>
              </div>
              <div className="text-xs text-slate-600"><span className="font-medium">{q.chapter}</span> · {q.topic}</div>
            </div>

            <div className="p-5 space-y-4">
              <p className="text-slate-800 leading-relaxed">{q.questionText}</p>
              {q.imageUrl && (
                <div className="bg-slate-50 rounded-lg p-3 flex justify-center">
                  <img src={q.imageUrl} alt={`Question ${q.number}`} className="max-w-full rounded border" />
                </div>
              )}
              <div className="space-y-2">
                {q.options.map((opt, idx) => (
                  <div key={idx} className="p-3 border-2 border-slate-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition cursor-pointer">
                    <p className="text-slate-800 text-sm">{opt}</p>
                  </div>
                ))}
              </div>

              <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-1.5">
                  <Lock className="w-4 h-4 text-amber-600" />
                  <div className="font-semibold text-slate-900">Solution locked</div>
                </div>
                <p className="text-sm text-slate-700 mb-3">Sign up to see the detailed step-by-step solution and unlock 10,000+ more questions.</p>
                <button
                  onClick={() => navigate('/signup')}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 text-sm"
                  data-testid="sample-signup-btn"
                >
                  Sign up for free <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}

        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-7 text-center text-white">
          <h3 className="text-2xl font-extrabold mb-2">Want 10,000+ questions like these?</h3>
          <p className="text-white/90 mb-5">Join NexUacademy for the full question bank, detailed solutions, live classes, and mentorship.</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <button onClick={() => navigate('/signup')} className="px-6 py-3 bg-white text-indigo-700 rounded-lg font-bold hover:bg-slate-100 transition">Sign up — it's free</button>
            <Link to="/#contact" className="px-6 py-3 border-2 border-white rounded-lg font-bold hover:bg-white hover:text-indigo-700 transition">Book a free demo</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SampleQuestions;
