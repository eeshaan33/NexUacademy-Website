import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Plus, Trash2, Users } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

/**
 * Reusable dialog that lets a teacher create or delete CUSTOM batches.
 * Predefined batches cannot be deleted.
 */
const BatchManagerDialog = ({ batches, onBatchesChanged }) => {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [year, setYear] = useState(new Date().getFullYear() + 2);
  const [busy, setBusy] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return toast.error('Enter a batch name');
    setBusy(true);
    try {
      await api.post('/batches/', { name: name.trim(), year: Number(year) });
      toast.success(`Batch "${name.trim()}" created`);
      setName('');
      onBatchesChanged?.();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create batch');
    } finally { setBusy(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(`Delete batch "${id}"? Students in it will be unassigned.`)) return;
    try {
      await api.delete(`/batches/${encodeURIComponent(id)}`);
      toast.success('Batch deleted');
      onBatchesChanged?.();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to delete');
    }
  };

  const custom = (batches || []).filter((b) => b.is_custom);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm" data-testid="manage-batches-btn">
          <Users className="h-4 w-4 mr-1" /> Manage Batches
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Custom Batches</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-2 items-end">
            <div className="col-span-2 space-y-1">
              <Label>Batch Name</Label>
              <Input data-testid="new-batch-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. NEET 2028 - Morning" />
            </div>
            <div className="space-y-1">
              <Label>Year</Label>
              <Input data-testid="new-batch-year" type="number" value={year} onChange={(e) => setYear(e.target.value)} />
            </div>
          </div>
          <Button onClick={handleCreate} disabled={busy} className="w-full" data-testid="create-batch-btn">
            <Plus className="h-4 w-4 mr-1" /> {busy ? 'Creating…' : 'Create Batch'}
          </Button>

          <div className="pt-2 border-t">
            <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Your custom batches</div>
            {custom.length === 0 ? (
              <p className="text-sm text-slate-400">No custom batches yet. Predefined batches are always available.</p>
            ) : (
              <div className="space-y-1">
                {custom.map((b) => (
                  <div key={b.id} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2" data-testid={`custom-batch-${b.id}`}>
                    <div>
                      <div className="text-sm font-medium text-slate-800">{b.name}</div>
                      <div className="text-xs text-slate-400">Year {b.year || '—'} · by {b.created_by || 'teacher'}</div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(b.id)} data-testid={`delete-batch-${b.id}`}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default BatchManagerDialog;
