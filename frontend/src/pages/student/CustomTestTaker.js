import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Clock, ArrowLeft, Send, CheckCircle, XCircle, Minus, Target } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';

const CustomTestTaker = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState({}); // {qNumber: "A"}
  const [timeLeft, setTimeLeft] = useState(0);
  const [startTs] = useState(Date.now());
  const [submitted, setSubmitted] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => { setPageTitle('Custom Test'); }, []);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/custom-tests/${testId}`);
        setTest(data);
        setTimeLeft((data.duration || 60) * 60);
      } catch { toast.error('Failed to load test'); navigate('/my-tests'); }
      finally { setLoading(false); }
    })();
  }, [testId]); // eslint-disable-line

  // Timer
  useEffect(() => {
    if (!test || submitted) return;
    if (timeLeft <= 0) { handleSubmit(true); return; }
    const id = setInterval(() => setTimeLeft((t) => t - 1), 1000);
    return () => clearInterval(id);
  }, [timeLeft, test, submitted]); // eslint-disable-line

  const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  const attempted = useMemo(() => Object.keys(answers).length, [answers]);

  const handleSelect = (qNum, opt) => {
    setAnswers((prev) => ({ ...prev, [qNum]: opt }));
  };

  const handleSubmit = async (auto = false) => {
    if (!auto && !window.confirm(`Submit test now? You attempted ${attempted} of ${test.questions.length}.`)) return;
    setBusy(true);
    try {
      const timeSpent = Math.floor((Date.now() - startTs) / 1000);
      const { data } = await api.post(`/custom-tests/${testId}/submit`, { answers, timeSpent });
      setSubmitted(data.results);
      toast.success('Test submitted!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Submission failed');
    } finally { setBusy(false); }
  };

  if (loading) return <div className="p-10 text-center text-slate-400">Loading test…</div>;
  if (!test) return null;

  if (submitted) {
    const { correct, incorrect, unattempted, totalMarks, maxMarks, percentage, accuracy } = submitted;
    return (
      <div className="max-w-3xl mx-auto p-6">
        <Card className="border-0 shadow-lg">
          <CardContent className="p-8 space-y-5 text-center">
            <div className="mx-auto bg-emerald-100 p-4 rounded-full w-fit">
              <CheckCircle className="h-10 w-10 text-emerald-600" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900">Test Submitted!</h1>
            <div className="text-4xl font-bold text-indigo-600">{totalMarks} <span className="text-lg text-slate-400">/ {maxMarks}</span></div>
            <div className="text-sm text-slate-500">{percentage}% · Accuracy {accuracy}%</div>
            <div className="grid grid-cols-3 gap-3">
              <div className="p-4 bg-green-50 rounded-lg"><CheckCircle className="h-5 w-5 mx-auto text-green-600 mb-1" /><div className="text-2xl font-bold">{correct}</div><div className="text-xs text-slate-500">Correct</div></div>
              <div className="p-4 bg-red-50 rounded-lg"><XCircle className="h-5 w-5 mx-auto text-red-600 mb-1" /><div className="text-2xl font-bold">{incorrect}</div><div className="text-xs text-slate-500">Incorrect</div></div>
              <div className="p-4 bg-slate-50 rounded-lg"><Minus className="h-5 w-5 mx-auto text-slate-400 mb-1" /><div className="text-2xl font-bold">{unattempted}</div><div className="text-xs text-slate-500">Skipped</div></div>
            </div>
            <Button className="w-full bg-indigo-600 hover:bg-indigo-700" onClick={() => navigate('/my-tests')} data-testid="back-to-my-tests">
              <ArrowLeft className="h-4 w-4 mr-1" /> Back to My Tests
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const q = test.questions[current];

  return (
    <div className="min-h-screen bg-slate-50" data-testid="custom-test-taker">
      <div className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="font-semibold text-slate-900 truncate">{test.test_name}</div>
            <div className="text-xs text-slate-500">
              <Target className="inline h-3 w-3 mr-1" />
              {attempted} / {test.questions.length} attempted
            </div>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-mono font-semibold ${timeLeft < 60 ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700'}`}>
            <Clock className="h-4 w-4" /> {fmt(timeLeft)}
          </div>
          <Button onClick={() => handleSubmit(false)} disabled={busy} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-custom-test">
            <Send className="h-4 w-4 mr-1" /> Submit
          </Button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto p-4 grid md:grid-cols-[1fr_240px] gap-4">
        <Card className="border-0 shadow-sm">
          <CardContent className="p-6 space-y-4">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <Badge>Q{q.questionNumber}</Badge>
              <Badge variant="outline">{q.subject}</Badge>
              <Badge variant="outline">{q.chapter}</Badge>
              {q.year && <Badge variant="secondary">{q.year}</Badge>}
              {q.difficulty && <Badge variant="secondary">{q.difficulty}</Badge>}
            </div>
            <div className="text-base text-slate-800 whitespace-pre-wrap">{q.questionText}</div>

            <div className="space-y-2 pt-2">
              {['A', 'B', 'C', 'D'].map((opt) => {
                const text = q.options?.[opt];
                if (!text) return null;
                const isSelected = answers[q.questionNumber] === opt;
                return (
                  <div
                    key={opt}
                    onClick={() => handleSelect(q.questionNumber, opt)}
                    data-testid={`ct-option-${opt}`}
                    className={`p-3 rounded-lg border-2 cursor-pointer transition ${isSelected ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-300'}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-7 h-7 shrink-0 rounded-full border-2 flex items-center justify-center text-sm font-bold ${isSelected ? 'bg-indigo-500 text-white border-indigo-500' : 'border-slate-300 text-slate-500'}`}>{opt}</div>
                      <div className="flex-1 text-sm">{text}</div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex items-center justify-between pt-3 border-t">
              <Button variant="outline" onClick={() => setCurrent(Math.max(0, current - 1))} disabled={current === 0}>
                <ArrowLeft className="h-4 w-4 mr-1" /> Previous
              </Button>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => { const n = { ...answers }; delete n[q.questionNumber]; setAnswers(n); }}>
                  Clear
                </Button>
                <Button onClick={() => setCurrent(Math.min(test.questions.length - 1, current + 1))} disabled={current === test.questions.length - 1}>
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm h-fit">
          <CardContent className="p-4 space-y-3">
            <div className="text-sm font-semibold text-slate-700">Question Palette</div>
            <div className="grid grid-cols-5 gap-1.5">
              {test.questions.map((_, idx) => {
                const qn = test.questions[idx].questionNumber;
                const answered = answers[qn] != null;
                const isCurrent = idx === current;
                return (
                  <button
                    key={qn}
                    onClick={() => setCurrent(idx)}
                    data-testid={`palette-${qn}`}
                    className={`h-8 rounded text-xs font-semibold transition ${isCurrent ? 'ring-2 ring-indigo-500 ' : ''}${answered ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                  >
                    {qn}
                  </button>
                );
              })}
            </div>
            <div className="text-xs text-slate-500 pt-2 border-t">
              <div className="flex items-center gap-2"><span className="inline-block w-3 h-3 rounded bg-emerald-500" />Answered</div>
              <div className="flex items-center gap-2 mt-1"><span className="inline-block w-3 h-3 rounded bg-slate-100 border" />Unattempted</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CustomTestTaker;
