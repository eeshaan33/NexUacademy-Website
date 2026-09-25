import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  ChevronLeft, Upload, Image as ImageIcon, X, Check, PlusCircle,
  Search, Loader2, Youtube, Film,
} from 'lucide-react';
import api from '../../../utils/api';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Card, CardContent } from '../../../components/ui/card';
import { setPageTitle } from '../../../utils/pageTitle';

const SUBJECTS = ['Physics', 'Chemistry', 'Mathematics', 'Biology'];
const NAVY = '#1B3A52';

const emptyQuestion = () => ({
  question_text: '',
  question_type: 'MCQ_Single',
  options: { A: { text: '' }, B: { text: '' }, C: { text: '' }, D: { text: '' } },
  correct_answers: [],
  numerical_answer: '',
  answer_range: { min: '', max: '' },
  difficulty: 'Medium',
  marks: 4,
  negative_marks: -1,
  teacher_note: '',
  solution_youtube_url: '',
});

/* ---------------- Searchable topic / subtopic combobox ---------------- */
function Combobox({ label, items, value, onChange, onCreate, placeholder, testId, extraForm, disabled }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createExtra, setCreateExtra] = useState({});
  const rootRef = useRef(null);

  useEffect(() => {
    const h = (e) => { if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const selected = items.find((i) => i.id === value);
  const q = query.trim().toLowerCase();
  const filtered = q ? items.filter((i) => i.name.toLowerCase().includes(q)) : items;
  const exactMatch = items.some((i) => i.name.toLowerCase() === q);
  const canCreate = q && !exactMatch && onCreate;

  const submitCreate = async () => {
    setCreating(true);
    try {
      const created = await onCreate(query.trim(), createExtra);
      if (created) {
        onChange(created.id);
        setQuery('');
        setCreateExtra({});
        setOpen(false);
      }
    } finally { setCreating(false); }
  };

  return (
    <div className="relative" ref={rootRef}>
      <Label className="text-slate-700">{label}</Label>
      <div
        className={`mt-1 flex items-center gap-2 rounded-lg border px-3 py-2 bg-white transition-colors ${open ? 'border-[#1B3A52] ring-1 ring-[#1B3A52]/20' : 'border-slate-300'} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-text'}`}
        onClick={() => !disabled && setOpen(true)}
        data-testid={testId}
      >
        <Search className="h-4 w-4 text-slate-400" />
        <input
          className="flex-1 outline-none text-sm bg-transparent"
          placeholder={selected ? selected.name : placeholder}
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          disabled={disabled}
        />
        {selected && !query && (
          <button
            type="button"
            className="text-xs text-slate-400 hover:text-red-500"
            onClick={(e) => { e.stopPropagation(); onChange(''); }}
            data-testid={`${testId}-clear`}
          >Clear</button>
        )}
      </div>

      {open && !disabled && (
        <div className="absolute z-30 mt-1 w-full rounded-lg border border-slate-200 bg-white shadow-lg max-h-64 overflow-auto">
          {filtered.length === 0 && !canCreate && (
            <div className="p-3 text-sm text-slate-400">No matches</div>
          )}
          {filtered.map((i) => (
            <button
              key={i.id}
              type="button"
              className={`w-full text-left px-3 py-2 text-sm hover:bg-slate-50 ${i.id === value ? 'bg-[#1B3A52]/5 text-[#1B3A52] font-medium' : 'text-slate-700'}`}
              onClick={() => { onChange(i.id); setQuery(''); setOpen(false); }}
            >
              {i.name}
              {i.subject && <span className="ml-2 text-xs text-slate-400">· {i.subject}</span>}
              {typeof i.question_count === 'number' && (
                <span className="float-right text-xs text-slate-400">{i.question_count} Qs</span>
              )}
            </button>
          ))}
          {canCreate && (
            <div className="border-t border-slate-200 p-3 bg-slate-50 space-y-2">
              <div className="text-xs text-slate-500">
                Can't find it? Create new: <b className="text-slate-800">"{query.trim()}"</b>
              </div>
              {extraForm && extraForm({ value: createExtra, onChange: setCreateExtra })}
              <Button
                type="button"
                size="sm"
                onClick={submitCreate}
                disabled={creating}
                className="bg-[#1B3A52] hover:bg-[#2B4A62] text-white"
                data-testid={`${testId}-create`}
              >
                {creating ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <PlusCircle className="h-3 w-3 mr-1" />}
                Create "{query.trim()}"
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* --------------------------- Image drop zone --------------------------- */
function ImageDrop({ file, previewUrl, onFile, onClear, label = 'Drop image here or click to browse', testId }) {
  const [drag, setDrag] = useState(false);
  const validate = (f) => {
    if (!f) return;
    if (!f.type.startsWith('image/')) { toast.error('Only images allowed'); return; }
    if (f.size > 5 * 1024 * 1024) { toast.error('Image exceeds 5 MB'); return; }
    onFile(f);
  };
  if (file || previewUrl) {
    return (
      <div className="relative inline-block">
        <img
          src={previewUrl || (file && URL.createObjectURL(file))}
          alt="preview"
          className="max-h-40 rounded-lg border border-slate-200 object-contain bg-slate-50"
        />
        <button
          type="button"
          onClick={onClear}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow"
          data-testid={`${testId}-remove`}
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }
  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault(); setDrag(false);
        validate(e.dataTransfer.files?.[0]);
      }}
      className={`flex flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed py-4 px-3 cursor-pointer transition-colors ${drag ? 'border-[#1B3A52] bg-[#1B3A52]/5' : 'border-slate-300 hover:border-[#1B3A52]/60 hover:bg-slate-50'}`}
      data-testid={testId}
    >
      <Upload className="h-5 w-5 text-slate-400" />
      <span className="text-xs text-slate-500 text-center">{label}</span>
      <input
        type="file"
        accept="image/png,image/jpeg,image/jpg"
        className="sr-only"
        onChange={(e) => validate(e.target.files?.[0])}
      />
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
    const limit = isVideo ? 25 * 1024 * 1024 : 5 * 1024 * 1024;
    if (f.size > limit) { toast.error(`File exceeds ${limit / (1024 * 1024)} MB`); return; }
    onFile(f);
  };
  if (file) {
    const url = URL.createObjectURL(file);
    const isVideo = file.type.startsWith('video/');
    return (
      <div className="relative inline-block">
        {isVideo ? (
          <video src={url} controls className="max-h-48 rounded-lg border border-slate-200 bg-black" />
        ) : (
          <img src={url} alt="solution" className="max-h-48 rounded-lg border border-slate-200 object-contain bg-slate-50" />
        )}
        <button type="button" onClick={onClear} data-testid={`${testId}-remove`}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow">
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
      <span className="text-xs text-slate-500 text-center">Drop an image (≤5 MB) or short video (≤25 MB) — or click to browse</span>
      <input
        type="file"
        accept="image/png,image/jpeg,image/jpg,video/mp4,video/quicktime,video/webm"
        className="sr-only"
        onChange={(e) => validate(e.target.files?.[0])}
      />
    </label>
  );
}

/* ============================== PAGE ============================== */
export default function AddQuestion() {
  const navigate = useNavigate();
  const [topics, setTopics] = useState([]);
  const [subtopics, setSubtopics] = useState([]);
  const [topicId, setTopicId] = useState('');
  const [subtopicId, setSubtopicId] = useState('');
  const [q, setQ] = useState(emptyQuestion());
  const [qImage, setQImage] = useState(null);
  const [optImages, setOptImages] = useState({ A: null, B: null, C: null, D: null });
  const [solutionMedia, setSolutionMedia] = useState(null); // image or video file
  const [saving, setSaving] = useState(false);
  const [savedCount, setSavedCount] = useState(0);

  useEffect(() => { setPageTitle('Add Question — Question Bank'); loadTopics(); }, []);
  useEffect(() => { if (topicId) loadSubtopics(topicId); else setSubtopics([]); setSubtopicId(''); }, [topicId]);

  const loadTopics = async () => {
    try { const { data } = await api.get('/teacher/topics'); setTopics(data.topics || []); }
    catch (e) { toast.error('Failed to load topics'); }
  };
  const loadSubtopics = async (tid) => {
    try { const { data } = await api.get(`/teacher/topics/${tid}/subtopics`); setSubtopics(data.subtopics || []); }
    catch (e) { toast.error('Failed to load subtopics'); }
  };

  const createTopic = async (name, extra) => {
    try {
      const { data } = await api.post('/teacher/topics', { name, subject: extra.subject || null });
      toast.success(`Topic "${data.topic.name}" ready`);
      setTopics((prev) => (prev.find((t) => t.id === data.topic.id) ? prev : [...prev, data.topic]));
      return data.topic;
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to create topic'); return null; }
  };
  const createSubtopic = async (name) => {
    try {
      const { data } = await api.post('/teacher/subtopics', { topic_id: topicId, name });
      toast.success(`Subtopic "${data.subtopic.name}" ready`);
      setSubtopics((prev) => (prev.find((s) => s.id === data.subtopic.id) ? prev : [...prev, data.subtopic]));
      return data.subtopic;
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to create subtopic'); return null; }
  };

  const toggleCorrect = (opt) => {
    if (q.question_type === 'MCQ_Single') setQ({ ...q, correct_answers: [opt] });
    else setQ((p) => ({
      ...p,
      correct_answers: p.correct_answers.includes(opt)
        ? p.correct_answers.filter((c) => c !== opt)
        : [...p.correct_answers, opt],
    }));
  };

  const selectedTopic = useMemo(() => topics.find((t) => t.id === topicId), [topics, topicId]);
  const selectedSubtopic = useMemo(() => subtopics.find((s) => s.id === subtopicId), [subtopics, subtopicId]);

  const resetQuestionKeepScope = () => {
    setQ(emptyQuestion());
    setQImage(null);
    setOptImages({ A: null, B: null, C: null, D: null });
    setSolutionMedia(null);
  };

  const validate = () => {
    if (!topicId) return 'Pick a topic';
    if (!subtopicId) return 'Pick a subtopic';
    if (q.question_type.startsWith('MCQ')) {
      if (q.correct_answers.length === 0) return 'Select at least one correct option';
      if (q.question_type === 'MCQ_Single' && q.correct_answers.length !== 1)
        return 'MCQ Single must have exactly one correct option';
    }
    if (q.question_type.startsWith('Numerical') && q.numerical_answer === '')
      return 'Enter the numerical answer';
    return null;
  };

  const save = async () => {
    const err = validate();
    if (err) { toast.error(err); return; }
    setSaving(true);
    const fd = new FormData();
    fd.append('topic_id', topicId);
    fd.append('subtopic_id', subtopicId);
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
      toast.success('Question saved to bank');
      setSavedCount((c) => c + 1);
      resetQuestionKeepScope();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Save failed');
    } finally { setSaving(false); }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6" data-testid="qbank-add-page">
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

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6 space-y-6">
          {/* Topic + Subtopic */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Combobox
              label="Topic *"
              items={topics}
              value={topicId}
              onChange={setTopicId}
              onCreate={createTopic}
              placeholder="Search or create a topic…"
              testId="topic-combobox"
              extraForm={({ value, onChange }) => (
                <Select value={value.subject || ''} onValueChange={(v) => onChange({ ...value, subject: v })}>
                  <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Subject (required for new topic)" /></SelectTrigger>
                  <SelectContent>
                    {SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
            />
            <Combobox
              label="Subtopic *"
              items={subtopics}
              value={subtopicId}
              onChange={setSubtopicId}
              onCreate={topicId ? createSubtopic : null}
              placeholder={topicId ? 'Search or create a subtopic…' : 'Pick a topic first'}
              testId="subtopic-combobox"
              disabled={!topicId}
            />
          </div>

          {selectedTopic && selectedSubtopic && (
            <div className="text-xs bg-slate-50 border border-slate-200 rounded-md px-3 py-2 text-slate-600">
              Adding under <b>{selectedTopic.name}</b>
              {selectedTopic.subject && <span className="opacity-70"> · {selectedTopic.subject}</span>}
              {' › '}<b>{selectedSubtopic.name}</b>
            </div>
          )}

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
                  key={v}
                  type="button"
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

          {/* Question image */}
          <div>
            <Label className="text-slate-700">Question Image (optional, ≤5 MB)</Label>
            <div className="mt-1">
              <ImageDrop
                file={qImage}
                onFile={setQImage}
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
                    {q.correct_answers.includes(opt) && (
                      <span className="text-[10px] text-emerald-600 font-semibold uppercase">Correct</span>
                    )}
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
                  <div>
                    <ImageDrop
                      file={optImages[opt]}
                      onFile={(f) => setOptImages((prev) => ({ ...prev, [opt]: f }))}
                      onClear={() => setOptImages((prev) => ({ ...prev, [opt]: null }))}
                      label={<span className="flex items-center gap-1"><ImageIcon className="h-3 w-3" />Option {opt} image</span>}
                      testId={`opt-${opt}-image-drop`}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Numerical answer */}
          {q.question_type.startsWith('Numerical') && (
            <div className="p-4 rounded-lg border border-amber-200 bg-amber-50/50 space-y-3">
              <div>
                <Label className="text-slate-700">
                  Numerical Answer * ({q.question_type === 'Numerical_Integer' ? 'Integer' : 'Decimal'})
                </Label>
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
                <Label className="text-xs text-slate-500">Answer Range (optional, JEE Advanced style)</Label>
                <div className="grid grid-cols-2 gap-3 mt-1">
                  <Input type="number" step="0.01" placeholder="Min"
                    value={q.answer_range.min}
                    onChange={(e) => setQ({ ...q, answer_range: { ...q.answer_range, min: e.target.value } })} />
                  <Input type="number" step="0.01" placeholder="Max"
                    value={q.answer_range.max}
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
                  {['Easy', 'Medium', 'Hard'].map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}
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

          <div className="rounded-xl border-2 border-[#1B3A52]/15 bg-[#1B3A52]/[0.03] p-4 space-y-4">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-[#1B3A52] text-white flex items-center justify-center">
                <Check className="h-4 w-4" />
              </div>
              <div>
                <div className="font-semibold text-slate-800">Solution / Hint (all optional)</div>
                <div className="text-xs text-slate-500">Shown to students after an attempt. Add any combination — text, YouTube, image or video.</div>
              </div>
            </div>

            <div>
              <Label className="text-slate-700 text-xs">Written Explanation</Label>
              <textarea
                rows={2}
                value={q.teacher_note}
                onChange={(e) => setQ({ ...q, teacher_note: e.target.value })}
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#1B3A52] focus:border-[#1B3A52]"
                placeholder="Solution steps, common trap, key insight…"
                data-testid="q-teacher-note"
              />
            </div>

            <div>
              <Label className="text-slate-700 text-xs flex items-center gap-1.5">
                <Youtube className="h-3.5 w-3.5 text-red-600" />
                YouTube Solution Link
              </Label>
              <Input
                type="url"
                placeholder="https://youtu.be/…?t=125  (paste the exact timestamp)"
                value={q.solution_youtube_url}
                onChange={(e) => setQ({ ...q, solution_youtube_url: e.target.value })}
                className="mt-1"
                data-testid="q-solution-youtube"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Tip: on YouTube, right-click the video at the exact moment → <i>Copy video URL at current time</i>.
              </p>
            </div>

            <div>
              <Label className="text-slate-700 text-xs flex items-center gap-1.5">
                <Film className="h-3.5 w-3.5 text-[#1B3A52]" />
                Solution Image or Short Video
              </Label>
              <div className="mt-1">
                <MediaDrop
                  file={solutionMedia}
                  onFile={setSolutionMedia}
                  onClear={() => setSolutionMedia(null)}
                  testId="q-solution-media"
                />
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 pt-4 border-t border-slate-200">
            <Button
              onClick={save}
              disabled={saving}
              className="bg-[#1B3A52] hover:bg-[#2B4A62] text-white flex-1 min-w-[200px]"
              data-testid="qbank-save-btn"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Check className="h-4 w-4 mr-2" />}
              Save to Question Bank
            </Button>
            {selectedSubtopic && (
              <Button
                variant="outline"
                onClick={resetQuestionKeepScope}
                data-testid="qbank-add-another"
              >
                + Add Another to "{selectedSubtopic.name}"
              </Button>
            )}
            <Button variant="ghost" asChild>
              <Link to="/teacher/question-bank">Done</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
