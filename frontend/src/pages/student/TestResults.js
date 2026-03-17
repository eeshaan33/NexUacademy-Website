import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { CheckCircle, XCircle, Minus, ArrowLeft, MessageSquare } from 'lucide-react';
import api from '../../utils/api';

const TestResults = () => {
  const { attemptId } = useParams();
  const [attempt, setAttempt] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/student/tests/results/${attemptId}`);
        setAttempt(res.data.attempt);
      } catch { }
      finally { setLoading(false); }
    };
    load();
  }, [attemptId]);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-slate-400">Loading results...</div>;
  }

  if (!attempt) {
    return <div className="min-h-screen flex items-center justify-center text-slate-400">Results not found</div>;
  }

  const { total_score, max_score, correct_answers, incorrect_answers, unattempted, accuracy, answers, test_name, time_spent } = attempt;
  const scorePercent = max_score > 0 ? ((total_score / max_score) * 100).toFixed(1) : 0;
  const formatTime = (s) => `${Math.floor(s / 60)}m ${s % 60}s`;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6" data-testid="test-results-page">
      <div className="flex items-center gap-3">
        <Link to="/assigned-tests">
          <Button variant="ghost" size="sm"><ArrowLeft className="h-4 w-4" /></Button>
        </Link>
        <h1 className="text-2xl font-bold text-slate-900">{test_name || 'Test Results'}</h1>
      </div>

      {/* Score Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <Card className="border-0 shadow-sm bg-gradient-to-br from-indigo-500 to-purple-600 text-white col-span-2 lg:col-span-1">
          <CardContent className="p-5 text-center">
            <p className="text-4xl font-bold">{total_score}</p>
            <p className="text-sm opacity-80">/ {max_score}</p>
            <p className="text-xs opacity-60 mt-1">{scorePercent}%</p>
          </CardContent>
        </Card>
        {[
          { label: 'Correct', value: correct_answers, icon: CheckCircle, color: 'text-green-600 bg-green-50' },
          { label: 'Incorrect', value: incorrect_answers, icon: XCircle, color: 'text-red-600 bg-red-50' },
          { label: 'Unattempted', value: unattempted, icon: Minus, color: 'text-slate-600 bg-slate-50' },
          { label: 'Accuracy', value: `${accuracy}%`, icon: CheckCircle, color: 'text-blue-600 bg-blue-50' },
        ].map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.label} className="border-0 shadow-sm">
              <CardContent className={`p-5 text-center ${s.color} rounded-xl`}>
                <Icon className="h-5 w-5 mx-auto mb-1" />
                <p className="text-2xl font-bold">{s.value}</p>
                <p className="text-xs opacity-70">{s.label}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {time_spent > 0 && (
        <p className="text-sm text-slate-400">Time spent: {formatTime(time_spent)}</p>
      )}

      {/* Questions Review */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-700">Question-wise Review</h2>
        {(answers || []).map((ans, i) => {
          const isCorrect = ans.is_correct;
          const isUnattempted = !ans.selected_answer;
          return (
            <Card key={i} className={`border-0 shadow-sm border-l-4 ${isCorrect ? 'border-l-green-500' : isUnattempted ? 'border-l-slate-300' : 'border-l-red-500'}`} data-testid={`result-q${ans.question_number}`}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <span className="text-sm font-medium text-slate-500">Q{ans.question_number}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${isCorrect ? 'bg-green-100 text-green-700' : isUnattempted ? 'bg-slate-100 text-slate-500' : 'bg-red-100 text-red-700'}`}>
                    {isCorrect ? `+${ans.marks}` : isUnattempted ? '0' : ans.marks}
                  </span>
                </div>

                <p className="text-base text-slate-800 mb-3 whitespace-pre-wrap">{ans.question_text}</p>
                {ans.question_image_url && <img src={ans.question_image_url} alt="" className="max-w-full max-h-40 mb-3 rounded" />}

                <div className="grid grid-cols-2 gap-2 mb-3">
                  {Object.entries(ans.options || {}).map(([key, val]) => {
                    const isSelected = ans.selected_answer === key;
                    const isAnswer = ans.correct_answer === key;
                    return (
                      <div
                        key={key}
                        className={`p-3 rounded-lg border text-sm ${isAnswer ? 'bg-green-50 border-green-300' : isSelected && !isCorrect ? 'bg-red-50 border-red-300' : 'bg-white border-slate-200'}`}
                      >
                        <span className={`font-medium ${isAnswer ? 'text-green-700' : isSelected ? 'text-red-700' : 'text-slate-500'}`}>
                          {key})
                        </span>{' '}
                        {val}
                        {isAnswer && <CheckCircle className="inline h-3.5 w-3.5 ml-1 text-green-500" />}
                        {isSelected && !isCorrect && <XCircle className="inline h-3.5 w-3.5 ml-1 text-red-500" />}
                      </div>
                    );
                  })}
                </div>

                {/* Teacher Note - ONLY shown for incorrect/unattempted */}
                {ans.teacher_note && (
                  <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg" data-testid={`teacher-note-q${ans.question_number}`}>
                    <div className="flex items-center gap-2 text-amber-700 text-sm font-medium mb-1">
                      <MessageSquare className="h-4 w-4" />
                      Teacher's Note
                    </div>
                    <p className="text-sm text-amber-800">{ans.teacher_note}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="pb-8">
        <Link to="/assigned-tests">
          <Button variant="outline" className="w-full" data-testid="back-to-tests-btn">
            <ArrowLeft className="h-4 w-4 mr-2" /> Back to Assigned Tests
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default TestResults;
