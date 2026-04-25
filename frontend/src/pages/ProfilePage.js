import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { User, Mail, Phone, MapPin, Calendar, GraduationCap, IdCard, Hash, Copy, CheckCircle } from 'lucide-react';
import api from '../utils/api';
import { setPageTitle } from '../utils/pageTitle';
import { toast } from 'sonner';

const InfoRow = ({ icon: Icon, label, value, mono }) => (
  <div className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-0">
    <Icon className="h-4 w-4 text-slate-400 mt-1 shrink-0" />
    <div className="flex-1 min-w-0">
      <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`text-slate-800 ${mono ? 'font-mono' : 'font-medium'} break-words`}>{value || '—'}</p>
    </div>
  </div>
);

const ProfilePage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState('');

  useEffect(() => {
    setPageTitle('My Profile');
    (async () => {
      try {
        const res = await api.get('/admissions/me');
        setData(res.data);
      } catch (e) {
        toast.error('Could not load profile');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const copy = (val, key) => {
    if (!val) return;
    navigator.clipboard.writeText(val);
    setCopied(key);
    toast.success('Copied');
    setTimeout(() => setCopied(''), 1200);
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading your profile...</div>;
  }
  if (!data) {
    return <div className="p-8 text-center text-slate-400">No profile available.</div>;
  }

  const u = data.user || {};
  const b = data.batch;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6" data-testid="profile-page">
      {/* Header card */}
      <Card className="border-0 shadow-lg overflow-hidden">
        <div className="h-28 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500" />
        <CardContent className="-mt-14 pb-6">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div className="flex items-end gap-4">
              {u.profile_pic ? (
                <img src={u.profile_pic} alt={u.name}
                  className="w-28 h-28 rounded-2xl border-4 border-white shadow-lg object-cover bg-white" />
              ) : (
                <div className="w-28 h-28 rounded-2xl border-4 border-white shadow-lg bg-indigo-100 text-indigo-600 flex items-center justify-center text-3xl font-bold">
                  {u.name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '?'}
                </div>
              )}
              <div className="pb-2">
                <h1 className="text-2xl font-bold text-slate-900" data-testid="profile-name">{u.name}</h1>
                <p className="text-slate-500 text-sm">{u.email}</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {u.role && <Badge className="bg-indigo-100 text-indigo-700 capitalize">{u.role}</Badge>}
                  {b?.name && <Badge className="bg-amber-100 text-amber-800">{b.name}</Badge>}
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-2 items-stretch md:items-end">
              {u.roll_number && (
                <button onClick={() => copy(u.roll_number, 'roll')}
                  className="flex items-center gap-2 bg-amber-50 text-amber-800 border border-amber-200 px-4 py-2 rounded-lg hover:bg-amber-100 transition"
                  data-testid="profile-roll-number">
                  <Hash className="h-4 w-4" />
                  <span className="font-mono font-semibold">{u.roll_number}</span>
                  {copied === 'roll' ? <CheckCircle className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4 text-amber-700" />}
                </button>
              )}
              {u.batch_code && (
                <button onClick={() => copy(u.batch_code, 'code')}
                  className="flex items-center gap-2 bg-indigo-50 text-indigo-800 border border-indigo-200 px-4 py-2 rounded-lg hover:bg-indigo-100 transition"
                  data-testid="profile-batch-code">
                  <GraduationCap className="h-4 w-4" />
                  <span className="font-mono font-semibold tracking-wider">{u.batch_code}</span>
                  {copied === 'code' ? <CheckCircle className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                </button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><User className="h-4 w-4 text-indigo-500" /> Personal Details</CardTitle></CardHeader>
          <CardContent>
            <InfoRow icon={User} label="Full Name" value={u.name} />
            <InfoRow icon={Calendar} label="Date of Birth" value={u.date_of_birth} />
            <InfoRow icon={User} label="Gender" value={u.gender} />
            <InfoRow icon={User} label="Father's Name" value={u.father_name} />
            <InfoRow icon={User} label="Mother's Name" value={u.mother_name} />
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Mail className="h-4 w-4 text-indigo-500" /> Contact</CardTitle></CardHeader>
          <CardContent>
            <InfoRow icon={Mail} label="Email" value={u.email} />
            <InfoRow icon={Phone} label="Phone" value={u.phone_number} />
            <InfoRow icon={MapPin} label="Address" value={u.address} />
            <InfoRow icon={MapPin} label="City / State" value={[u.city, u.state].filter(Boolean).join(', ')} />
            <InfoRow icon={MapPin} label="Pincode" value={u.pincode} />
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm md:col-span-2">
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><GraduationCap className="h-4 w-4 text-indigo-500" /> Academic & Account</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
            <InfoRow icon={Hash} label="Roll Number" value={u.roll_number} mono />
            <InfoRow icon={IdCard} label="Admission ID" value={u.admission_id} mono />
            <InfoRow icon={GraduationCap} label="Batch" value={b?.name || u.batch_id} />
            <InfoRow icon={Hash} label="Batch Join Code" value={u.batch_code} mono />
            <InfoRow icon={GraduationCap} label="Course" value={u.course} />
            <InfoRow icon={Calendar} label="Joined" value={u.created_at ? new Date(u.created_at).toLocaleDateString() : null} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ProfilePage;
