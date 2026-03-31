import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Clock, Flag, ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';

const TakeTest = () => {
  const { attemptId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    setPageTitle('Take Test');
  }, []);

  const [test, setTest] = useState(location.state?.test || null);
  const [attempt, setAttempt] = useState(location.state?.attempt || null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [flagged, setFlagged] = useState({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (test) {
      setTimeLeft(test.duration * 60);
    }
  }, [test]);

  useEffect(() => {
    if (timeLeft <= 0 && test) {
      handleSubmit(true);
      return;
    }
    const timer = setInterval(() => setTimeLeft((t) => t - 1), 1000);
    return () => clearInterval(timer);
  }, [timeLeft, test]);

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  };

  const handleSelect = (qNum, option) => {
    setAnswers((prev) => ({ ...prev, [qNum]: option }));
  };

  const toggleFlag = (qNum) => {
    setFlagged((prev) => ({ ...prev, [qNum]: !prev[qNum] }));
  };

  const clearAnswer = (qNum) => {
    setAnswers((prev) => { const n = { ...prev }; delete n[qNum]; return n; });
  };

  const handleSubmit = useCallback(async (auto = false) => {
    if (submitting) return;
    if (!auto && !window.confirm('Are you sure you want to submit?')) return;
    setSubmitting(true);

    const questions = test?.questions || [];
    const answerList = questions.map((q) => ({
      question_number: q.question_number,
      selected_answer: answers[q.question_number] || '',
      time_taken: 0,
      flagged: !!flagged[q.question_number],
    }));

    try {
      const res = await api.post(`/student/tests/attempts/${attemptId}/submit`, {
        answers: answerList,
        time_spent: (test.duration * 60) - timeLeft,
      });
      toast.success(auto ? 'Time up! Test auto-submitted.' : 'Test submitted successfully!');
      navigate(`/test-results/${attemptId}`, { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit');
      setSubmitting(false);
    }
  }, [submitting, test, answers, flagged, attemptId, timeLeft, navigate]);

  if (!test || !test.questions) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-400">Loading test...</p>
      </div>
    );
  }

  const questions = test.questions;
  const currentQ = questions[currentIdx];
  const answered = Object.keys(answers).length;
  const total = questions.length;

  return (
    <div className="min-h-screen bg-slate-50" data-testid="take-test-page">
      {/* Top bar */}
      <div className="sticky top-0 z-50 bg-white border-b shadow-sm px-4 py-3 flex items-center justify-between">
        <h2 className="font-semibold text-slate-900 truncate">{test.test_name}</h2>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-1.5 font-mono text-lg font-bold ${timeLeft < 300 ? 'text-red-600 animate-pulse' : 'text-slate-700'}`} data-testid="test-timer">
            <Clock className="h-5 w-5" />
            {formatTime(timeLeft)}
          </div>
          <Button className="bg-red-500 hover:bg-red-600 text-white" onClick={() => handleSubmit(false)} disabled={submitting} data-testid="submit-test-btn">
            {submitting ? 'Submitting...' : 'Submit Test'}
          </Button>
        </div>
      </div>

      <div className="flex h-[calc(100vh-60px)]">
        {/* Main question area */}
        <div className="flex-1 p-6 overflow-y-auto">
          <Card className="border-0 shadow-sm max-w-3xl mx-auto">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-indigo-600" data-testid="question-number">
                  Question {currentQ.question_number} of {total}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">+{currentQ.marks} / {currentQ.negative_marks}</span>
                  <Button variant="ghost" size="sm" onClick={() => toggleFlag(currentQ.question_number)} data-testid="flag-question-btn">
                    <Flag className={`h-4 w-4 ${flagged[currentQ.question_number] ? 'text-amber-500 fill-amber-500' : 'text-slate-400'}`} />
                  </Button>
                </div>
              </div>

              <div className="text-base text-slate-800 mb-6 whitespace-pre-wrap" data-testid="question-text">
                {currentQ.question_text}
              </div>
              {currentQ.question_image_url && (
                <img src={currentQ.question_image_url} alt="Question" className="max-w-full max-h-60 mb-6 rounded-lg" />
              )}

              <div className="space-y-3">
                {Object.entries(currentQ.options).map(([key, val]) => (
                  <button
                    key={key}
                    className={`w-full text-left p-4 rounded-xl border-2 transition-all ${answers[currentQ.question_number] === key ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-slate-300'}`}
                    onClick={() => handleSelect(currentQ.question_number, key)}
                    data-testid={`option-${key}`}
                  >
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-medium mr-3 ${answers[currentQ.question_number] === key ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                      {key}
                    </span>
                    {val}
                  </button>
                ))}
              </div>

              {answers[currentQ.question_number] && (
                <Button variant="ghost" size="sm" className="mt-3 text-slate-400" onClick={() => clearAnswer(currentQ.question_number)}>
                  Clear Answer
                </Button>
              )}

              <div className="flex justify-between mt-8">
                <Button variant="outline" disabled={currentIdx === 0} onClick={() => setCurrentIdx(currentIdx - 1)} data-testid="prev-question-btn">
                  <ChevronLeft className="h-4 w-4 mr-1" /> Previous
                </Button>
                <Button variant="outline" disabled={currentIdx === total - 1} onClick={() => setCurrentIdx(currentIdx + 1)} data-testid="next-question-btn">
                  Next <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Question palette sidebar */}
        <div className="hidden md:block w-64 border-l bg-white p-4 overflow-y-auto">
          <div className="mb-4">
            <p className="text-xs text-slate-400 mb-2">Progress: {answered}/{total} answered</p>
            <div className="w-full bg-slate-100 h-2 rounded-full">
              <div className="bg-indigo-600 h-2 rounded-full transition-all" style={{ width: `${(answered / total) * 100}%` }} />
            </div>
          </div>
          <div className="grid grid-cols-5 gap-2" data-testid="question-palette">
            {questions.map((q, i) => {
              const isAnswered = !!answers[q.question_number];
              const isFlagged = !!flagged[q.question_number];
              const isCurrent = i === currentIdx;
              return (
                <button
                  key={i}
                  className={`w-9 h-9 rounded-lg text-xs font-medium border transition-all ${isCurrent ? 'ring-2 ring-indigo-400' : ''} ${isAnswered ? 'bg-green-500 text-white border-green-500' : isFlagged ? 'bg-amber-100 text-amber-700 border-amber-300' : 'bg-white text-slate-600 border-slate-200'}`}
                  onClick={() => setCurrentIdx(i)}
                >
                  {q.question_number}
                </button>
              );
            })}
          </div>
          <div className="mt-4 space-y-1 text-xs text-slate-400">
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-green-500" /> Answered</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-amber-100 border border-amber-300" /> Flagged</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-white border border-slate-200" /> Not answered</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TakeTest;
