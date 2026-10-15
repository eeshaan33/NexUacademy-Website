import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  ChevronLeft, Upload, Image as ImageIcon, X, Check, Loader2, Youtube, Film,
} from 'lucide-react';
import api from '../../../utils/api';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Card, CardContent } from '../../../components/ui/card';
import { setPageTitle } from '../../../utils/pageTitle';
import { QBFolderTree } from '../../../components/QBFolderTree';

const NAVY = '#1B3A52';
const DIFFICULTIES = ['Easy', 'Moderate', 'Difficult'];
const MAX_TOTAL_BYTES = 15 * 1024 * 1024; // 15 MB
const MB = (n) => `${(n / (1024 * 1024)).toFixed(2)} MB`;

const emptyQuestion = () => ({
  question_text: '',
  question_type: 'MCQ_Single',
  options: { A: { text: '' }, B: { text: '' }, C: { text: '' }, D: { text: '' } },
  correct_answers: [],
  numerical_answer: '',
  answer_range: { min: '', max: '' },
  difficulty: 'Moderate',
  marks: 4,
  negative_marks: -1,
  teacher_note: '',
  solution_youtube_url: '',
});

/* ------------------------- Folder tree picker ------------------------- */
/* (recursive JSX moved into components/QBFolderTree.js — the craco
   visual-edits babel plugin barfed on self-referencing JSX in this file.) */

/* --------------------------- Image drop zone --------------------------- */
function ImageDrop({ file, onFile, onClear, label, testId }) {
  const [drag, setDrag] = useState(false);
  const validate = (f) => {
    if (!f) return;
    if (!f.type.startsWith('image/')) { toast.error('Only images allowed'); return; }
    onFile(f);
  };
  if (file) {
    return (
      <div className="relative inline-block">
        <img src={URL.createObjectURL(file)} alt="preview" className="max-h-40 rounded-lg border border-slate-200 object-contain bg-slate-50" />
        <div className="absolute bottom-1 left-1 text-[10px] bg-black/60 text-white rounded px-1.5 py-0.5">{MB(f.size || file.size || 0)}</div>
        <button type="button" onClick={onClear} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow" data-testid={`${testId}-remove`}>
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }
  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); validate(e.dataTransfer.files?.[0]); }}
      className={`flex flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed py-4 px-3 cursor-pointer transition-colors ${drag ? 'border-[#1B3A52] bg-[#1B3A52]/5' : 'border-slate-300 hover:border-[#1B3A52]/60 hover:bg-slate-50'}`}
      data-testid={testId}
    >
      <Upload className="h-5 w-5 text-slate-400" />
      <span className="text-xs text-slate-500 text-center">{label}</span>
      <input type="file" accept="image/png,image/jpeg,image/jpg" className="sr-only" onChange={(e) => validate(e.target.files?.[0])} />
    </label>
  );
}

/* --------------------- Image OR Video drop zone --------------------- */
function MediaDrop({ file, onFile, onClear, testId }) {
  const [drag, setDrag] = useState(false);
  const validate = (f) => {
    if (!f) return;
    const isImage = f.type.startsWith('image/');
    const isVideo = f.type.startsWith('video/');
    if (!isImage && !isVideo) { toast.error('Only image or video allowed'); return; }
    const limit = isVideo ? 25 * 1024 * 1024 : 15 * 1024 * 1024;
    if (f.size > limit) { toast.error(`File exceeds ${limit / (1024 * 1024)} MB`); return; }
    onFile(f);
  };
  if (file) {
    const url = URL.createObjectURL(file);
    const isVideo = file.type.startsWith('video/');
    return (
      <div className="relative inline-block">
        {isVideo
          ? <video src={url} controls className="max-h-48 rounded-lg border border-slate-200 bg-black" />
          : <img src={url} alt="solution" className="max-h-48 rounded-lg border border-slate-200 object-contain bg-slate-50" />}
        <button type="button" onClick={onClear} data-testid={`${testId}-remove`} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow">
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }
  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); validate(e.dataTransfer.files?.[0]); }}
      className={`flex flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed py-4 px-3 cursor-pointer transition-colors ${drag ? 'border-[#1B3A52] bg-[#1B3A52]/5' : 'border-slate-300 hover:border-[#1B3A52]/60 hover:bg-slate-50'}`}
      data-testid={testId}
    >
      <Upload className="h-5 w-5 text-slate-400" />
      <span className="text-xs text-slate-500 text-center">Drop image or short video (≤25 MB) — or click to browse</span>
      <input type="file" accept="image/*,video/mp4,video/quicktime,video/webm" className="sr-only" onChange={(e) => validate(e.target.files?.[0])} />
    </label>
  );
}

