import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Database, Upload, Sparkles, Trash2, FileDown, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const SAMPLE_CSV = `exam_type,subject,chapter,topic,year,difficulty,question_text,option_a,option_b,option_c,option_d,correct_answer
JEE_Main,Physics,Kinematics,1D motion,2022,Medium,"Find acceleration if v = 2t²",2t,4t,t²,2t²,B
JEE_Main,Chemistry,Thermodynamics,First law,2021,Easy,"Process with ΔU = 0 for ideal gas",Adiabatic,Isobaric,Isochoric,Isothermal,D`;

const AdminPyqSeederPane = () => {
  const [stats, setStats] = useState(null);
  const [csvText, setCsvText] = useState('');
  const [count, setCount] = useState(30);
  const [busy, setBusy] = useState(false);
  const [importResult, setImportResult] = useState(null);

  const loadStats = async () => {
    try {
      const { data } = await api.get('/questions/stats');
      setStats(data);
    } catch { /* ignore */ }
  };

  useEffect(() => { loadStats(); }, []);

  const handleSeedSample = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/questions/seed-sample?count=${count}`);
      toast.success(`Seeded ${data.inserted} questions. Total: ${data.total}`);
      loadStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Seeding failed');
    } finally { setBusy(false); }
  };

  const handleCsvImport = async () => {
    if (!csvText.trim()) return toast.error('Paste CSV content first');
    setBusy(true);
    setImportResult(null);
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/questions/bulk-import/csv`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'text/csv' },
        body: csvText,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Import failed');
      setImportResult(data);
      toast.success(`Imported ${data.inserted} questions`);
      loadStats();
    } catch (e) {
      toast.error(e.message || 'CSV import failed');
    } finally { setBusy(false); }
  };

  const handleWipe = async () => {
    const c = window.prompt('Type WIPE to confirm deleting ALL questions:');
    if (c !== 'WIPE') return toast.info('Cancelled');
    setBusy(true);
    try {
      const { data } = await api.delete(`/questions/bulk/all`, { params: { confirm: 'WIPE' } });
      toast.success(`Deleted ${data.deleted} questions`);
      loadStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Wipe failed');
    } finally { setBusy(false); }
  };

  const downloadTemplate = () => {
    const blob = new Blob([SAMPLE_CSV], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pyq_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4" data-testid="pyq-seeder-pane">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-4">
            <div className="text-slate-400 text-xs uppercase">Total Questions</div>
            <div className="text-3xl font-bold text-white mt-1">{(stats?.total || 0).toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700 md:col-span-2">
          <CardContent className="p-4">
            <div className="text-slate-400 text-xs uppercase mb-1">By Subject</div>
            <ResponsiveContainer width="100%" height={80}>
              <BarChart data={stats?.by_subject || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="_id" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9' }} />
                <Bar dataKey="count" fill="#14B8A6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Quick seed */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-slate-200 text-sm flex items-center gap-2"><Sparkles className="h-4 w-4 text-amber-400" /> Quick Seed (Sample Pack)</CardTitle>
        </CardHeader>
        <CardContent className="flex items-end gap-3 flex-wrap">
          <div>
            <Label className="text-slate-300">Number to seed</Label>
            <Input type="number" value={count} onChange={(e) => setCount(Math.max(5, Math.min(200, Number(e.target.value) || 30)))}
              className="bg-slate-700 border-slate-600 text-white w-28" data-testid="seed-count" />
          </div>
          <Button onClick={handleSeedSample} disabled={busy} className="bg-amber-600 hover:bg-amber-700" data-testid="seed-sample-btn">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Sparkles className="h-4 w-4 mr-1" /> Seed</>}
          </Button>
          <span className="text-xs text-slate-400">Uses a rotating pool of 15 high-quality questions across Physics / Chemistry / Math.</span>
        </CardContent>
      </Card>

      {/* CSV Import */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-slate-200 text-sm flex items-center gap-2"><Upload className="h-4 w-4 text-emerald-400" /> Bulk CSV Import</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" variant="outline" onClick={downloadTemplate} className="border-slate-600 text-slate-200 hover:bg-slate-700" data-testid="download-template">
              <FileDown className="h-4 w-4 mr-1" /> Download CSV template
            </Button>
            <span className="text-xs text-slate-400">Expected headers: exam_type, subject, chapter, topic, year, difficulty, question_text, option_a, option_b, option_c, option_d, correct_answer</span>
          </div>
          <Textarea
            rows={10}
            value={csvText}
            onChange={(e) => setCsvText(e.target.value)}
            placeholder="Paste CSV content here..."
            className="bg-slate-700 border-slate-600 text-white font-mono text-xs"
            data-testid="csv-input"
          />
          <div className="flex gap-2">
            <Button onClick={handleCsvImport} disabled={busy || !csvText.trim()} className="bg-emerald-600 hover:bg-emerald-700" data-testid="csv-import-btn">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Upload className="h-4 w-4 mr-1" /> Import CSV</>}
            </Button>
            <Button variant="ghost" onClick={() => { setCsvText(''); setImportResult(null); }} className="text-slate-300 hover:text-white hover:bg-slate-700">Clear</Button>
          </div>

          {importResult && (
            <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700 text-sm">
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle className="h-4 w-4 text-emerald-400" />
                <span className="text-slate-200">Inserted {importResult.inserted} · Total: {importResult.total}</span>
              </div>
              {importResult.errors?.length > 0 && (
                <div className="mt-2">
                  <div className="flex items-center gap-2 text-amber-400 mb-1"><AlertTriangle className="h-4 w-4" /> {importResult.errors.length} rows had errors:</div>
                  <ul className="list-disc pl-5 text-xs text-slate-400 max-h-32 overflow-y-auto">
                    {importResult.errors.slice(0, 10).map((e, i) => <li key={i}>Row {e.row}: {e.error}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Danger zone */}
      <Card className="bg-red-900/10 border-red-700/30">
        <CardHeader className="pb-2">
          <CardTitle className="text-red-300 text-sm flex items-center gap-2"><Trash2 className="h-4 w-4" /> Danger Zone</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={handleWipe} disabled={busy} className="border-red-500/40 text-red-300 hover:bg-red-500/10" data-testid="wipe-all-btn">
            <Trash2 className="h-4 w-4 mr-1" /> Delete ALL questions
          </Button>
          <p className="text-xs text-slate-500 mt-2">Requires typing WIPE to confirm.</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminPyqSeederPane;
