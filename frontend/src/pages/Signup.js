import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import axios from 'axios';
import { User, Mail, Lock, Chrome, Phone, ShieldCheck, ArrowLeft, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { setPageTitle } from '../utils/pageTitle';

const Signup = () => {
  const navigate = useNavigate();
  const { startSignupOtp, verifySignupOtp, loginWithGoogle, isAuthenticated, user } = useAuth();
  const [step, setStep] = useState('details'); // 'details' | 'otp'
  const [formData, setFormData] = useState({
    name: '', email: '', phone: '', password: '', confirmPassword: '', batch_id: '',
  });
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [batches, setBatches] = useState([]);
  const [resendCooldown, setResendCooldown] = useState(0);

  useEffect(() => { setPageTitle('Sign Up'); }, []);
  useEffect(() => { if (isAuthenticated && user) navigate('/dashboard', { replace: true }); }, [isAuthenticated, user, navigate]);
  useEffect(() => {
    axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/batches/`)
      .then((res) => setBatches(res.data.batches || []))
      .catch(() => {});
  }, []);
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setTimeout(() => setResendCooldown((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [resendCooldown]);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const validateDetails = () => {
    if (formData.password !== formData.confirmPassword) { toast.error('Passwords do not match'); return false; }
    if (formData.password.length < 6) { toast.error('Password must be at least 6 characters'); return false; }
    if (!formData.batch_id) { toast.error('Please select a batch'); return false; }
    if (!/^\+?\d[\d\s\-()]{5,}$/.test(formData.phone)) { toast.error('Enter a valid phone number'); return false; }
    return true;
  };

  const sendOtp = async () => {
    if (!validateDetails()) return;
    setLoading(true);
    try {
      await startSignupOtp({
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        phone: formData.phone.trim(),
        password: formData.password,
        batch_code: formData.batch_id,
      });
      toast.success(`Verification code sent to ${formData.email}`);
      setStep('otp');
      setResendCooldown(30);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not send code');
    } finally { setLoading(false); }
  };

  const resendOtp = async () => {
    if (resendCooldown > 0) return;
    setLoading(true);
    try {
      await startSignupOtp({
        name: formData.name.trim(), email: formData.email.trim().toLowerCase(),
        phone: formData.phone.trim(), password: formData.password,
        batch_code: formData.batch_id,
      });
      toast.success('New code sent');
      setResendCooldown(30);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Resend failed');
    } finally { setLoading(false); }
  };

  const verify = async (e) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(otp)) { toast.error('Enter the 6-digit code'); return; }
    setLoading(true);
    try {
      await verifySignupOtp(formData.email.trim().toLowerCase(), otp);
      toast.success('Welcome to NexUacademy!');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Verification failed');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-card">
        <CardHeader className="space-y-2 text-center">
          <div className="mx-auto w-fit">
            <img src="/logo.png" alt="NexUacademy" className="h-24 w-auto object-contain" />
          </div>
          <CardTitle className="text-3xl font-heading">
            {step === 'details' ? 'Join NexUacademy' : 'Verify your email'}
          </CardTitle>
          <CardDescription>
            {step === 'details'
              ? 'Create your student account to start preparing'
              : `We sent a 6-digit code to ${formData.email}`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === 'details' && (
            <>
              <form onSubmit={(e) => { e.preventDefault(); sendOtp(); }} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input id="name" name="name" type="text" required className="pl-10"
                      placeholder="John Doe" value={formData.name} onChange={handleChange}
                      data-testid="name-input" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input id="email" name="email" type="email" required className="pl-10"
                      placeholder="you@example.com" value={formData.email} onChange={handleChange}
                      data-testid="email-input" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input id="phone" name="phone" type="tel" required className="pl-10"
                      placeholder="+91 98765 43210" value={formData.phone} onChange={handleChange}
                      data-testid="phone-input" />
                  </div>
                  <p className="text-[11px] text-muted-foreground">SMS verification will be added later — for now, email code only.</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="batch_id">Select Batch</Label>
                  <Select value={formData.batch_id} onValueChange={(v) => setFormData({ ...formData, batch_id: v })}>
                    <SelectTrigger data-testid="batch-select"><SelectValue placeholder="Select your batch" /></SelectTrigger>
                    <SelectContent>
                      {batches.map((b) => <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input id="password" name="password" type="password" required minLength={6} className="pl-10"
                      placeholder="Minimum 6 characters" value={formData.password} onChange={handleChange}
                      data-testid="password-input" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input id="confirmPassword" name="confirmPassword" type="password" required className="pl-10"
                      placeholder="Re-enter password" value={formData.confirmPassword} onChange={handleChange}
                      data-testid="confirm-password-input" />
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="signup-button">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ShieldCheck className="h-4 w-4 mr-2" />}
                  Send Verification Code
                </Button>
              </form>

              <div className="relative">
                <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
                </div>
              </div>
              <Button type="button" variant="outline" className="w-full" onClick={loginWithGoogle}
                data-testid="google-signup-button">
                <Chrome className="mr-2 h-4 w-4" /> Sign up with Google
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                Already have an account?{' '}
                <Link to="/login" className="text-primary hover:underline" data-testid="login-link">Sign in</Link>
              </p>
            </>
          )}

          {step === 'otp' && (
            <form onSubmit={verify} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="otp">6-Digit Code</Label>
                <Input
                  id="otp" inputMode="numeric" maxLength={6} required
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center tracking-[0.6em] text-2xl font-bold"
                  placeholder="••••••"
                  autoFocus
                  data-testid="signup-otp-input"
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading} data-testid="signup-otp-verify">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Verify & Create Account
              </Button>
              <div className="flex items-center justify-between text-sm">
                <button type="button" onClick={() => setStep('details')}
                  className="text-muted-foreground hover:text-foreground flex items-center gap-1">
                  <ArrowLeft className="h-3 w-3" /> Change email
                </button>
                <button type="button" onClick={resendOtp} disabled={resendCooldown > 0 || loading}
                  data-testid="signup-otp-resend"
                  className={`${resendCooldown > 0 ? 'text-muted-foreground' : 'text-primary hover:underline'}`}>
                  {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
                </button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Signup;
