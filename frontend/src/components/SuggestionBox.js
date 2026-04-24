import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { MessageSquare, Send, CheckCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';

const TYPES = ['Feature Request', 'Bug Report', 'Course Content', 'UI/UX', 'General', 'Other'];

const SuggestionBox = () => {
  const { user, isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ suggestion_type: 'General', subject: '', message: '' });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Only show to authenticated students
  if (!isAuthenticated || user?.role !== 'student') return null;

  const submit = async (e) => {
    e.preventDefault();
    if (!form.subject.trim() || !form.message.trim()) return toast.error('Subject and message are required');
    setLoading(true);
    try {
      await api.post('/student/suggestions/', form);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setOpen(false);
        setForm({ suggestion_type: 'General', subject: '', message: '' });
      }, 1600);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit');
    } finally { setLoading(false); }
  };

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen(true)}
        data-testid="suggestion-box-btn"
        title="Send a suggestion"
        className="fixed bottom-6 right-6 p-3.5 bg-gradient-to-br from-indigo-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all z-40"
      >
        <MessageSquare className="h-5 w-5" />
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-indigo-600" /> Send a Suggestion
            </DialogTitle>
            <DialogDescription>
              Share feedback, report a bug, or propose a new feature.
            </DialogDescription>
          </DialogHeader>

          {success ? (
            <div className="py-10 text-center space-y-2">
              <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto" />
              <p className="font-semibold text-slate-800">Thank you!</p>
              <p className="text-sm text-slate-500">We'll review your feedback soon.</p>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              <div>
                <Label>Type *</Label>
                <Select value={form.suggestion_type} onValueChange={(v) => setForm({ ...form, suggestion_type: v })}>
                  <SelectTrigger data-testid="sug-type"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {TYPES.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Subject *</Label>
                <Input data-testid="sug-subject" value={form.subject} maxLength={100}
                  onChange={(e) => setForm({ ...form, subject: e.target.value })}
                  placeholder="Short summary of your suggestion" />
                <p className="text-[10px] text-slate-400 mt-0.5">{form.subject.length}/100</p>
              </div>
              <div>
                <Label>Message *</Label>
                <Textarea data-testid="sug-message" rows={5} value={form.message} maxLength={2000}
                  onChange={(e) => setForm({ ...form, message: e.target.value })}
                  placeholder="Describe the idea, the bug, or feedback in detail…" />
                <p className="text-[10px] text-slate-400 mt-0.5">{form.message.length}/2000</p>
              </div>
              <div className="flex gap-2 pt-2">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="flex-1 bg-indigo-600 hover:bg-indigo-700" disabled={loading} data-testid="sug-submit">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Send className="h-4 w-4 mr-1" /> Send</>}
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default SuggestionBox;
