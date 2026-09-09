import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { CheckCircle, IndianRupee, Shield, BookOpen, Loader2, Copy, KeyRound } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { setPageTitle } from '../utils/pageTitle';
import { useAuth } from '../context/AuthContext';

const FEE_AMOUNT_INR = 30000;

const loadRazorpay = () => new Promise((resolve) => {
  if (window.Razorpay) return resolve(true);
  const s = document.createElement('script');
  s.src = 'https://checkout.razorpay.com/v1/checkout.js';
  s.onload = () => resolve(true);
  s.onerror = () => resolve(false);
  document.body.appendChild(s);
});

const FeeStructure = () => {
  const [loading, setLoading] = useState(false);
  const [paid, setPaid] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, checkAuth } = useAuth();

  useEffect(() => { setPageTitle('Admission Fee'); }, []);

  const handlePay = async () => {
    setLoading(true);
    const ok = await loadRazorpay();
    if (!ok) {
      toast.error('Payment gateway failed to load. Check your network and retry.');
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.post('/payments/create-order', { plan: 'admission_fee' });
      const options = {
        key: data.key_id,
        amount: data.amount,
        currency: data.currency,
        order_id: data.order_id,
        name: 'NexUacademy',
        description: `Admission Fee — ${data.receipt}`,
        image: '/logo192.png',
        prefill: data.prefill,
        theme: { color: '#6366f1' },
        modal: {
          ondismiss: () => {
            toast.info('Payment cancelled. You can retry any time.');
            setLoading(false);
          },
        },
        handler: async (resp) => {
          try {
            await api.post('/payments/verify', {
              razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id,
              razorpay_signature: resp.razorpay_signature,
            });
            setPaid(true);
            toast.success('Payment successful! Welcome to NexUacademy 🎉');
            // Refresh auth so access_tier flips from 'free' → 'live_batch' in-app
            try { await checkAuth(); } catch { /* non-fatal */ }
            setTimeout(() => navigate('/dashboard', { replace: true }), 2000);
          } catch (e) {
            toast.error('Payment could not be verified. Please contact support.');
          } finally {
            setLoading(false);
          }
        },
      };
      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', (err) => {
        toast.error(`Payment failed: ${err?.error?.description || 'unknown error'}`);
        setLoading(false);
      });
      rzp.open();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to start payment');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm mb-3">
            <CheckCircle className="h-4 w-4" /> Admission form submitted
          </div>
          <h1 className="text-3xl font-bold text-slate-900">One last step — pay your admission fee</h1>
          <p className="text-slate-500 mt-2">Complete payment to activate your NexUacademy account.</p>
        </div>

        <Card className="border-0 shadow-lg overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
            <CardTitle className="flex items-center gap-2"><BookOpen className="h-5 w-5" /> Fee Structure</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="flex items-center justify-between p-4 border-2 border-indigo-100 rounded-lg bg-indigo-50/50">
              <div>
                <p className="text-sm text-slate-500 uppercase tracking-wide">Admission Fee</p>
                <p className="text-3xl font-bold text-indigo-700 flex items-center">
                  <IndianRupee className="h-6 w-6" />{FEE_AMOUNT_INR.toLocaleString('en-IN')}
                </p>
                <p className="text-xs text-slate-500 mt-1">One-time · GST inclusive</p>
              </div>
              <Badge className="bg-indigo-600 text-white">One-time</Badge>
            </div>

            <ul className="mt-5 space-y-2 text-sm text-slate-700">
              {[
                'Full access to your assigned batch\'s live classes',
                'Weekly tests + detailed solutions',
                'Question bank + past year papers',
                'Personal mentorship from IIT-trained faculty',
                'Progress analytics + parent updates',
              ].map((t) => (
                <li key={t} className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                  <span>{t}</span>
                </li>
              ))}
            </ul>

            <div className="mt-6 flex flex-col md:flex-row items-stretch md:items-center gap-3">
              <Button
                onClick={handlePay}
                disabled={loading || paid}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white h-12 text-base"
                data-testid="pay-now-btn"
              >
                {paid ? <><CheckCircle className="h-5 w-5 mr-2" /> Payment Complete</> :
                 loading ? <><Loader2 className="h-5 w-5 mr-2 animate-spin" /> Opening Checkout...</> :
                 <>Pay <IndianRupee className="h-4 w-4 mx-1" />{FEE_AMOUNT_INR.toLocaleString('en-IN')} Securely</>}
              </Button>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Shield className="h-4 w-4 text-green-500" />
                <span>Powered by Razorpay · 256-bit SSL secured</span>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-100 text-xs text-slate-500">
              <p>Signed in as <strong>{user?.email}</strong> · Roll: <strong className="font-mono">{location.state?.roll_number || user?.roll_number || '—'}</strong></p>
              <p className="mt-1">Having trouble? Email support@nexuacademy.com</p>
            </div>

            {location.state?.generated_password && (
              <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
                <div className="flex items-center gap-2 font-semibold mb-1">
                  <KeyRound className="h-4 w-4" /> Save your login password
                </div>
                <p className="text-xs mb-2">You can also sign in via Google using the same email.</p>
                <div className="flex items-center gap-2 bg-white rounded px-2 py-1 border border-amber-200">
                  <code className="font-mono text-sm flex-1" data-testid="generated-password">{location.state.generated_password}</code>
                  <button
                    onClick={() => { navigator.clipboard.writeText(location.state.generated_password); toast.success('Copied'); }}
                    className="text-amber-700 hover:text-amber-900"
                    data-testid="copy-generated-password-btn"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FeeStructure;
