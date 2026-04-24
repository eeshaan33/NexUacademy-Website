import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  FileEdit, Sparkles, ChevronRight, ChevronLeft, PlayCircle, History,
  CheckCircle, Loader2, Target,
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { setPageTitle } from '../utils/pageTitle';

const SUBJECTS = ['Physics', 'Chemistry', 'Mathematics'];
const DIFFICULTIES = ['Mixed', 'Easy', 'Medium', 'Hard'];
const EXAM_TYPES = ['Mixed', 'JEE_Main', 'JEE_Advanced'];
const CURRENT_YEAR = new Date().getFullYear();

const MyTestsPage = () => {
  const navigate = useNavigate();
  const [view, setView] = useState('home');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const [step, setStep] = useState(1);
  const [examType, setExamType] = useState('JEE_Main');
  const [yearRange, setYearRange] = useState({ start: 2015, end: CURRENT_YEAR });
  const [difficulty, setDifficulty] = useState('Mixed');
  const [duration, setDuration] = useState(60);
  const [perChapter, setPerChapter] = useState(5);
  const [syllabus, setSyllabus] = useState(null);
  const [selected, setSelected] = useState({});
  const [generating, setGenerating] = useState(false);
  const [lastGenerated, setLastGenerated] = useState(null);

  useEffect(() => { setPageTitle('My Tests'); loadHistory(); }, []);
  useEffect(() => { if (view === 'builder' && !syllabus) loadSyllabus(); }, [view]); // eslint-disable-line

  const loadHistory = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/custom-tests/history/mine');
      setHistory(data.attempts || []);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const loadSyllabus = async () => {
    try {
      const { data } = await api.get('/custom-tests/syllabus');
      setSyllabus(data);
    } catch (e) {
      toast.error('Failed to load syllabus');
    }
  };

  const totalQuestions = useMemo(
    () => Object.values(selected).reduce((sum, s) => sum + (s.questionCount || 0), 0),
    [selected]
  );

  const toggleChapter = (subject, chapter) => {
    const key = `${subject}|${chapter.chapter}`;
    setSelected((prev) => {
      const next = { ...prev };
      if (next[key]) delete next[key];
      else next[key] = { subject, chapter: chapter.chapter, topic: chapter.chapter, questionCount: perChapter, difficulty };
      return next;
    });
  };

  const updateChapterCount = (key, n) => {
    setSelected((prev) => ({ ...prev, [key]: { ...prev[key], questionCount: Math.max(1, Math.min(30, Number(n) || 1)) } }));
  };

  const generateTest = async () => {
    if (totalQuestions < 5) { toast.error('Select at least 5 questions'); return; }
    setGenerating(true);
    try {
      const payload = {
        examType,
        selectedTopics: Object.values(selected).map((s) => ({ ...s, difficulty })),
        yearRange,
        duration,
        totalQuestions,
        totalMarks: totalQuestions * 4,
      };
      const { data } = await api.post('/custom-tests/generate', payload);
      setLastGenerated(data);
      if (data.warnings?.length) {
        toast.warning(`Test created with ${data.total_questions} questions (some chapters had fewer available).`);
      } else {
        toast.success('Custom test ready!');
      }
      setView('ready');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to generate test');
    } finally {
      setGenerating(false);
    }
  };

  const startTest = (testId) => navigate(`/my-tests/take/${testId}`);

  if (view === 'home') {
    return (
      <div className="max-w-5xl mx-auto p-6 space-y-6" data-testid="my-tests-page">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
              <FileEdit className="h-7 w-7 text-indigo-600" /> My Tests
            </h1>
            <p className="text-sm text-slate-500 mt-1">Build custom practice tests from the PYQ bank and review your attempts.</p>
          </div>
          <Button onClick={() => { setView('builder'); setStep(1); setSelected({}); setLastGenerated(null); }} className="bg-indigo-600 hover:bg-indigo-700" data-testid="build-test-btn">
            <Sparkles className="h-4 w-4 mr-2" /> Build Custom Test
          </Button>
        </div>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <History className="h-5 w-5 text-slate-500" />
              <h2 className="font-semibold text-slate-700">Recent Attempts</h2>
            </div>
            {loading ? (
              <div className="py-8 text-center text-slate-400">Loading…</div>
            ) : history.length === 0 ? (
              <div className="py-10 text-center space-y-2">
                <Target className="h-10 w-10 text-slate-300 mx-auto" />
                <p className="text-slate-500">No custom tests yet</p>
                <p className="text-sm text-slate-400">Click "Build Custom Test" to create your first practice test.</p>
              </div>
            ) : (
              <div className="divide-y">
                {history.map((a) => (
                  <div key={a.attempt_id} className="py-3 flex items-center justify-between gap-3" data-testid={`history-${a.attempt_id}`}>
                    <div className="min-w-0">
                      <div className="font-medium text-slate-800 truncate">{a.test_name || a.test_id}</div>
                      <div className="text-xs text-slate-400 flex flex-wrap items-center gap-2 mt-0.5">
                        <span>{new Date(a.submitted_at).toLocaleString()}</span>
                        {a.exam_type && <Badge variant="outline" className="text-[10px]">{a.exam_type.replace('_', ' ')}</Badge>}
                        {a.subject_breakdown && (
                          <span className="text-slate-400">
                            {Object.entries(a.subject_breakdown).filter(([, n]) => n > 0).map(([s, n]) => `${s.charAt(0)} ${n}`).join(' · ')}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="font-semibold text-slate-900">{a.total_marks}<span className="text-xs text-slate-400"> / {a.max_marks}</span></div>
                      <div className={`text-xs font-medium ${a.accuracy >= 60 ? 'text-emerald-600' : a.accuracy >= 40 ? 'text-amber-600' : 'text-red-500'}`}>{a.accuracy}% accuracy</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (view === 'ready' && lastGenerated) {
    return (
      <div className="max-w-xl mx-auto p-6">
        <Card className="border-0 shadow-lg">
          <CardContent className="p-8 text-center space-y-4">
            <div className="mx-auto bg-emerald-100 p-4 rounded-full w-fit">
              <CheckCircle className="h-10 w-10 text-emerald-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">Test Ready!</h2>
            <p className="text-slate-600">{lastGenerated.test_name}</p>
            <div className="grid grid-cols-3 gap-3 py-3">
              <div className="bg-slate-50 rounded p-3">
                <div className="text-xs text-slate-500">Questions</div>
                <div className="text-2xl font-bold">{lastGenerated.total_questions}</div>
              </div>
              <div className="bg-slate-50 rounded p-3">
                <div className="text-xs text-slate-500">Marks</div>
                <div className="text-2xl font-bold">{lastGenerated.total_marks}</div>
              </div>
              <div className="bg-slate-50 rounded p-3">
                <div className="text-xs text-slate-500">Duration</div>
                <div className="text-2xl font-bold">{lastGenerated.duration}m</div>
              </div>
            </div>
            {lastGenerated.subject_breakdown && (
              <div className="flex flex-wrap justify-center gap-2">
                {Object.entries(lastGenerated.subject_breakdown).map(([s, n]) => n > 0 && (
                  <Badge key={s} variant="outline">{s}: {n}</Badge>
                ))}
              </div>
            )}
            <div className="flex gap-2 pt-2">
              <Button variant="outline" className="flex-1" onClick={() => setView('home')}>Later</Button>
              <Button className="flex-1 bg-indigo-600 hover:bg-indigo-700" onClick={() => startTest(lastGenerated.test_id)} data-testid="start-custom-test">
                <PlayCircle className="h-4 w-4 mr-1" /> Start Now
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Builder
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-5" data-testid="custom-test-builder">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => setView('home')}>
          <ChevronLeft className="h-4 w-4 mr-1" /> Back
        </Button>
        <h1 className="text-2xl font-bold text-slate-900">Build Custom Test</h1>
        <Badge variant="outline" className="ml-2">Step {step} / 2</Badge>
      </div>

      {step === 1 && (
        <Card className="border-0 shadow-sm">
          <CardContent className="p-6 space-y-5">
            <h2 className="font-semibold text-slate-700">Test Configuration</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label>Exam Source</Label>
                <Select value={examType} onValueChange={setExamType}>
                  <SelectTrigger data-testid="exam-type-select"><SelectValue /></SelectTrigger>
                  <SelectContent>{EXAM_TYPES.map((e) => <SelectItem key={e} value={e}>{e.replace('_', ' ')}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label>Difficulty</Label>
                <Select value={difficulty} onValueChange={setDifficulty}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{DIFFICULTIES.map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label>Year Range</Label>
                <div className="flex gap-2 mt-1">
                  <Input type="number" value={yearRange.start} onChange={(e) => setYearRange({ ...yearRange, start: Number(e.target.value) })} min={2000} max={CURRENT_YEAR} />
                  <span className="self-center text-slate-400">to</span>
                  <Input type="number" value={yearRange.end} onChange={(e) => setYearRange({ ...yearRange, end: Number(e.target.value) })} min={2000} max={CURRENT_YEAR} />
                </div>
              </div>
              <div>
                <Label>Duration (minutes)</Label>
                <Input type="number" value={duration} onChange={(e) => setDuration(Math.max(10, Number(e.target.value) || 60))} data-testid="duration-input" />
              </div>
              <div>
                <Label>Default Questions per Chapter</Label>
                <Input type="number" min={1} max={30} value={perChapter} onChange={(e) => setPerChapter(Math.max(1, Math.min(30, Number(e.target.value) || 5)))} />
              </div>
            </div>
            <div className="pt-4 flex justify-end">
              <Button onClick={() => setStep(2)} className="bg-indigo-600 hover:bg-indigo-700" data-testid="builder-step-next">
                Next: Pick Chapters <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <>
          <Card className="border-0 shadow-sm">
            <CardContent className="p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-slate-700">Pick Chapters</h2>
                <div className="text-sm text-slate-500">
                  <span className="font-bold text-indigo-600">{Object.keys(selected).length}</span> chapters ·
                  <span className="font-bold text-indigo-600 ml-1">{totalQuestions}</span> questions
                </div>
              </div>

              {!syllabus ? (
                <div className="py-10 text-center text-slate-400"><Loader2 className="h-5 w-5 animate-spin mx-auto" /> Loading syllabus…</div>
              ) : (
                <div className="space-y-6">
                  {SUBJECTS.map((subject) => {
                    const chapters = [
                      ...(syllabus[subject]?.Class11 || []),
                      ...(syllabus[subject]?.Class12 || []),
                    ].filter((c) => c.questionCount > 0);
                    if (!chapters.length) return null;
                    return (
                      <div key={subject}>
                        <h3 className="text-sm font-semibold text-slate-700 mb-2">{subject} ({chapters.length} chapters)</h3>
                        <div className="grid md:grid-cols-2 gap-2">
                          {chapters.map((ch) => {
                            const key = `${subject}|${ch.chapter}`;
                            const isOn = !!selected[key];
                            return (
                              <div
                                key={key}
                                className={`p-3 rounded-lg border-2 transition-all cursor-pointer ${isOn ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-300'}`}
                                onClick={() => toggleChapter(subject, ch)}
                                data-testid={`chapter-${subject}-${ch.chapter}`}
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <div className="min-w-0">
                                    <div className="text-sm font-medium text-slate-800 truncate">{ch.chapter}</div>
                                    <div className="text-xs text-slate-400">{ch.questionCount} available</div>
                                  </div>
                                  {isOn ? (
                                    <Input
                                      type="number"
                                      min={1}
                                      max={30}
                                      value={selected[key].questionCount}
                                      onChange={(e) => updateChapterCount(key, e.target.value)}
                                      onClick={(e) => e.stopPropagation()}
                                      className="w-16 h-8 text-center shrink-0"
                                    />
                                  ) : <span className="text-slate-300 text-xs">Add</span>}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex items-center justify-between">
            <Button variant="outline" onClick={() => setStep(1)}>
              <ChevronLeft className="h-4 w-4 mr-1" /> Back
            </Button>
            <Button onClick={generateTest} disabled={generating || totalQuestions < 5} className="bg-indigo-600 hover:bg-indigo-700" data-testid="generate-test-btn">
              {generating ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Generating…</> : <><Sparkles className="h-4 w-4 mr-1" /> Generate Test ({totalQuestions} Qs)</>}
            </Button>
          </div>
        </>
      )}
    </div>
  );
};

export default MyTestsPage;
