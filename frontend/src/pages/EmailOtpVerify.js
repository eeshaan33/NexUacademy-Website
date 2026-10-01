import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Mail, ShieldCheck, ArrowLeft, Loader2, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { setPageTitle } from '../utils/pageTitle';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const NAVY = '#1B3A52';

export default function EmailOtpVerify() {
  const [step, setStep] = useState('email'); // 'email' | 'otp' | 'done'
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => { setPageTitle('Verify Email'); }, []);
  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const sendCode = async (e) => {
    if (e) e.preventDefault();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.error('Enter a valid email'); return;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/auth/send-otp`, { email: email.trim().toLowerCase() });
      toast.success(`Code sent to ${email}`);
      setStep('otp');
      setCooldown(30);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not send code');
    } finally { setLoading(false); }
  };

  const verify = async (e) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(otp)) { toast.error('Enter the 6-digit code'); return; }
    setLoading(true);
    try {
      await axios.post(`${API}/auth/verify-otp`, {
        email: email.trim().toLowerCase(), otp,
      });
      setStep('done');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Verification failed');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-xl border-slate-200" data-testid="email-otp-card">
        <CardHeader className="space-y-2 text-center">
          <div className="mx-auto h-14 w-14 rounded-2xl flex items-center justify-center text-white" style={{ background: NAVY }}>
            {step === 'done' ? <CheckCircle2 className="h-7 w-7" /> : <ShieldCheck className="h-7 w-7" />}
          </div>
          <CardTitle className="text-2xl font-bold" style={{ color: NAVY }}>
            {step === 'email' && 'Verify your email'}
            {step === 'otp' && 'Enter the 6-digit code'}
            {step === 'done' && 'Email verified'}
          </CardTitle>
          <CardDescription>
            {step === 'email' && 'We\'ll send a one-time code to confirm it\'s really you.'}
            {step === 'otp' && (<>Sent to <b className="text-slate-700">{email}</b> — expires in 5 minutes.</>)}
            {step === 'done' && 'You can safely close this page or continue to your dashboard.'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === 'email' && (
            <form onSubmit={sendCode} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input id="email" type="email" required className="pl-10"
                    placeholder="you@example.com" value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoFocus data-testid="email-input" />
                </div>
              </div>
              <Button type="submit" disabled={loading} className="w-full text-white"
                style={{ background: NAVY }} data-testid="send-otp-btn">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ShieldCheck className="h-4 w-4 mr-2" />}
                Send Verification Code
              </Button>
            </form>
          )}

          {step === 'otp' && (
            <form onSubmit={verify} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="otp">6-Digit Code</Label>
                <Input id="otp" inputMode="numeric" maxLength={6} required autoFocus
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center tracking-[0.6em] text-2xl font-bold"
                  placeholder="••••••"
                  data-testid="otp-input" />
              </div>
              <Button type="submit" disabled={loading} className="w-full text-white"
                style={{ background: NAVY }} data-testid="verify-otp-btn">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Verify Email
              </Button>
              <div className="flex items-center justify-between text-sm">
                <button type="button" onClick={() => { setStep('email'); setOtp(''); }}
                  className="text-slate-500 hover:text-slate-800 flex items-center gap-1"
                  data-testid="change-email">
                  <ArrowLeft className="h-3 w-3" /> Change email
                </button>
                <button type="button" onClick={sendCode} disabled={cooldown > 0 || loading}
                  data-testid="resend-otp"
                  className={cooldown > 0 ? 'text-slate-400' : 'text-[#1B3A52] hover:underline'}>
                  {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend code'}
                </button>
              </div>
            </form>
          )}

          {step === 'done' && (
            <div className="space-y-4 text-center">
              <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4" data-testid="verify-success">
                <div className="font-semibold text-emerald-800">{email}</div>
                <div className="text-xs text-emerald-700 mt-1">has been verified ✓</div>
              </div>
              <Button className="w-full text-white" style={{ background: NAVY }}
                onClick={() => { window.location.href = '/dashboard'; }}>
                Continue
              </Button>
              <button type="button"
                onClick={() => { setStep('email'); setEmail(''); setOtp(''); }}
                className="text-xs text-slate-500 hover:text-slate-800">
                Verify another address
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
