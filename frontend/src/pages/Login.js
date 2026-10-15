import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Mail, Lock, Chrome, ShieldCheck, ArrowLeft, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { setPageTitle } from '../utils/pageTitle';

const Login = () => {
  const navigate = useNavigate();
  const { login, verifyLoginOtp, resendLoginOtp, loginWithGoogle, loginWithEmergent, isAuthenticated, user } = useAuth();
  const [step, setStep] = useState('creds'); // 'creds' | 'otp'
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  useEffect(() => { setPageTitle('Login'); }, []);
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'admin') navigate('/admin', { replace: true });
      else if (user.role === 'teacher') navigate('/teacher', { replace: true });
      else navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, user, navigate]);
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setTimeout(() => setResendCooldown((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [resendCooldown]);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const routeUser = (u) => {
    if (u?.role === 'admin') navigate('/admin', { replace: true });
    else if (u?.role === 'teacher') navigate('/teacher', { replace: true });
    else navigate('/dashboard', { replace: true });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await login(formData.email, formData.password);
      if (data.requires_otp) {
        toast.info('New device detected — check your email for a 6-digit code');
        setStep('otp');
        setResendCooldown(30);
      } else {
        toast.success('Login successful!');
        routeUser(data.user);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally { setLoading(false); }
  };

  const verify = async (e) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(otp)) { toast.error('Enter the 6-digit code'); return; }
    setLoading(true);
    try {
      const data = await verifyLoginOtp(formData.email, formData.password, otp);
      toast.success('Device verified — signed in!');
      routeUser(data.user);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Verification failed');
    } finally { setLoading(false); }
  };

  const resend = async () => {
    if (resendCooldown > 0) return;
    try {
      await resendLoginOtp(formData.email);
      toast.success('New code sent');
      setResendCooldown(30);
    } catch (err) { toast.error(err.response?.data?.detail || 'Resend failed'); }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-card">
        <CardHeader className="space-y-2 text-center">
          <div className="mx-auto w-fit">
            <img src="/logo.png" alt="NexUacademy" className="h-24 w-auto object-contain" />
          </div>
          <CardTitle className="text-3xl font-heading">
            {step === 'creds' ? 'Welcome to NexUacademy' : 'Verify this device'}
          </CardTitle>
          <CardDescription>
            {step === 'creds'
              ? 'Sign in to continue your learning journey'
              : `We sent a 6-digit code to ${formData.email}`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === 'creds' && (
            <>
              <form onSubmit={handleSubmit} className="space-y-4">
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
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input id="password" name="password" type="password" required className="pl-10"
                      placeholder="Enter your password" value={formData.password} onChange={handleChange}
                      data-testid="password-input" />
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="login-button">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Sign in
                </Button>
              </form>

              <div className="relative">
                <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
                </div>
              </div>

              <Button type="button" variant="outline" className="w-full" onClick={loginWithEmergent}
                data-testid="emergent-google-button">
                <Chrome className="mr-2 h-4 w-4" /> Continue with Google
              </Button>
              <Button type="button" variant="ghost" className="w-full text-xs text-muted-foreground"
                onClick={loginWithGoogle} data-testid="google-login-button">
                Or use legacy Supabase Google sign-in
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                Don't have an account?{' '}
                <Link to="/signup" className="text-primary hover:underline" data-testid="signup-link">Sign up</Link>
              </p>

              <div className="pt-4 border-t space-y-2">
                <Link to="/admission">
                  <Button variant="outline" className="w-full bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 hover:bg-green-100">
                    <span className="text-green-700">New Student? Apply for Admission</span>
                  </Button>
                </Link>
                <Link to="/first-time-setup">
                  <Button variant="outline" className="w-full bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200 hover:bg-indigo-100"
                    data-testid="first-time-setup-link">
                    <span className="text-indigo-700">Already Enrolled? Claim Your Account</span>
                  </Button>
                </Link>
              </div>
            </>
          )}

          {step === 'otp' && (
            <form onSubmit={verify} className="space-y-4">
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800 flex gap-2">
                <ShieldCheck className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>We only ask for this on new devices. It expires in 10 minutes.</span>
              </div>
              <div className="space-y-2">
                <Label htmlFor="otp">6-Digit Code</Label>
                <Input
                  id="otp" inputMode="numeric" maxLength={6} required autoFocus
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center tracking-[0.6em] text-2xl font-bold"
                  placeholder="••••••"
                  data-testid="login-otp-input"
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading} data-testid="login-otp-verify">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Verify & Continue
              </Button>
              <div className="flex items-center justify-between text-sm">
                <button type="button" onClick={() => setStep('creds')}
                  className="text-muted-foreground hover:text-foreground flex items-center gap-1">
                  <ArrowLeft className="h-3 w-3" /> Back
                </button>
                <button type="button" onClick={resend} disabled={resendCooldown > 0 || loading}
                  data-testid="login-otp-resend"
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

export default Login;
