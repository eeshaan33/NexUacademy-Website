import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Download, Search, Loader2, ShieldCheck, CircleAlert, Users } from 'lucide-react';
import api, { API_BASE_URL } from '../utils/api';
import { getToken } from '../context/AuthContext';
import { toast } from 'sonner';

const roleColor = {
  admin: 'bg-amber-500/20 text-amber-300',
  teacher: 'bg-sky-500/20 text-sky-300',
  student: 'bg-emerald-500/20 text-emerald-300',
};

const AdminContactsPane = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');

  useEffect(() => { load(); }, []);
  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/admin/contacts');
      setContacts(data.contacts || []);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load contacts');
    } finally { setLoading(false); }
  };

  const downloadCsv = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/contacts/export.csv`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'nexuacademy-contacts.csv';
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (e) { toast.error('CSV download failed'); }
  };

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return contacts;
    return contacts.filter((c) =>
      [c.name, c.email, c.phone, c.role, c.batch_id]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(needle))
    );
  }, [contacts, q]);

  const stats = useMemo(() => {
    const total = contacts.length;
    const verifiedEmail = contacts.filter((c) => c.email_verified_at).length;
    const verifiedPhone = contacts.filter((c) => c.phone_verified_at).length;
    const withPhone = contacts.filter((c) => c.phone).length;
    return { total, verifiedEmail, verifiedPhone, withPhone };
  }, [contacts]);

  return (
    <Card className="bg-slate-800 border-slate-700 text-white">
      <CardHeader className="flex flex-row items-center justify-between gap-3 flex-wrap">
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5 text-amber-500" /> Contacts
          <span className="text-xs font-normal text-slate-400 ml-2">
            {stats.total} total · {stats.withPhone} with phone · {stats.verifiedEmail} email verified
          </span>
        </CardTitle>
        <Button onClick={downloadCsv} className="bg-amber-500 hover:bg-amber-600 text-slate-900" data-testid="admin-contacts-csv">
          <Download className="h-4 w-4 mr-1.5" /> Export CSV
        </Button>
      </CardHeader>
      <CardContent>
        <div className="relative mb-4">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Search name / email / phone / batch…"
            className="pl-9 bg-slate-900 border-slate-700 text-white placeholder:text-slate-500"
            data-testid="admin-contacts-search"
          />
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12 text-slate-400">
            <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading…
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            {contacts.length === 0 ? 'No contacts yet.' : 'No matches.'}
          </div>
        ) : (
          <div className="overflow-auto rounded-lg border border-slate-700 max-h-[70vh]">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/60 sticky top-0">
                <tr className="text-left text-slate-300">
                  <th className="px-3 py-2 font-medium">Name</th>
                  <th className="px-3 py-2 font-medium">Email</th>
                  <th className="px-3 py-2 font-medium">Phone</th>
                  <th className="px-3 py-2 font-medium">Role</th>
                  <th className="px-3 py-2 font-medium">Batch</th>
                  <th className="px-3 py-2 font-medium">Verified</th>
                  <th className="px-3 py-2 font-medium">Signed Up</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.id} className="border-t border-slate-700 hover:bg-slate-900/40">
                    <td className="px-3 py-2">{c.name || <span className="text-slate-500">—</span>}</td>
                    <td className="px-3 py-2 text-slate-300">{c.email}</td>
                    <td className="px-3 py-2 text-slate-300">{c.phone || <span className="text-slate-500">—</span>}</td>
                    <td className="px-3 py-2">
                      <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full ${roleColor[c.role] || 'bg-slate-700 text-slate-300'}`}>
                        {c.role || '—'}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-300">{c.batch_id || <span className="text-slate-500">—</span>}</td>
                    <td className="px-3 py-2">
                      <div className="flex gap-1">
                        {c.email_verified_at ? (
                          <span className="flex items-center gap-0.5 text-[10px] text-emerald-300"><ShieldCheck className="h-3 w-3" /> Email</span>
                        ) : (
                          <span className="flex items-center gap-0.5 text-[10px] text-slate-500"><CircleAlert className="h-3 w-3" /> Email</span>
                        )}
                        {c.phone_verified_at ? (
                          <span className="flex items-center gap-0.5 text-[10px] text-emerald-300"><ShieldCheck className="h-3 w-3" /> Phone</span>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-3 py-2 text-slate-400 text-xs">
                      {c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AdminContactsPane;
