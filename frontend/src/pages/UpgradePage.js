import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  CheckCircle, IndianRupee, Loader2, Sparkles, Video, ClipboardList,
  Zap, Lock, Shield
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { setPageTitle } from '../utils/pageTitle';

const loadRazorpay = () => new Promise((resolve) => {
  if (window.Razorpay) return resolve(true);
  const s = document.createElement('script');
  s.src = 'https://checkout.razorpay.com/v1/checkout.js';
  s.onload = () => resolve(true);
  s.onerror = () => resolve(false);
  document.body.appendChild(s);
});

const PACKS = [
  {
    id: 'lectures_upgrade',
    price: 1500,
    tag: 'Lectures Pack',
    badge: 'Popular',
    accent: 'from-indigo-500 to-purple-500',
    features: [
      { icon: Video, text: 'All Class 11 recorded lectures' },
      { icon: Video, text: 'All Class 12 recorded lectures' },
      { icon: ClipboardList, text: 'Free sample chapter tests only', muted: true },
      { icon: Lock, text: 'Live classes NOT included', muted: true },
    ],
  },
  {
    id: 'lectures_tests_upgrade',
    price: 2500,
    tag: 'Lectures + Tests',
    badge: 'Best Value',
    accent: 'from-emerald-500 to-teal-500',
    features: [
      { icon: Video, text: 'All Class 11 recorded lectures' },
      { icon: Video, text: 'All Class 12 recorded lectures' },
      { icon: ClipboardList, text: 'All chapter-wise practice tests' },
      { icon: Lock, text: 'Live classes NOT included', muted: true },
    ],
  },
];

const tierRank = { free: 0, lectures_only: 1, full_recorded: 2, live_batch: 3 };

const UpgradePage = () => {
  const navigate = useNavigate();
  const { user, checkAuth } = useAuth();
  const [loadingPlan, setLoadingPlan] = useState(null);

  useEffect(() => { setPageTitle('Upgrade your access'); }, []);

  const currentTier = user?.access_tier || 'free';
  const currentRank = tierRank[currentTier] ?? 0;

  const handlePay = async (plan) => {
    setLoadingPlan(plan.id);
    const ok = await loadRazorpay();
    if (!ok) {
      toast.error('Payment gateway failed to load. Retry with a stable network.');
      setLoadingPlan(null);
      return;
    }
    try {
      const { data } = await api.post('/payments/create-order', { plan: plan.id });
      const options = {
        key: data.key_id,
        amount: data.amount,
        currency: data.currency,
        order_id: data.order_id,
        name: 'NexUacademy',
        description: `${plan.tag} — ${data.receipt}`,
        image: '/logo192.png',
        prefill: data.prefill,
        theme: { color: '#6366f1' },
        modal: { ondismiss: () => { toast.info('Payment cancelled.'); setLoadingPlan(null); } },
        handler: async (resp) => {
          try {
            await api.post('/payments/verify', {
              razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id,
              razorpay_signature: resp.razorpay_signature,
            });
            toast.success(`${plan.tag} unlocked! Welcome aboard 🎉`);
            await checkAuth();
            setTimeout(() => navigate('/dashboard', { replace: true }), 1000);
          } catch {
            toast.error('Payment verification failed. Contact support.');
          } finally {
            setLoadingPlan(null);
          }
        },
      };
      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', (err) => {
        toast.error(`Payment failed: ${err?.error?.description || 'unknown error'}`);
        setLoadingPlan(null);
      });
      rzp.open();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to start payment');
      setLoadingPlan(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-xs font-semibold mb-3">
          <Sparkles className="h-3.5 w-3.5" /> Unlock more content
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-slate-900">Upgrade your NexUacademy access</h1>
        <p className="text-slate-600 mt-2">
          Current plan: <span className="font-semibold capitalize" data-testid="current-tier">{currentTier.replace(/_/g, ' ')}</span>
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {PACKS.map((plan) => {
          const grantedRank = tierRank[
            plan.id === 'lectures_upgrade' ? 'lectures_only' : 'full_recorded'
          ];
          const alreadyOwned = currentRank >= grantedRank;
          const isLoading = loadingPlan === plan.id;

          return (
            <Card
              key={plan.id}
              className={`border-2 ${alreadyOwned ? 'border-emerald-200 bg-emerald-50/40' : 'border-slate-200 hover:border-indigo-300'} shadow-sm hover:shadow-lg transition-all overflow-hidden`}
              data-testid={`plan-${plan.id}`}
            >
              <CardHeader className={`bg-gradient-to-r ${plan.accent} text-white`}>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl">{plan.tag}</CardTitle>
                  {plan.badge && (
                    <Badge className="bg-white/20 text-white border-0">{plan.badge}</Badge>
                  )}
                </div>
                <CardDescription className="text-white/90 flex items-center text-2xl font-bold mt-2">
                  <IndianRupee className="h-5 w-5" />{plan.price.toLocaleString('en-IN')}
                  <span className="text-xs font-normal opacity-80 ml-2">one-time</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <ul className="space-y-2.5 mb-6">
                  {plan.features.map((f, i) => (
                    <li key={i} className={`flex items-start gap-2 text-sm ${f.muted ? 'text-slate-400' : 'text-slate-700'}`}>
                      {f.muted ? (
                        <f.icon className="h-4 w-4 mt-0.5 shrink-0 text-slate-400" />
                      ) : (
                        <CheckCircle className="h-4 w-4 mt-0.5 shrink-0 text-emerald-500" />
                      )}
                      <span>{f.text}</span>
                    </li>
                  ))}
                </ul>
                <Button
                  onClick={() => handlePay(plan)}
                  disabled={alreadyOwned || isLoading}
                  className="w-full h-11 text-base"
                  data-testid={`pay-${plan.id}-btn`}
                >
                  {alreadyOwned ? (
                    <><CheckCircle className="h-4 w-4 mr-2" /> Already unlocked</>
                  ) : isLoading ? (
                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Opening checkout…</>
                  ) : (
                    <><Zap className="h-4 w-4 mr-2" /> Pay <IndianRupee className="h-3.5 w-3.5 mx-0.5" />{plan.price.toLocaleString('en-IN')}</>
                  )}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-8 text-center">
        <p className="text-sm text-slate-500 mb-3">Want live classes too?</p>
        <a href="/admission" className="inline-flex items-center gap-2 text-indigo-600 hover:underline text-sm font-medium">
          <IndianRupee className="h-4 w-4" /> 30,000 Live Batch — recorded + live + mentorship →
        </a>
      </div>

      <div className="mt-6 text-center text-xs text-slate-400 flex items-center justify-center gap-1">
        <Shield className="h-3.5 w-3.5 text-emerald-500" /> Secure Razorpay checkout · 256-bit SSL
      </div>
    </div>
  );
};

export default UpgradePage;
