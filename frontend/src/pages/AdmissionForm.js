import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { User, Mail, Phone, Loader2, CheckCircle, IndianRupee, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { setTokens, useAuth } from '../context/AuthContext';
import { setPageTitle } from '../utils/pageTitle';

const AdmissionForm = () => {
  const navigate = useNavigate();
  const { setUser, setIsAuthenticated } = useAuth();

  const [form, setForm] = useState({ full_name: '', email: '', whatsapp_number: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => { setPageTitle('New Student Application'); }, []);

  const onChange = (e) => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!form.full_name.trim() || !form.email.trim() || !form.whatsapp_number.trim()) {
      toast.error('Please fill all fields');
      return;
    }
    if (!emailRegex.test(form.email)) {
      toast.error('Please enter a valid email');
      return;
    }
    if (form.whatsapp_number.replace(/\D/g, '').length < 10) {
      toast.error('Please enter a valid 10-digit WhatsApp number');
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post('/admissions/simple-submit', {
        full_name: form.full_name.trim(),
        email: form.email.trim().toLowerCase(),
        whatsapp_number: form.whatsapp_number.replace(/\D/g, ''),
      });
      if (data.access_token) setTokens(data.access_token, data.refresh_token);
      if (data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
      }
      toast.success('Application received! Redirecting to payment…');
      setTimeout(() => {
        navigate('/fee-structure', {
          state: {
            application_id: data.application_id,
            generated_password: data.generated_password,
          },
        });
      }, 900);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to submit. Please try again.';
      toast.error(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-10 px-4">
      <div className="max-w-lg mx-auto">
        <div className="text-center mb-6">
          <img src="/logo.png" alt="NexUacademy" className="h-20 w-auto object-contain mx-auto mb-2" />
          <h1 className="text-3xl font-bold text-slate-900">New Student Application</h1>
          <p className="text-slate-600 mt-1">Join the live batch — three fields, one payment.</p>
        </div>

        <Card className="shadow-xl border-slate-200">
          <CardHeader>
            <CardTitle>Enrol for the Live Batch</CardTitle>
            <CardDescription className="flex items-center gap-1 text-indigo-700">
              <IndianRupee className="h-4 w-4" />
              <span>30,000 · full access to live classes, tests & lectures</span>
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name *</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="full_name"
                    name="full_name"
                    value={form.full_name}
                    onChange={onChange}
                    placeholder="Enter your full name"
                    className="pl-10 h-11"
                    data-testid="full-name-input"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address *</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={form.email}
                    onChange={onChange}
                    placeholder="you@example.com"
                    className="pl-10 h-11"
                    data-testid="email-input"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="whatsapp_number">WhatsApp Number *</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="whatsapp_number"
                    name="whatsapp_number"
                    type="tel"
                    value={form.whatsapp_number}
                    onChange={onChange}
                    placeholder="10-digit number"
                    className="pl-10 h-11"
                    maxLength={14}
                    data-testid="whatsapp-input"
                    required
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-indigo-600 hover:bg-indigo-700 text-white text-base"
                data-testid="submit-application-btn"
              >
                {loading ? (
                  <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Submitting…</>
                ) : (
                  <>Continue to Payment <IndianRupee className="h-4 w-4 ml-2" />30,000</>
                )}
              </Button>

              <div className="flex items-center justify-center gap-2 text-xs text-slate-500 pt-1">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                <span>Secure Razorpay checkout · 256-bit SSL</span>
              </div>
            </form>

            <div className="mt-6 pt-4 border-t text-center text-xs text-slate-500 space-y-1">
              <p>
                Already enrolled at NexUacademy?{' '}
                <a className="text-indigo-600 hover:underline" href="/first-time-setup">
                  Claim your account
                </a>
              </p>
              <p>
                Have an account already?{' '}
                <a className="text-indigo-600 hover:underline" href="/login">Sign in</a>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdmissionForm;
