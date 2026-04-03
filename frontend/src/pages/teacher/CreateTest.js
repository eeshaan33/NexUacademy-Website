import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Plus, Trash2, ChevronRight, ChevronLeft, Eye, Send, Image as ImageIcon, X, Upload } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';

const SUBJECTS = ['Physics', 'Chemistry', 'Mathematics', 'All Subjects'];
const DIFFICULTIES = ['Easy', 'Medium', 'Hard'];

const CreateTest = () => {
  const navigate = useNavigate();
  const [tests, setTests] = useState([]);
  const [step, setStep] = useState('list');
  const [loading, setLoading] = useState(false);
  const [batches, setBatches] = useState([]);
  const [form, setForm] = useState({
    test_name: '', exam_type: 'JEE_Main', test_pattern: 'JEE_Main_Pattern',
    subject: 'All Subjects', test_type: 'Full Length', duration: 180,
    scheduled_date_time: '', assigned_batches: [], instructions: '',
    allow_reattempts: false, randomize_questions: false,
  });
  const [currentTestId, setCurrentTestId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [qForm, setQForm] = useState(defaultQuestion(1));

  useEffect(() => { setPageTitle('Create Test'); loadTests(); loadBatches(); }, []);

  function defaultQuestion(num) {
    return {
      question_number: num, question_text: '', question_image_url: '',
      question_type: 'MCQ_Single',
      options: { A: { text: '', imageUrl: '' }, B: { text: '', imageUrl: '' }, C: { text: '', imageUrl: '' }, D: { text: '', imageUrl: '' } },
      correct_answers: [], numerical_answer: '', answer_range: { min: '', max: '' },
      marks: 4, negative_marks: -1, subject: '', chapter: '', difficulty: 'Medium', teacher_note: '',
    };
  }

  const loadTests = async () => {
    try { const { data } = await api.get('/teacher/tests/'); setTests(data.tests || []); } catch {}
  };
  const loadBatches = async () => {
    try { const { data } = await api.get('/batches/'); setBatches(data.batches || []); } catch {}
  };

  const handleImageUpload = async (file, cb) => {
    const fd = new FormData();
    fd.append('file', file);
    try {
      const { data } = await api.post('/upload/image', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      cb(data.url);
      toast.success('Image uploaded');
    } catch { toast.error('Upload failed'); }
  };

  const handleCreateTest = async () => {
    if (!form.test_name || !form.scheduled_date_time || form.assigned_batches.length === 0) {
      toast.error('Fill all required fields'); return;
    }
    setLoading(true);
    try {
      const { data } = await api.post('/teacher/tests/create', { ...form, questions: [] });
      setCurrentTestId(data.test.test_id);
      setStep('questions');
      toast.success('Test created. Now add questions.');
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const handleAddQuestion = async () => {
    if (!qForm.question_text.trim()) { toast.error('Enter question text'); return; }
    if (qForm.question_type.startsWith('MCQ') && qForm.correct_answers.length === 0) { toast.error('Select correct answer(s)'); return; }
    if (qForm.question_type.startsWith('Numerical') && !qForm.numerical_answer && qForm.numerical_answer !== 0) { toast.error('Enter numerical answer'); return; }
    setLoading(true);
    try {
      const payload = { ...qForm };
      if (qForm.question_type.startsWith('Numerical')) {
        payload.numerical_answer = parseFloat(qForm.numerical_answer);
        if (qForm.answer_range.min !== '' && qForm.answer_range.max !== '') {
          payload.answer_range = { min: parseFloat(qForm.answer_range.min), max: parseFloat(qForm.answer_range.max) };
        } else { payload.answer_range = null; }
      }
      const { data } = await api.post(`/teacher/tests/${currentTestId}/add-question`, payload);
      setQuestions([...questions, { ...qForm, question_number: data.question_number }]);
      setQForm(defaultQuestion(data.question_number + 1));
      toast.success(`Q${data.question_number} added (${data.total_questions} total)`);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const handlePublish = async () => {
    try {
      await api.put(`/teacher/tests/${currentTestId}/publish`);
      toast.success('Test published!');
      setStep('list'); loadTests();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
  };

  const toggleBatch = (batchId) => {
    setForm(f => ({
      ...f, assigned_batches: f.assigned_batches.includes(batchId)
        ? f.assigned_batches.filter(b => b !== batchId) : [...f.assigned_batches, batchId]
    }));
  };

  const toggleCorrectAnswer = (opt) => {
    if (qForm.question_type === 'MCQ_Single') {
      setQForm({ ...qForm, correct_answers: [opt] });
    } else {
      setQForm(q => ({
        ...q, correct_answers: q.correct_answers.includes(opt)
          ? q.correct_answers.filter(a => a !== opt) : [...q.correct_answers, opt]
      }));
    }
  };

  // TEST LIST
  if (step === 'list') return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Tests</h1>
        <Button onClick={() => setStep('config')} data-testid="create-test-btn"><Plus className="h-4 w-4 mr-2" />Create Test</Button>
      </div>
      {tests.length === 0 ? <p className="text-muted-foreground text-center py-12">No tests yet.</p> : (
        <div className="grid gap-4">
          {tests.map(t => (
            <Card key={t.test_id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex justify-between items-center">
                <div>
                  <h3 className="font-semibold">{t.test_name}</h3>
                  <p className="text-sm text-muted-foreground">{t.exam_type} | {t.subject} | {t.total_questions || 0} Qs | {t.duration}min</p>
                  <p className="text-xs text-muted-foreground">Batches: {(t.assigned_batches || []).join(', ')}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs rounded ${t.status === 'scheduled' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{t.status}</span>
                  <span className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded">{t.test_pattern === 'JEE_Advanced_Pattern' ? 'JEE Adv' : 'JEE Main'} UI</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  // TEST CONFIG
  if (step === 'config') return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" onClick={() => setStep('list')}><ChevronLeft className="h-4 w-4" /></Button>
        <h1 className="text-2xl font-bold">Test Configuration</h1>
      </div>
      <Card>
        <CardContent className="p-6 space-y-5">
          <div>
            <Label>Test Name *</Label>
            <Input value={form.test_name} onChange={e => setForm({ ...form, test_name: e.target.value })} placeholder="JEE Main Physics Mock 1" data-testid="test-name-input" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label>Exam Type</Label>
              <Select value={form.exam_type} onValueChange={v => setForm({ ...form, exam_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="JEE_Main">JEE Main</SelectItem><SelectItem value="JEE_Advanced">JEE Advanced</SelectItem><SelectItem value="Practice">Practice</SelectItem></SelectContent>
              </Select></div>
            <div><Label>Subject</Label>
              <Select value={form.subject} onValueChange={v => setForm({ ...form, subject: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{SUBJECTS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
              </Select></div>
          </div>
          <div>
            <Label>Test Interface Pattern *</Label>
            <div className="grid grid-cols-2 gap-3 mt-2">
              {[
                { val: 'JEE_Main_Pattern', label: 'JEE Main Pattern', desc: 'Orange-themed NTA interface, subject tabs, question palette' },
                { val: 'JEE_Advanced_Pattern', label: 'JEE Advanced Pattern', desc: 'Blue-themed interface, section-wise tabs, advanced marking' },
              ].map(p => (
                <label key={p.val} className={`flex items-start gap-3 p-4 border-2 rounded-xl cursor-pointer transition-all ${form.test_pattern === p.val ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/40'}`}>
                  <input type="radio" name="pattern" checked={form.test_pattern === p.val} onChange={() => setForm({ ...form, test_pattern: p.val })} className="mt-1" />
                  <div><div className="font-semibold text-sm">{p.label}</div><div className="text-xs text-muted-foreground">{p.desc}</div></div>
                </label>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label>Duration (minutes)</Label><Input type="number" value={form.duration} onChange={e => setForm({ ...form, duration: parseInt(e.target.value) || 0 })} /></div>
            <div><Label>Schedule Date & Time</Label><Input type="datetime-local" value={form.scheduled_date_time} onChange={e => setForm({ ...form, scheduled_date_time: e.target.value })} data-testid="schedule-input" /></div>
          </div>
          <div>
            <Label>Assign to Batches *</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {batches.map(b => (
                <button key={b.id} type="button" onClick={() => toggleBatch(b.id)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${form.assigned_batches.includes(b.id) ? 'bg-primary text-primary-foreground border-primary' : 'bg-background border-border hover:border-primary/40'}`}>
                  {b.name}
                </button>
              ))}
            </div>
          </div>
          <div><Label>Instructions</Label><textarea value={form.instructions} onChange={e => setForm({ ...form, instructions: e.target.value })} rows={3} className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="Test instructions..." /></div>
          <Button onClick={handleCreateTest} disabled={loading} className="w-full" data-testid="create-test-submit">{loading ? 'Creating...' : 'Create Test & Add Questions'}</Button>
        </CardContent>
      </Card>
    </div>
  );

  // ADD QUESTIONS
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Add Questions ({questions.length} added)</h1>
        <div className="flex gap-2">
          {questions.length > 0 && <Button variant="outline" onClick={() => { setStep('list'); loadTests(); }}><Eye className="h-4 w-4 mr-2" />Save as Draft</Button>}
          {questions.length > 0 && <Button onClick={handlePublish}><Send className="h-4 w-4 mr-2" />Publish Test</Button>}
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle className="flex justify-between items-center">
          <span>Question {qForm.question_number}</span>
          <span className="text-sm font-normal px-3 py-1 bg-blue-50 text-blue-700 rounded-full">{qForm.question_type.replace(/_/g, ' ')}</span>
        </CardTitle></CardHeader>
        <CardContent className="space-y-5">
          {/* Question Type */}
          <div>
            <Label>Question Type</Label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
              {[
                { v: 'MCQ_Single', l: 'MCQ (Single)' }, { v: 'MCQ_Multiple', l: 'MCQ (Multiple)' },
                { v: 'Numerical_Integer', l: 'Numerical (Int)' }, { v: 'Numerical_Decimal', l: 'Numerical (Dec)' },
              ].map(t => (
                <button key={t.v} type="button" onClick={() => setQForm({ ...qForm, question_type: t.v, correct_answers: [], numerical_answer: '' })}
                  className={`px-3 py-2 rounded-lg text-sm border transition-all ${qForm.question_type === t.v ? 'bg-primary text-primary-foreground border-primary' : 'border-border hover:border-primary/40'}`}>
                  {t.l}
                </button>
              ))}
            </div>
          </div>

          {/* Question Text */}
          <div>
            <Label>Question Text * (supports LaTeX: $x^2$)</Label>
            <textarea value={qForm.question_text} onChange={e => setQForm({ ...qForm, question_text: e.target.value })} rows={4}
              className="w-full px-3 py-2 border rounded-lg text-sm mt-1" placeholder="Enter question text..." data-testid="question-text" />
          </div>

          {/* Question Image */}
          <div>
            <Label>Question Image (optional)</Label>
            <div className="flex items-center gap-3 mt-1">
              <label className="flex items-center gap-2 px-4 py-2 border-2 border-dashed rounded-lg cursor-pointer hover:border-primary/40">
                <input type="file" accept="image/*" className="sr-only" onChange={e => { if (e.target.files[0]) handleImageUpload(e.target.files[0], url => setQForm({ ...qForm, question_image_url: url })); }} />
                <Upload className="h-4 w-4" /><span className="text-sm">Upload Image</span>
              </label>
              {qForm.question_image_url && (
                <div className="relative">
                  <img src={`${process.env.REACT_APP_BACKEND_URL}${qForm.question_image_url}`} alt="Q" className="w-20 h-20 object-contain border rounded" />
                  <button onClick={() => setQForm({ ...qForm, question_image_url: '' })} className="absolute -top-1 -right-1 p-0.5 bg-red-500 text-white rounded-full"><X className="h-3 w-3" /></button>
                </div>
              )}
            </div>
          </div>

          {/* MCQ Options */}
          {qForm.question_type.startsWith('MCQ') && (
            <div className="space-y-3">
              <Label>Options * {qForm.question_type === 'MCQ_Multiple' && <span className="text-blue-600 text-xs ml-1">(select multiple correct)</span>}</Label>
              {['A', 'B', 'C', 'D'].map(opt => (
                <div key={opt} className={`flex items-start gap-3 p-3 rounded-xl border-2 transition-all ${qForm.correct_answers.includes(opt) ? 'border-green-500 bg-green-50' : 'border-border'}`}>
                  <input type={qForm.question_type === 'MCQ_Single' ? 'radio' : 'checkbox'} checked={qForm.correct_answers.includes(opt)}
                    onChange={() => toggleCorrectAnswer(opt)} className="mt-2 w-5 h-5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1"><span className="font-bold">{opt}.</span>{qForm.correct_answers.includes(opt) && <span className="text-xs text-green-600 font-medium">Correct</span>}</div>
                    <Input value={qForm.options[opt].text} onChange={e => setQForm({ ...qForm, options: { ...qForm.options, [opt]: { ...qForm.options[opt], text: e.target.value } } })} placeholder={`Option ${opt}`} />
                    <div className="flex items-center gap-2 mt-2">
                      <label className="flex items-center gap-1 px-2 py-1 border rounded text-xs cursor-pointer hover:bg-muted">
                        <input type="file" accept="image/*" className="sr-only" onChange={e => { if (e.target.files[0]) handleImageUpload(e.target.files[0], url => setQForm({ ...qForm, options: { ...qForm.options, [opt]: { ...qForm.options[opt], imageUrl: url } } })); }} />
                        <ImageIcon className="h-3 w-3" /> Add Image
                      </label>
                      {qForm.options[opt].imageUrl && <img src={`${process.env.REACT_APP_BACKEND_URL}${qForm.options[opt].imageUrl}`} alt={opt} className="w-16 h-16 object-contain border rounded" />}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Numerical Answer */}
          {qForm.question_type.startsWith('Numerical') && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-3">
              <div><Label>Numerical Answer * ({qForm.question_type === 'Numerical_Integer' ? 'Integer' : 'Decimal'})</Label>
                <Input type="number" step={qForm.question_type === 'Numerical_Decimal' ? '0.01' : '1'} value={qForm.numerical_answer}
                  onChange={e => setQForm({ ...qForm, numerical_answer: e.target.value })} placeholder="Correct answer" className="mt-1" /></div>
              <div><Label className="text-xs">Answer Range (optional, for JEE Advanced)</Label>
                <div className="grid grid-cols-2 gap-3 mt-1">
                  <Input type="number" step="0.01" value={qForm.answer_range.min} onChange={e => setQForm({ ...qForm, answer_range: { ...qForm.answer_range, min: e.target.value } })} placeholder="Min" />
                  <Input type="number" step="0.01" value={qForm.answer_range.max} onChange={e => setQForm({ ...qForm, answer_range: { ...qForm.answer_range, max: e.target.value } })} placeholder="Max" />
                </div></div>
            </div>
          )}

          {/* Marking & Metadata */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div><Label>Marks</Label><Input type="number" value={qForm.marks} onChange={e => setQForm({ ...qForm, marks: parseInt(e.target.value) || 0 })} /></div>
            <div><Label>Negative Marks</Label><Input type="number" value={qForm.negative_marks} onChange={e => setQForm({ ...qForm, negative_marks: parseInt(e.target.value) || 0 })} /></div>
            <div><Label>Subject</Label>
              <Select value={qForm.subject} onValueChange={v => setQForm({ ...qForm, subject: v })}>
                <SelectTrigger><SelectValue placeholder="Subject" /></SelectTrigger>
                <SelectContent>{['Physics', 'Chemistry', 'Mathematics'].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
              </Select></div>
            <div><Label>Difficulty</Label>
              <Select value={qForm.difficulty} onValueChange={v => setQForm({ ...qForm, difficulty: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{DIFFICULTIES.map(d => <SelectItem key={d} value={d}>{d}</SelectItem>)}</SelectContent>
              </Select></div>
          </div>
          <div><Label>Chapter</Label><Input value={qForm.chapter} onChange={e => setQForm({ ...qForm, chapter: e.target.value })} placeholder="e.g. Kinematics" /></div>
          <div><Label>Teacher Note (shown after submission for incorrect answers)</Label>
            <textarea value={qForm.teacher_note} onChange={e => setQForm({ ...qForm, teacher_note: e.target.value })} rows={2} className="w-full px-3 py-2 border rounded-lg text-sm mt-1" placeholder="Solution approach, tips..." /></div>

          <div className="flex gap-3 pt-4 border-t">
            <Button onClick={handleAddQuestion} disabled={loading} className="flex-1" data-testid="add-question-btn">
              <Plus className="h-4 w-4 mr-2" />{loading ? 'Adding...' : 'Add Question & Continue'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Added Questions List */}
      {questions.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Added Questions ({questions.length})</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {questions.map((q, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div>
                    <span className="font-semibold text-sm">Q{q.question_number}.</span>
                    <span className="text-sm ml-2">{q.question_text.substring(0, 80)}{q.question_text.length > 80 ? '...' : ''}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{q.question_type.replace(/_/g, ' ')}</span>
                    <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">{q.subject}</span>
                    <span className="text-xs font-medium">+{q.marks} / {q.negative_marks}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CreateTest;