/* ============================== PAGE ============================== */
export default function AddQuestion() {
  const navigate = useNavigate();
  const [folders, setFolders] = useState([]);
  const [expanded, setExpanded] = useState(new Set());
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [q, setQ] = useState(emptyQuestion());
  const [qImage, setQImage] = useState(null);
  const [optImages, setOptImages] = useState({ A: null, B: null, C: null, D: null });
  const [solutionMedia, setSolutionMedia] = useState(null);
  const [saving, setSaving] = useState(false);
  const [savedCount, setSavedCount] = useState(0);

  useEffect(() => { setPageTitle('Add Question — Question Bank'); loadFolders(); }, []);

  const loadFolders = async () => {
    try {
      const { data } = await api.get('/teacher/qb/folders');
      setFolders(data.folders || []);
      // Expand roots by default
      setExpanded((p) => {
        const n = new Set(p);
        (data.folders || []).forEach((r) => n.add(r.id));
        return n;
      });
    }
    catch (e) { toast.error('Failed to load folders'); }
  };

  const toggleExpanded = (id) => setExpanded((p) => {
    const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n;
  });

  const toggleCorrect = (opt) => {
    if (q.question_type === 'MCQ_Single') setQ({ ...q, correct_answers: [opt] });
    else setQ((p) => ({
      ...p,
      correct_answers: p.correct_answers.includes(opt)
        ? p.correct_answers.filter((c) => c !== opt)
        : [...p.correct_answers, opt],
    }));
  };

  // Live total-size calculation + 15 MB guard
  const totalImageBytes = useMemo(() => {
    let n = 0;
    if (qImage) n += qImage.size;
    ['A', 'B', 'C', 'D'].forEach((k) => { if (optImages[k]) n += optImages[k].size; });
    return n;
  }, [qImage, optImages]);
  const overQuota = totalImageBytes > MAX_TOTAL_BYTES;

  const setImageIfUnder = (setter, next, label) => {
    const existingWithout = totalImageBytes - (
      label === 'Q' ? (qImage?.size || 0) : (optImages[label]?.size || 0)
    );
    if (next && existingWithout + next.size > MAX_TOTAL_BYTES) {
      toast.error(
        `Total image size would exceed 15 MB (${MB(existingWithout + next.size)}). ` +
        `Compress or drop another image first.`,
      );
      return;
    }
    setter(next);
  };

  const resetQuestionKeepScope = () => {
    setQ(emptyQuestion());
    setQImage(null);
    setOptImages({ A: null, B: null, C: null, D: null });
    setSolutionMedia(null);
  };

  const validate = () => {
    if (!selectedFolder) return 'Pick a folder (leaf) first';
    if (q.question_type.startsWith('MCQ')) {
      if (q.correct_answers.length === 0) return 'Select at least one correct option';
      if (q.question_type === 'MCQ_Single' && q.correct_answers.length !== 1)
        return 'MCQ Single must have exactly one correct option';
    }
    if (q.question_type.startsWith('Numerical') && q.numerical_answer === '')
      return 'Enter the numerical answer';
    if (overQuota) return 'Reduce image sizes — total exceeds 15 MB';
    return null;
  };

  const save = async () => {
    const err = validate();
    if (err) { toast.error(err); return; }
    setSaving(true);
    const fd = new FormData();
    fd.append('folder_id', selectedFolder.id);
    fd.append('question_text', q.question_text);
    fd.append('question_type', q.question_type);
    fd.append('difficulty', q.difficulty);
    fd.append('marks', String(q.marks));
    fd.append('negative_marks', String(q.negative_marks));
    fd.append('teacher_note', q.teacher_note);
    fd.append('solution_youtube_url', q.solution_youtube_url || '');
    if (solutionMedia) fd.append('solution_media', solutionMedia);
    if (q.question_type.startsWith('MCQ')) {
      fd.append('options_text', JSON.stringify({
        A: q.options.A.text, B: q.options.B.text, C: q.options.C.text, D: q.options.D.text,
      }));
      fd.append('correct_answers', JSON.stringify(q.correct_answers));
    } else {
      fd.append('numerical_answer', String(q.numerical_answer));
      if (q.answer_range.min !== '' && q.answer_range.max !== '') {
        fd.append('answer_range', JSON.stringify(q.answer_range));
      }
    }
    if (qImage) fd.append('question_image', qImage);
    ['A', 'B', 'C', 'D'].forEach((k) => {
      if (optImages[k]) fd.append(`option_${k.toLowerCase()}_image`, optImages[k]);
    });
    try {
      await api.post('/teacher/question-bank', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Question saved');
      setSavedCount((c) => c + 1);
      resetQuestionKeepScope();
      loadFolders(); // refresh counts
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Save failed');
    } finally { setSaving(false); }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6" data-testid="qbank-add-page">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/teacher/question-bank')} data-testid="qbank-back">
            <ChevronLeft className="h-4 w-4 mr-1" /> Back to Bank
          </Button>
          <h1 className="text-2xl font-bold" style={{ color: NAVY }}>Add Question</h1>
        </div>
        {savedCount > 0 && (
          <span className="text-xs bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full">
            {savedCount} saved this session
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6">
        {/* Folder picker (left) */}
        <Card className="border-slate-200 shadow-sm h-fit sticky top-4">
          <CardContent className="p-3">
            <div className="text-xs uppercase font-semibold text-slate-500 mb-2 px-2">Pick a leaf folder *</div>
            <div className="max-h-[70vh] overflow-y-auto pb-2">
              {folders.length === 0
                ? <div className="text-xs text-slate-400 italic p-3">Loading folders…</div>
                : <QBFolderTree
                    roots={folders}
                    expanded={expanded}
                    toggleExpanded={toggleExpanded}
                    selectedId={selectedFolder?.id}
                    onSelect={setSelectedFolder}
                  />}
            </div>
            {selectedFolder && (
              <div className="mt-2 p-2 rounded-md bg-emerald-50 border border-emerald-200 text-xs text-emerald-700">
                <div className="font-semibold">Adding to:</div>
                <div className="truncate">{selectedFolder.path}</div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Question form (right) */}
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-6 space-y-6">
            {/* Question type */}
            <div>
              <Label className="text-slate-700">Question Type</Label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
                {[
                  ['MCQ_Single', 'MCQ (Single)'],
                  ['MCQ_Multiple', 'MCQ (Multiple)'],
                  ['Numerical_Integer', 'Numerical (Int)'],
                  ['Numerical_Decimal', 'Numerical (Dec)'],
                ].map(([v, l]) => (
                  <button
                    key={v} type="button"
                    onClick={() => setQ({ ...q, question_type: v, correct_answers: [], numerical_answer: '' })}
                    className={`px-3 py-2 rounded-lg text-sm border-2 transition-all ${q.question_type === v ? 'border-[#1B3A52] bg-[#1B3A52] text-white' : 'border-slate-200 text-slate-600 hover:border-[#1B3A52]/40'}`}
                    data-testid={`qtype-${v}`}
                  >{l}</button>
                ))}
              </div>
            </div>

            {/* Question text */}
            <div>
              <Label className="text-slate-700">Question Text (optional, LaTeX supported)</Label>
              <textarea
                rows={4}
                value={q.question_text}
                onChange={(e) => setQ({ ...q, question_text: e.target.value })}
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#1B3A52] focus:border-[#1B3A52]"
                placeholder="Type the question…  ($x^2$ inline TeX)"
                data-testid="q-text"
              />
            </div>

            {/* Image size indicator */}
            <div className={`p-3 rounded-lg border flex items-center justify-between ${overQuota ? 'border-red-300 bg-red-50' : 'border-slate-200 bg-slate-50'}`}>
              <div className="text-xs">
                <div className="font-semibold text-slate-700">Image budget: 15 MB total per question</div>
                <div className={overQuota ? 'text-red-600' : 'text-slate-500'}>
                  Used: <b>{MB(totalImageBytes)}</b> / 15 MB
                </div>
              </div>
              <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${overQuota ? 'bg-red-500' : 'bg-emerald-500'}`}
                  style={{ width: `${Math.min(100, (totalImageBytes / MAX_TOTAL_BYTES) * 100)}%` }}
                />
              </div>
            </div>

            {/* Question image */}
            <div>
              <Label className="text-slate-700">Question Image (optional)</Label>
              <div className="mt-1">
                <ImageDrop
                  file={qImage}
                  onFile={(f) => setImageIfUnder(setQImage, f, 'Q')}
                  onClear={() => setQImage(null)}
                  label="Drag question image here or click to browse"
                  testId="q-image-drop"
                />
              </div>
            </div>

            {/* MCQ options */}
            {q.question_type.startsWith('MCQ') && (
              <div className="space-y-3">
                <Label className="text-slate-700">
                  Options *
                  {q.question_type === 'MCQ_Multiple' && (
                    <span className="ml-2 text-xs text-[#1B3A52]">(select multiple correct)</span>
                  )}
                </Label>
                {['A', 'B', 'C', 'D'].map((opt) => (
                  <div
                    key={opt}
                    className={`grid grid-cols-1 md:grid-cols-[auto_1fr_180px] gap-3 items-start p-3 rounded-lg border-2 transition-colors ${q.correct_answers.includes(opt) ? 'border-emerald-500 bg-emerald-50/40' : 'border-slate-200'}`}
                  >
                    <label className="flex items-center gap-2 pt-1.5">
                      <input
                        type={q.question_type === 'MCQ_Single' ? 'radio' : 'checkbox'}
                        checked={q.correct_answers.includes(opt)}
                        onChange={() => toggleCorrect(opt)}
                        className="w-4 h-4 accent-[#1B3A52]"
                        data-testid={`opt-${opt}-correct`}
                      />
                      <span className="font-bold" style={{ color: NAVY }}>{opt}.</span>
                    </label>
                    <Input
                      value={q.options[opt].text}
                      onChange={(e) => setQ({
                        ...q,
                        options: { ...q.options, [opt]: { ...q.options[opt], text: e.target.value } },
                      })}
                      placeholder={`Option ${opt} text`}
                      data-testid={`opt-${opt}-text`}
                    />
                    <ImageDrop
                      file={optImages[opt]}
                      onFile={(f) => setImageIfUnder((v) => setOptImages((p) => ({ ...p, [opt]: v })), f, opt)}
                      onClear={() => setOptImages((p) => ({ ...p, [opt]: null }))}
                      label={<span className="flex items-center gap-1"><ImageIcon className="h-3 w-3" />Option {opt}</span>}
                      testId={`opt-${opt}-image-drop`}
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Numerical answer */}
            {q.question_type.startsWith('Numerical') && (
              <div className="p-4 rounded-lg border border-amber-200 bg-amber-50/50 space-y-3">
                <div>
                  <Label>Numerical Answer * ({q.question_type === 'Numerical_Integer' ? 'Integer' : 'Decimal'})</Label>
                  <Input
                    type="number"
                    step={q.question_type === 'Numerical_Decimal' ? '0.01' : '1'}
                    value={q.numerical_answer}
                    onChange={(e) => setQ({ ...q, numerical_answer: e.target.value })}
                    data-testid="num-answer"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-500">Answer Range (optional)</Label>
                  <div className="grid grid-cols-2 gap-3 mt-1">
                    <Input type="number" step="0.01" placeholder="Min" value={q.answer_range.min}
                      onChange={(e) => setQ({ ...q, answer_range: { ...q.answer_range, min: e.target.value } })} />
                    <Input type="number" step="0.01" placeholder="Max" value={q.answer_range.max}
                      onChange={(e) => setQ({ ...q, answer_range: { ...q.answer_range, max: e.target.value } })} />
                  </div>
                </div>
              </div>
            )}

            {/* Meta */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <div>
                <Label>Difficulty</Label>
                <Select value={q.difficulty} onValueChange={(v) => setQ({ ...q, difficulty: v })}>
                  <SelectTrigger data-testid="q-difficulty"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {DIFFICULTIES.map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Marks</Label>
                <Input type="number" value={q.marks} onChange={(e) => setQ({ ...q, marks: parseInt(e.target.value, 10) || 0 })} />
              </div>
              <div>
                <Label>Negative Marks</Label>
                <Input type="number" value={q.negative_marks} onChange={(e) => setQ({ ...q, negative_marks: parseInt(e.target.value, 10) || 0 })} />
              </div>
            </div>

            {/* Solution */}
            <div className="rounded-xl border-2 border-[#1B3A52]/15 bg-[#1B3A52]/[0.03] p-4 space-y-4">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-[#1B3A52] text-white flex items-center justify-center">
                  <Check className="h-4 w-4" />
                </div>
                <div>
                  <div className="font-semibold text-slate-800">Solution / Hint (all optional)</div>
                  <div className="text-xs text-slate-500">Shown to students after an attempt.</div>
                </div>
              </div>
              <div>
                <Label className="text-slate-700 text-xs">Written Explanation</Label>
                <textarea rows={2} value={q.teacher_note}
                  onChange={(e) => setQ({ ...q, teacher_note: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#1B3A52] focus:border-[#1B3A52]"
                  placeholder="Solution steps, common trap…"
                  data-testid="q-teacher-note"
                />
              </div>
              <div>
                <Label className="text-slate-700 text-xs flex items-center gap-1.5">
                  <Youtube className="h-3.5 w-3.5 text-red-600" /> YouTube Solution Link
                </Label>
                <Input type="url" placeholder="https://youtu.be/…?t=125"
                  value={q.solution_youtube_url}
                  onChange={(e) => setQ({ ...q, solution_youtube_url: e.target.value })}
                  className="mt-1"
                  data-testid="q-solution-youtube"
                />
              </div>
              <div>
                <Label className="text-slate-700 text-xs flex items-center gap-1.5">
                  <Film className="h-3.5 w-3.5 text-[#1B3A52]" /> Solution Image or Short Video
                </Label>
                <div className="mt-1">
                  <MediaDrop file={solutionMedia} onFile={setSolutionMedia}
                    onClear={() => setSolutionMedia(null)} testId="q-solution-media" />
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-4 border-t border-slate-200">
              <Button
                onClick={save}
                disabled={saving || overQuota}
                className="bg-[#1B3A52] hover:bg-[#2B4A62] text-white flex-1 min-w-[200px]"
                data-testid="qbank-save-btn"
              >
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Check className="h-4 w-4 mr-2" />}
                Save to Question Bank
              </Button>
              {selectedFolder && (
                <Button variant="outline" onClick={resetQuestionKeepScope} data-testid="qbank-add-another">
                  + Add Another to "{selectedFolder.name}"
                </Button>
              )}
              <Button variant="ghost" asChild>
                <Link to="/teacher/question-bank">Done</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
