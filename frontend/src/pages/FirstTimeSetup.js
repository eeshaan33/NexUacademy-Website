import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { User, Mail, Loader2, CheckCircle, Info, Copy } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { setTokens, useAuth } from '../context/AuthContext';
import { setPageTitle } from '../utils/pageTitle';

const BATCHES = [
  { id: 'NEX2027', label: 'NEX2027 (2027 batch)' },
  { id: 'NEX2028', label: 'NEX2028 (2028 batch)' },
];

const FirstTimeSetup = () => {
  const navigate = useNavigate();
  const { setUser, setIsAuthenticated } = useAuth();

  const [form, setForm] = useState({ first_name: '', email: '', batch_id: 'NEX2027' });
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(null); // { email, password }

  useEffect(() => { setPageTitle('First-Time Account Setup'); }, []);

  const onChange = (e) => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.first_name.trim() || !form.email.trim() || !form.batch_id) {
      toast.error('Please fill all fields');
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post('/auth/claim-preseed', {
        first_name: form.first_name.trim(),
        email: form.email.trim().toLowerCase(),
        batch_id: form.batch_id,
      });
      if (data.access_token) setTokens(data.access_token, data.refresh_token);
      setUser(data.user);
      setIsAuthenticated(true);
      setDone({ email: form.email.trim().toLowerCase(), password: data.default_password });
      toast.success('Account claimed! Save your password.');
    } catch (err) {
      const detail = err.response?.data?.detail || 'Could not claim your account.';
      toast.error(detail);
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full shadow-2xl border-emerald-200">
          <CardContent className="pt-8 pb-8 text-center space-y-5">
            <div className="mx-auto bg-emerald-100 p-4 rounded-full w-fit">
              <CheckCircle className="h-14 w-14 text-emerald-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-emerald-900">You're all set!</h2>
              <p className="text-slate-600 mt-1">Save these credentials — you'll need them to log in.</p>
            </div>
            <div className="bg-slate-50 border rounded-lg p-4 text-left space-y-2">
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">Email</div>
                <div className="font-mono text-sm break-all" data-testid="claim-email">{done.email}</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">Password</div>
                <div className="flex items-center gap-2">
                  <div className="font-mono text-sm" data-testid="claim-password">{done.password}</div>
                  <button
                    className="text-slate-400 hover:text-slate-700"
                    onClick={() => { navigator.clipboard.writeText(done.password); toast.success('Copied'); }}
                    data-testid="copy-password-btn"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800 flex gap-2 text-left">
              <Info className="h-4 w-4 mt-0.5 shrink-0" />
              <span>Next time, sign in with this email using <b>Google Sign-In</b> or with the password above.</span>
            </div>
            <Button
              className="w-full h-11"
              onClick={() => navigate('/dashboard', { replace: true })}
              data-testid="go-to-dashboard-btn"
            >
              Continue to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="max-w-md w-full shadow-2xl">
        <CardHeader className="text-center">
          <img src="/logo.png" alt="NexUacademy" className="h-20 mx-auto mb-2" />
          <CardTitle className="text-2xl">First-Time Setup</CardTitle>
          <CardDescription>
            Already enrolled at NexUacademy? Claim your account below.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="first_name">First Name *</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="first_name"
                  name="first_name"
                  value={form.first_name}
                  onChange={onChange}
                  placeholder="e.g. Arjun"
                  className="pl-10"
                  data-testid="first-name-input"
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Your Email *</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={onChange}
                  placeholder="you@example.com"
                  className="pl-10"
                  data-testid="email-input"
                  required
                />
              </div>
              <p className="text-xs text-slate-500">You'll use this email + Google Sign-In from now on.</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="batch_id">Batch *</Label>
              <select
                id="batch_id"
                name="batch_id"
                value={form.batch_id}
                onChange={onChange}
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                data-testid="batch-select"
              >
                {BATCHES.map(b => (
                  <option key={b.id} value={b.id}>{b.label}</option>
                ))}
              </select>
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-11"
              data-testid="claim-submit-btn"
            >
              {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Claiming...</> : 'Claim my account'}
            </Button>
            <p className="text-center text-xs text-slate-500">
              Not on the enrolled list? <a className="text-indigo-600 hover:underline" href="/admission">New Student Application</a>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default FirstTimeSetup;
