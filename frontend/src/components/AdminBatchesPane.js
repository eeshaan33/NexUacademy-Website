import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Layers, Plus, Trash2, Copy, CheckCircle } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

const AdminBatchesPane = () => {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: '', year: new Date().getFullYear() + 1, code: '' });
  const [copied, setCopied] = useState('');

  const fetchBatches = async () => {
    setLoading(true);
    try {
      const res = await api.get('/batches/');
      setBatches(res.data.batches || []);
    } catch (e) {
      toast.error('Failed to load batches');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBatches(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name || !form.year) {
      toast.error('Name and year are required');
      return;
    }
    if (form.code && !/^[A-Z0-9]+$/i.test(form.code)) {
      toast.error('Batch code must be alphanumeric');
      return;
    }
    setCreating(true);
    try {
      const payload = { name: form.name, year: Number(form.year) };
      if (form.code) payload.code = form.code.toUpperCase();
      const res = await api.post('/batches/', payload);
      toast.success(`Batch "${res.data.batch.name}" created with code ${res.data.batch.code}`);
      setForm({ name: '', year: new Date().getFullYear() + 1, code: '' });
      fetchBatches();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create batch');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (batch) => {
    if (batch.is_predefined) {
      toast.error('Predefined batches cannot be deleted');
      return;
    }
    if (!window.confirm(`Delete batch "${batch.name}"? Students assigned to it will be unassigned.`)) return;
    try {
      await api.delete(`/batches/${encodeURIComponent(batch.id)}`);
      toast.success('Batch deleted');
      fetchBatches();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Delete failed');
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopied(code);
    toast.success(`Copied "${code}" to clipboard`);
    setTimeout(() => setCopied(''), 1500);
  };

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2"><Plus className="h-5 w-5 text-amber-500" /> Create New Batch</CardTitle>
          <CardDescription className="text-slate-400">
            Each batch gets a unique alphanumeric Batch ID. Share it with students so they can join during admission.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div className="space-y-2">
              <Label className="text-slate-300">Batch Name</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. JEE Crash Course 2027"
                className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                data-testid="batch-name-input" />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Year</Label>
              <Input type="number" min={2024} max={2035} value={form.year}
                onChange={(e) => setForm({ ...form, year: e.target.value })}
                className="bg-slate-700 border-slate-600 text-white"
                data-testid="batch-year-input" />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Custom Batch ID <span className="text-slate-500 text-xs">(optional)</span></Label>
              <Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '') })}
                placeholder="Auto-generate if empty"
                maxLength={16}
                className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500 font-mono uppercase tracking-wider"
                data-testid="batch-code-input" />
            </div>
            <Button type="submit" disabled={creating} className="bg-amber-600 hover:bg-amber-700 text-white md:col-span-3 md:w-fit"
              data-testid="create-batch-btn">
              {creating ? 'Creating...' : 'Create Batch'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-amber-500" /> All Batches ({batches.length})
          </CardTitle>
          <CardDescription className="text-slate-400">
            Click on a Batch ID to copy it. Students enter this ID in the admission form to join.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-slate-500 text-center py-8">Loading...</p>
          ) : batches.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No batches yet.</p>
          ) : (
            <div className="space-y-3">
              {batches.map((b) => (
                <div key={b.id} data-testid={`batch-row-${b.code}`}
                  className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
                      <Layers className="h-5 w-5 text-amber-400" />
                    </div>
                    <div>
                      <p className="text-white font-medium">{b.name}</p>
                      <p className="text-slate-400 text-sm">Year: {b.year}{b.created_by ? ` · by ${b.created_by}` : ''}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => copyCode(b.code)}
                      className="flex items-center gap-2 bg-slate-900 px-3 py-2 rounded-md border border-slate-600 hover:border-amber-500 transition-colors"
                      data-testid={`copy-code-${b.code}`}
                    >
                      <span className="font-mono text-amber-300 tracking-wider">{b.code}</span>
                      {copied === b.code ? <CheckCircle className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4 text-slate-400" />}
                    </button>
                    {b.is_predefined ? (
                      <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30">Predefined</Badge>
                    ) : (
                      <Button size="sm" variant="outline" onClick={() => handleDelete(b)}
                        className="border-red-500/40 text-red-400 hover:bg-red-500/10"
                        data-testid={`delete-batch-${b.code}`}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminBatchesPane;
