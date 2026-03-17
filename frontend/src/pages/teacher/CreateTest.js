import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Checkbox } from '../../components/ui/checkbox';
import { Switch } from '../../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Plus, Trash2, FileEdit, ChevronRight, ChevronLeft, Eye, Send } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../utils/api';

const EXAM_TYPES = ['JEE_Main', 'JEE_Advanced', 'Practice'];
const SUBJECTS = ['Physics', 'Chemistry', 'Mathematics', 'All Subjects'];
const TEST_TYPES = ['Full Length', 'Chapter Test', 'Topic Test', 'Mock Test', 'Practice Test'];
const DIFFICULTIES = ['Easy', 'Medium', 'Hard'];

const CreateTest = () => {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [step, setStep] = useState(1);
  const [batches, setBatches] = useState([]);
  const [form, setForm] = useState({
    test_name: '', exam_type: 'JEE_Main', subject: 'Physics', test_type: 'Chapter Test',
    chapters: '', topics: '',
    scheduled_date_time: '', duration: '60', instructions: '',
    allow_reattempts: false, max_attempts: '1',
    show_solutions_after_submit: true, show_results_immediately: true, randomize_questions: false,
    assigned_batches: [],
  });
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState({
    question_text: '', question_image_url: '', options: { A: '', B: '', C: '', D: '' },
    correct_answer: 'A', marks: '4', negative_marks: '-1',
    subject: '', chapter: '', topic: '', difficulty: 'Medium', teacher_note: '',
  });
  const [editingIdx, setEditingIdx] = useState(-1);

  useEffect(() => {
    loadTests();
    loadBatches();
  }, []);

  const loadTests = async () => {
    try {
      const res = await api.get('/teacher/tests/');
      setTests(res.data.tests || []);
    } catch { }
    finally { setLoading(false); }
  };

  const loadBatches = async () => {
    try {
      const res = await api.get('/batches/');
      setBatches(res.data.batches || []);
    } catch { }
  };

  const handleBatchToggle = (batchId) => {
    setForm((prev) => ({
      ...prev,
      assigned_batches: prev.assigned_batches.includes(batchId)
        ? prev.assigned_batches.filter((b) => b !== batchId)
        : [...prev.assigned_batches, batchId],
    }));
  };

  const addQuestion = () => {
    if (!currentQ.question_text || !currentQ.options.A || !currentQ.options.B || !currentQ.options.C || !currentQ.options.D) {
      toast.error('Fill question text and all 4 options');
      return;
    }
    if (editingIdx >= 0) {
      const updated = [...questions];
      updated[editingIdx] = { ...currentQ, question_number: editingIdx + 1 };
      setQuestions(updated);
      setEditingIdx(-1);
    } else {
      setQuestions([...questions, { ...currentQ, question_number: questions.length + 1 }]);
    }
    setCurrentQ({ question_text: '', question_image_url: '', options: { A: '', B: '', C: '', D: '' }, correct_answer: 'A', marks: '4', negative_marks: '-1', subject: '', chapter: '', topic: '', difficulty: 'Medium', teacher_note: '' });
    toast.success(editingIdx >= 0 ? 'Question updated' : 'Question added');
  };

  const editQuestion = (idx) => {
    setCurrentQ(questions[idx]);
    setEditingIdx(idx);
  };

  const deleteQuestion = (idx) => {
    setQuestions(questions.filter((_, i) => i !== idx).map((q, i) => ({ ...q, question_number: i + 1 })));
    if (editingIdx === idx) { setEditingIdx(-1); setCurrentQ({ question_text: '', question_image_url: '', options: { A: '', B: '', C: '', D: '' }, correct_answer: 'A', marks: '4', negative_marks: '-1', subject: '', chapter: '', topic: '', difficulty: 'Medium', teacher_note: '' }); }
  };

  const handlePublish = async (isDraft = false) => {
    if (!form.test_name || !form.scheduled_date_time || !form.duration || form.assigned_batches.length === 0) {
      toast.error('Fill test details and select batches');
      return;
    }
    if (!isDraft && questions.length === 0) {
      toast.error('Add at least one question to publish');
      return;
    }
    try {
      const payload = {
        ...form,
        chapters: form.chapters ? form.chapters.split(',').map((c) => c.trim()) : [],
        topics: form.topics ? form.topics.split(',').map((t) => t.trim()) : [],
        questions: questions.map((q) => ({ ...q, marks: Number(q.marks), negative_marks: Number(q.negative_marks) })),
      };
      if (isDraft) payload.questions = [];
      const res = await api.post('/teacher/tests/create', payload);
      toast.success(res.data.message);
      setShowCreate(false);
      resetForm();
      loadTests();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create test');
    }
  };

  const handlePublishExisting = async (testId) => {
    try {
      const res = await api.put(`/teacher/tests/${testId}/publish`);
      toast.success(res.data.message);
      loadTests();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to publish');
    }
  };

  const handleDeleteTest = async (testId) => {
    if (!window.confirm('Delete this test?')) return;
    try {
      await api.delete(`/teacher/tests/${testId}`);
      toast.success('Test deleted');
      loadTests();
    } catch { toast.error('Failed to delete'); }
  };

  const resetForm = () => {
    setForm({ test_name: '', exam_type: 'JEE_Main', subject: 'Physics', test_type: 'Chapter Test', chapters: '', topics: '', scheduled_date_time: '', duration: '60', instructions: '', allow_reattempts: false, max_attempts: '1', show_solutions_after_submit: true, show_results_immediately: true, randomize_questions: false, assigned_batches: [] });
    setQuestions([]);
    setCurrentQ({ question_text: '', question_image_url: '', options: { A: '', B: '', C: '', D: '' }, correct_answer: 'A', marks: '4', negative_marks: '-1', subject: '', chapter: '', topic: '', difficulty: 'Medium', teacher_note: '' });
    setStep(1);
    setEditingIdx(-1);
  };

  const statusColors = { draft: 'bg-amber-100 text-amber-700', scheduled: 'bg-blue-100 text-blue-700', completed: 'bg-green-100 text-green-700' };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6" data-testid="create-test-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Create & Manage Tests</h1>
          <p className="text-slate-500 text-sm mt-1">Design, add questions, and publish tests</p>
        </div>
        <Button className="bg-indigo-600 hover:bg-indigo-700" onClick={() => { resetForm(); setShowCreate(true); }} data-testid="create-test-btn">
          <Plus className="h-4 w-4 mr-2" /> Create New Test
        </Button>
      </div>

      {/* Create Test Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Test — Step {step} of 3</DialogTitle>
          </DialogHeader>

          {step === 1 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Test Name *</Label>
                <Input value={form.test_name} onChange={(e) => setForm({ ...form, test_name: e.target.value })} placeholder="e.g. JEE Main Mock Test 1" data-testid="test-name-input" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Exam Type</Label>
                  <Select value={form.exam_type} onValueChange={(v) => setForm({ ...form, exam_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{EXAM_TYPES.map((e) => <SelectItem key={e} value={e}>{e.replace('_', ' ')}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Subject</Label>
                  <Select value={form.subject} onValueChange={(v) => setForm({ ...form, subject: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Test Type</Label>
                  <Select value={form.test_type} onValueChange={(v) => setForm({ ...form, test_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{TEST_TYPES.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Duration (minutes) *</Label>
                  <Input type="number" value={form.duration} onChange={(e) => setForm({ ...form, duration: e.target.value })} data-testid="test-duration-input" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Scheduled Date & Time *</Label>
                <Input type="datetime-local" value={form.scheduled_date_time} onChange={(e) => setForm({ ...form, scheduled_date_time: e.target.value })} data-testid="test-datetime-input" />
              </div>
              <div className="space-y-2">
                <Label>Instructions</Label>
                <textarea className="w-full border rounded-lg p-2 text-sm min-h-[60px] resize-none" value={form.instructions} onChange={(e) => setForm({ ...form, instructions: e.target.value })} placeholder="Test instructions..." />
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Allow Reattempts</Label>
                  <Switch checked={form.allow_reattempts} onCheckedChange={(v) => setForm({ ...form, allow_reattempts: v })} />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Show Solutions After Submit</Label>
                  <Switch checked={form.show_solutions_after_submit} onCheckedChange={(v) => setForm({ ...form, show_solutions_after_submit: v })} />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Randomize Questions</Label>
                  <Switch checked={form.randomize_questions} onCheckedChange={(v) => setForm({ ...form, randomize_questions: v })} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Assign to Batches *</Label>
                <div className="grid grid-cols-2 gap-2 p-3 border rounded-lg bg-slate-50">
                  {batches.map((b) => (
                    <label key={b.id} className="flex items-center space-x-2 cursor-pointer">
                      <Checkbox checked={form.assigned_batches.includes(b.id)} onCheckedChange={() => handleBatchToggle(b.id)} />
                      <span className="text-sm">{b.name}</span>
                    </label>
                  ))}
                </div>
              </div>
              <Button className="w-full bg-indigo-600 hover:bg-indigo-700" onClick={() => setStep(2)}>
                Next: Add Questions <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              {/* Questions list */}
              {questions.length > 0 && (
                <div className="border rounded-lg divide-y max-h-40 overflow-y-auto bg-slate-50">
                  {questions.map((q, i) => (
                    <div key={i} className="flex items-center justify-between px-3 py-2 text-sm">
                      <span className="truncate flex-1">Q{q.question_number}: {q.question_text.substring(0, 50)}...</span>
                      <div className="flex items-center space-x-1 ml-2">
                        <Button variant="ghost" size="sm" onClick={() => editQuestion(i)}><Edit className="h-3 w-3" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => deleteQuestion(i)}><Trash2 className="h-3 w-3 text-red-500" /></Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div className="text-sm font-medium text-slate-700">
                {editingIdx >= 0 ? `Editing Q${editingIdx + 1}` : `Add Q${questions.length + 1}`}
              </div>

              <div className="space-y-2">
                <Label>Question Text *</Label>
                <textarea className="w-full border rounded-lg p-2 text-sm min-h-[80px]" value={currentQ.question_text} onChange={(e) => setCurrentQ({ ...currentQ, question_text: e.target.value })} placeholder="Enter question..." data-testid="question-text-input" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                {['A', 'B', 'C', 'D'].map((opt) => (
                  <div key={opt} className="space-y-1">
                    <Label>Option {opt} *</Label>
                    <Input value={currentQ.options[opt]} onChange={(e) => setCurrentQ({ ...currentQ, options: { ...currentQ.options, [opt]: e.target.value } })} placeholder={`Option ${opt}`} data-testid={`option-${opt}-input`} />
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label>Correct Answer *</Label>
                  <Select value={currentQ.correct_answer} onValueChange={(v) => setCurrentQ({ ...currentQ, correct_answer: v })}>
                    <SelectTrigger data-testid="correct-answer-select"><SelectValue /></SelectTrigger>
                    <SelectContent>{['A', 'B', 'C', 'D'].map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label>Marks</Label>
                  <Input type="number" value={currentQ.marks} onChange={(e) => setCurrentQ({ ...currentQ, marks: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label>Negative Marks</Label>
                  <Input type="number" value={currentQ.negative_marks} onChange={(e) => setCurrentQ({ ...currentQ, negative_marks: e.target.value })} />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label>Subject</Label>
                  <Input value={currentQ.subject} onChange={(e) => setCurrentQ({ ...currentQ, subject: e.target.value })} placeholder="Physics" />
                </div>
                <div className="space-y-1">
                  <Label>Chapter</Label>
                  <Input value={currentQ.chapter} onChange={(e) => setCurrentQ({ ...currentQ, chapter: e.target.value })} placeholder="Kinematics" />
                </div>
                <div className="space-y-1">
                  <Label>Difficulty</Label>
                  <Select value={currentQ.difficulty} onValueChange={(v) => setCurrentQ({ ...currentQ, difficulty: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{DIFFICULTIES.map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-1">
                <Label>Teacher's Note (shown only after submission for incorrect/unattempted)</Label>
                <textarea className="w-full border rounded-lg p-2 text-sm min-h-[60px]" value={currentQ.teacher_note} onChange={(e) => setCurrentQ({ ...currentQ, teacher_note: e.target.value })} placeholder="Explain the correct answer, common mistakes, tips..." data-testid="teacher-note-input" />
              </div>
              <div className="flex gap-2">
                <Button className="flex-1 bg-emerald-600 hover:bg-emerald-700" onClick={addQuestion} data-testid="save-question-btn">
                  {editingIdx >= 0 ? 'Update Question' : 'Save & Add Next'}
                </Button>
              </div>
              <div className="flex justify-between pt-2">
                <Button variant="outline" onClick={() => setStep(1)}>
                  <ChevronLeft className="h-4 w-4 mr-1" /> Back
                </Button>
                <Button className="bg-indigo-600 hover:bg-indigo-700" onClick={() => setStep(3)}>
                  Preview & Publish <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <Card className="border shadow-sm">
                <CardContent className="p-4 space-y-3">
                  <h3 className="font-semibold text-lg">{form.test_name || 'Untitled Test'}</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm text-slate-600">
                    <span>Exam: {form.exam_type.replace('_', ' ')}</span>
                    <span>Subject: {form.subject}</span>
                    <span>Type: {form.test_type}</span>
                    <span>Duration: {form.duration} min</span>
                    <span>Questions: {questions.length}</span>
                    <span>Total Marks: {questions.reduce((s, q) => s + Number(q.marks), 0)}</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {form.assigned_batches.map((b) => (
                      <span key={b} className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{b}</span>
                    ))}
                  </div>
                </CardContent>
              </Card>
              {questions.length > 0 && (
                <div className="border rounded-lg divide-y max-h-60 overflow-y-auto">
                  {questions.map((q, i) => (
                    <div key={i} className="px-4 py-3">
                      <p className="text-sm font-medium">Q{q.question_number}: {q.question_text}</p>
                      <div className="grid grid-cols-2 gap-1 mt-1 text-xs text-slate-500">
                        {Object.entries(q.options).map(([k, v]) => (
                          <span key={k} className={k === q.correct_answer ? 'text-green-600 font-medium' : ''}>
                            {k}) {v}
                          </span>
                        ))}
                      </div>
                      {q.teacher_note && <p className="text-xs text-amber-600 mt-1">Note: {q.teacher_note.substring(0, 60)}...</p>}
                    </div>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                  <ChevronLeft className="h-4 w-4 mr-1" /> Edit Questions
                </Button>
                <Button variant="outline" className="flex-1" onClick={() => handlePublish(true)}>
                  Save as Draft
                </Button>
                <Button className="flex-1 bg-indigo-600 hover:bg-indigo-700" onClick={() => handlePublish(false)} data-testid="publish-test-btn">
                  <Send className="h-4 w-4 mr-1" /> Publish Test
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Tests List */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading tests...</div>
      ) : tests.length === 0 ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="py-12 text-center">
            <FileEdit className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No tests created yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {tests.map((test) => (
            <Card key={test.test_id} className="border-0 shadow-sm hover:shadow-md transition-shadow" data-testid={`test-card-${test.test_id}`}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-slate-900">{test.test_name}</h3>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusColors[test.status] || 'bg-slate-100 text-slate-600'}`}>
                        {test.status}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                      <span>{test.subject}</span>
                      <span>{test.test_type}</span>
                      <span>{test.total_questions || 0} questions</span>
                      <span>{test.duration} min</span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(test.assigned_batches || []).map((b) => (
                        <span key={b} className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{b}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {test.status === 'draft' && (
                      <Button variant="outline" size="sm" onClick={() => handlePublishExisting(test.test_id)}>
                        <Send className="h-3.5 w-3.5 mr-1" /> Publish
                      </Button>
                    )}
                    <Button variant="outline" size="sm" onClick={() => handleDeleteTest(test.test_id)}>
                      <Trash2 className="h-3.5 w-3.5 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default CreateTest;
