import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import {
  Plus, ChevronLeft, Send, BarChart3,
  Library, Loader2, Check, FolderTree,
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';
import BatchManagerDialog from '../../components/BatchManagerDialog';
import { QBFolderMultiTree } from '../../components/QBFolderTree';

const SUBJECTS = ['Physics', 'Chemistry', 'Mathematics', 'Biology', 'All Subjects'];
const NAVY = '#1B3A52';

/* -------- Folder tree (multi-select for bank picker) -------- */
/* Moved into /app/frontend/src/components/QBFolderTree.js — the craco
   visual-edits babel plugin barfed on self-referencing JSX in this file. */

function BankPicker({ folders, selectedFolderIds, setSelectedFolderIds }) {
  const [expanded, setExpanded] = useState(() => new Set(folders.map((r) => r.id)));
  // When folders list changes (reloaded), auto-expand roots
  useEffect(() => {
    setExpanded((p) => {
      const n = new Set(p);
      folders.forEach((r) => n.add(r.id));
      return n;
    });
  }, [folders]);
  const toggleExpanded = (id) => setExpanded((p) => {
    const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n;
  });
  const toggleSel = (id) => setSelectedFolderIds((p) =>
    p.includes(id) ? p.filter((x) => x !== id) : [...p, id]);
  return (
    <div className="max-h-[65vh] overflow-y-auto">
      <QBFolderMultiTree
        roots={folders}
        selectedIds={selectedFolderIds}
        toggleSel={toggleSel}
        expanded={expanded}
        toggleExpanded={toggleExpanded}
      />
    </div>
  );
}

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

  // Bank picker state (fixed folders)
  const [folders, setFolders] = useState([]);
  const [selectedFolderIds, setSelectedFolderIds] = useState([]);
  const [bankAvailable, setBankAvailable] = useState([]);
  const [bankHiddenCount, setBankHiddenCount] = useState(0);
  const [bankTotalBefore, setBankTotalBefore] = useState(0);
  const [bankSelected, setBankSelected] = useState(new Set());
  const [bankLoading, setBankLoading] = useState(false);

  useEffect(() => { setPageTitle('Create Test'); loadTests(); loadBatches(); }, []);

  const loadTests = async () => {
    try { const { data } = await api.get('/teacher/tests/my-tests'); setTests(data.tests || []); }
    catch { try { const { data } = await api.get('/teacher/tests/'); setTests(data.tests || []); } catch {} }
  };
  const loadBatches = async () => {
    try { const { data } = await api.get('/batches/'); setBatches(data.batches || []); } catch {}
  };
  const loadFolders = async () => {
    try { const { data } = await api.get('/teacher/qb/folders'); setFolders(data.folders || []); }
    catch { toast.error('Failed to load question bank folders'); }
  };

  const goToBankStep = async () => {
    if (!form.test_name || !form.scheduled_date_time || form.assigned_batches.length === 0) {
      toast.error('Fill all required fields'); return;
    }
    await loadFolders();
    setStep('bank');
  };

  const loadBankAvailable = async () => {
    if (selectedFolderIds.length === 0 || form.assigned_batches.length === 0) {
      setBankAvailable([]); setBankHiddenCount(0); setBankTotalBefore(0);
      return;
    }
    setBankLoading(true);
    try {
      const params = new URLSearchParams();
      selectedFolderIds.forEach((id) => params.append('folder_ids', id));
      form.assigned_batches.forEach((b) => params.append('batch_codes', b));
      const { data } = await api.get(`/teacher/question-bank/available?${params}`);
      setBankAvailable(data.questions || []);
      setBankHiddenCount(data.hidden_count || 0);
      setBankTotalBefore(data.total_before_exclusion || 0);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load bank questions');
    } finally { setBankLoading(false); }
  };

  useEffect(() => {
    if (step === 'bank') loadBankAvailable();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFolderIds, form.assigned_batches, step]);

  const toggleBankSelected = (id) => setBankSelected((p) => {
    const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n;
  });
  const selectAllVisible = () => setBankSelected(new Set(bankAvailable.map((q) => q.id)));
  const clearBankSelection = () => setBankSelected(new Set());

  const bankQuestionToTestQuestion = (q, num) => ({
    question_number: num,
    question_text: q.question_text || '',
    question_image_url: q.question_image_url || '',
    question_type: q.question_type,
    options: q.options || { A: { text: '' }, B: { text: '' }, C: { text: '' }, D: { text: '' } },
    correct_answers: q.correct_answers || [],
    numerical_answer: q.numerical_answer,
    answer_range: q.answer_range || null,
    marks: q.marks || 4,
    negative_marks: q.negative_marks || -1,
    subject: form.subject === 'All Subjects' ? '' : form.subject,
    chapter: '', difficulty: q.difficulty || 'Moderate',
    teacher_note: q.teacher_note || '',
    solution_youtube_url: q.solution_youtube_url || '',
    solution_media_url: q.solution_media_url || '',
    solution_media_type: q.solution_media_type || '',
    from_question_bank_id: q.id,
  });

  const submitWithBankQuestions = async () => {
    const picks = bankAvailable.filter((q) => bankSelected.has(q.id));
    if (picks.length === 0) { toast.error('Select at least one question from the bank'); return; }
    setLoading(true);
    try {
      const testQuestions = picks.map((q, i) => bankQuestionToTestQuestion(q, i + 1));
      const { data } = await api.post('/teacher/tests/create', {
        ...form,
        questions: testQuestions,
        total_questions: testQuestions.length,
        total_marks: testQuestions.reduce((s, q) => s + (q.marks || 0), 0),
        status: 'scheduled',
      });
      const testId = data.test.test_id;
      try {
        await api.post('/teacher/question-bank/record-assignments', {
          test_id: testId,
          question_ids: picks.map((q) => q.id),
          batch_codes: form.assigned_batches,
        });
      } catch { /* non-fatal */ }
      toast.success(`Test created with ${picks.length} question(s) from the bank`);
      resetBankPickerState();
      setStep('list'); loadTests();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create test');
    } finally { setLoading(false); }
  };

  const resetBankPickerState = () => {
    setSelectedFolderIds([]); setBankAvailable([]);
    setBankHiddenCount(0); setBankTotalBefore(0); setBankSelected(new Set());
  };

  const toggleBatch = (batchId) => {
    setForm((f) => ({
      ...f, assigned_batches: f.assigned_batches.includes(batchId)
        ? f.assigned_batches.filter((b) => b !== batchId) : [...f.assigned_batches, batchId],
    }));
  };

  // LIST
  if (step === 'list') return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Tests</h1>
        <Button onClick={() => setStep('config')} data-testid="create-test-btn">
          <Plus className="h-4 w-4 mr-2" />Create Test
        </Button>
      </div>
      {tests.length === 0 ? (
        <p className="text-muted-foreground text-center py-12">No tests yet.</p>
      ) : (
        <div className="grid gap-4">
          {tests.map((t) => (
            <Card key={t.test_id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex justify-between items-center">
                <div>
                  <h3 className="font-semibold">{t.test_name}</h3>
                  <p className="text-sm text-muted-foreground">{t.exam_type} | {t.subject} | {t.total_questions || 0} Qs | {t.duration}min</p>
                  <p className="text-xs text-muted-foreground">Batches: {(t.assigned_batches || []).join(', ')}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs rounded ${t.status === 'scheduled' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{t.status}</span>
                  <Button size="sm" variant="outline" data-testid={`view-results-${t.test_id}`} onClick={() => navigate(`/teacher/tests/${t.test_id}/results`)}>
                    <BarChart3 className="h-3.5 w-3.5 mr-1" /> Results
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  // CONFIG
  if (step === 'config') return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" onClick={() => setStep('list')}><ChevronLeft className="h-4 w-4" /></Button>
        <h1 className="text-2xl font-bold">Test Configuration</h1>
      </div>
      <Card>
        <CardContent className="p-6 space-y-5">
          <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800">
            <b>Note:</b> Every test must now be built from the central Question Bank.
            Add questions in the Question Bank first, then compose tests here.
          </div>
          <div>
            <Label>Test Name *</Label>
            <Input value={form.test_name} onChange={(e) => setForm({ ...form, test_name: e.target.value })} placeholder="JEE Main Physics Mock 1" data-testid="test-name-input" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Exam Type</Label>
              <Select value={form.exam_type} onValueChange={(v) => setForm({ ...form, exam_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="JEE_Main">JEE Main</SelectItem>
                  <SelectItem value="JEE_Advanced">JEE Advanced</SelectItem>
                  <SelectItem value="NEET">NEET</SelectItem>
                  <SelectItem value="Practice">Practice</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Subject</Label>
              <Select value={form.subject} onValueChange={(v) => setForm({ ...form, subject: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label>Test Interface Pattern *</Label>
            <div className="grid grid-cols-2 gap-3 mt-2">
              {[
                { val: 'JEE_Main_Pattern', label: 'JEE Main Pattern', desc: 'Orange NTA UI, subject tabs, palette' },
                { val: 'JEE_Advanced_Pattern', label: 'JEE Advanced Pattern', desc: 'Blue section-wise UI, advanced marking' },
              ].map((p) => (
                <label key={p.val} className={`flex items-start gap-3 p-4 border-2 rounded-xl cursor-pointer transition-all ${form.test_pattern === p.val ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/40'}`}>
                  <input type="radio" name="pattern" checked={form.test_pattern === p.val} onChange={() => setForm({ ...form, test_pattern: p.val })} className="mt-1" />
                  <div><div className="font-semibold text-sm">{p.label}</div><div className="text-xs text-muted-foreground">{p.desc}</div></div>
                </label>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label>Duration (minutes)</Label><Input type="number" value={form.duration} onChange={(e) => setForm({ ...form, duration: parseInt(e.target.value, 10) || 0 })} /></div>
            <div><Label>Schedule Date & Time</Label><Input type="datetime-local" value={form.scheduled_date_time} onChange={(e) => setForm({ ...form, scheduled_date_time: e.target.value })} data-testid="schedule-input" /></div>
          </div>
          <div>
            <div className="flex items-center justify-between">
              <Label>Assign to Batches *</Label>
              <BatchManagerDialog batches={batches} onBatchesChanged={loadBatches} />
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {batches.map((b) => (
                <button key={b.id} type="button" onClick={() => toggleBatch(b.id)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${form.assigned_batches.includes(b.id) ? 'bg-primary text-primary-foreground border-primary' : 'bg-background border-border hover:border-primary/40'}`}>
                  {b.name}
                </button>
              ))}
            </div>
          </div>
          <div><Label>Instructions</Label><textarea value={form.instructions} onChange={(e) => setForm({ ...form, instructions: e.target.value })} rows={3} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
          <Button onClick={goToBankStep} disabled={loading} className="w-full" data-testid="create-test-submit">
            {loading ? 'Loading…' : 'Next: Pick Questions from Bank →'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  // BANK PICKER
  return (
    <div className="max-w-6xl mx-auto space-y-6" data-testid="test-bank-step">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={() => setStep('config')}><ChevronLeft className="h-4 w-4" /></Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2" style={{ color: NAVY }}>
              <Library className="h-6 w-6" /> Build Test from Question Bank
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Test: <b>{form.test_name}</b> · Batches: <b>{form.assigned_batches.join(', ')}</b>
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        <Card className="border-slate-200 h-fit lg:sticky lg:top-4">
          <CardContent className="p-3">
            <div className="text-xs uppercase font-semibold text-slate-500 mb-2 px-2">Pick folders *</div>
            {folders.length === 0
              ? <div className="p-3 text-sm text-slate-400 italic">No folders available yet.</div>
              : <BankPicker folders={folders} selectedFolderIds={selectedFolderIds} setSelectedFolderIds={setSelectedFolderIds} />}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {selectedFolderIds.length === 0 ? (
            <Card className="border-dashed border-2 border-slate-200">
              <CardContent className="py-16 flex flex-col items-center text-center gap-3">
                <FolderTree className="h-10 w-10 text-slate-300" />
                <h3 className="text-base font-semibold text-slate-700">Select one or more leaf folders</h3>
                <p className="text-sm text-slate-500 max-w-sm">
                  Questions already assigned to the selected batch{form.assigned_batches.length === 1 ? '' : 'es'} are hidden automatically.
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-slate-200">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between flex-wrap gap-3">
                  <span className="text-base">
                    {bankLoading
                      ? <span className="flex items-center gap-2 text-slate-500 text-sm"><Loader2 className="h-4 w-4 animate-spin" /> Loading…</span>
                      : (
                        <>
                          <b>{bankAvailable.length}</b> available for {form.assigned_batches.join(', ')}
                          {bankHiddenCount > 0 && (
                            <span className="ml-2 text-xs font-normal text-slate-500">
                              ({bankHiddenCount} already used, hidden)
                            </span>
                          )}
                        </>
                      )}
                  </span>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={selectAllVisible} disabled={bankAvailable.length === 0} data-testid="bank-select-all">
                      Select All Visible
                    </Button>
                    <Button size="sm" variant="ghost" onClick={clearBankSelection} disabled={bankSelected.size === 0}>Clear</Button>
                    <span className="text-xs text-slate-500">{bankSelected.size} selected</span>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {bankAvailable.length === 0 && !bankLoading && (
                  <div className="text-sm text-slate-400 italic py-4 text-center">
                    {bankTotalBefore === 0
                      ? 'No questions in these folders yet.'
                      : 'Every matching question has already been used for the selected batch(es).'}
                  </div>
                )}
                {bankAvailable.map((q) => {
                  const selected = bankSelected.has(q.id);
                  const multi = form.assigned_batches.length > 1;
                  return (
                    <button key={q.id} type="button" onClick={() => toggleBankSelected(q.id)}
                      className={`w-full text-left flex items-start gap-3 p-3 rounded-lg border-2 transition-all ${selected ? 'border-emerald-500 bg-emerald-50/40' : 'border-slate-200 hover:border-[#1B3A52]/40'}`}
                      data-testid={`bank-q-${q.id}`}
                    >
                      <div className={`mt-0.5 h-5 w-5 rounded flex items-center justify-center border-2 ${selected ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-300'}`}>
                        {selected && <Check className="h-3 w-3" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-slate-800">
                          {(q.question_text || '(image only)').slice(0, 140)}{q.question_text?.length > 140 ? '…' : ''}
                        </div>
                        <div className="flex flex-wrap items-center gap-1.5 mt-1">
                          <span className="text-[10px] bg-[#1B3A52]/10 text-[#1B3A52] rounded px-1.5 py-0.5 font-semibold">
                            {q.question_type.replace(/_/g, ' ')}
                          </span>
                          {q.difficulty && <span className="text-[10px] bg-amber-100 text-amber-700 rounded px-1.5 py-0.5">{q.difficulty}</span>}
                          <span className="text-[10px] text-slate-400">+{q.marks} / {q.negative_marks}</span>
                          {multi && q.fresh_for?.length > 0 && (
                            <span className="text-[10px] bg-emerald-100 text-emerald-700 rounded px-1.5 py-0.5">
                              Fresh: {q.fresh_for.join(', ')}
                            </span>
                          )}
                          {multi && q.used_for?.length > 0 && (
                            <span className="text-[10px] bg-slate-200 text-slate-600 rounded px-1.5 py-0.5">
                              Used: {q.used_for.join(', ')}
                            </span>
                          )}
                        </div>
                      </div>
                      {q.question_image_url && (
                        <img src={q.question_image_url} alt="q" className="w-12 h-12 rounded object-cover border border-slate-200" />
                      )}
                    </button>
                  );
                })}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-3 sticky bottom-4 bg-white/80 backdrop-blur border rounded-lg p-3 shadow">
        <Button variant="ghost" onClick={() => setStep('config')}>Back</Button>
        <Button onClick={submitWithBankQuestions} disabled={loading || bankSelected.size === 0}
          className="bg-[#1B3A52] hover:bg-[#2B4A62] text-white" data-testid="bank-create-test">
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
          Create Test with {bankSelected.size || ''} Question{bankSelected.size === 1 ? '' : 's'}
        </Button>
      </div>
    </div>
  );
};

export default CreateTest;
