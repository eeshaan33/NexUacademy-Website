import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Trash2, Bookmark as BookmarkIcon, Search, PlayCircle, FileText } from 'lucide-react';
import { toast } from 'sonner';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';
import api from '../utils/api';
import { setPageTitle } from '../utils/pageTitle';

const BACKEND = process.env.REACT_APP_BACKEND_URL;

function renderMath(text) {
  if (!text || typeof text !== 'string') return text;
  const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[^$]+?\$)/g);
  return parts.map((part, i) => {
    if (part.startsWith('$$') && part.endsWith('$$')) {
      try { return <BlockMath key={i} math={part.slice(2, -2)} />; } catch { return part; }
    } else if (part.startsWith('$') && part.endsWith('$')) {
      try { return <InlineMath key={i} math={part.slice(1, -1)} />; } catch { return part; }
    }
    return <span key={i}>{part}</span>;
  });
}

const BookmarksPage = () => {
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');

  useEffect(() => {
    setPageTitle('My Bookmarks');
    load();
  }, []);

  const load = async () => {
    try {
      const res = await api.get('/bookmarks/');
      setBookmarks(res.data.bookmarks || []);
    } catch (e) {
      // empty
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm('Remove this bookmark?')) return;
    try {
      await api.delete(`/bookmarks/${id}`);
      toast.success('Bookmark removed');
      setBookmarks((prev) => prev.filter((b) => b.bookmark_id !== id));
    } catch {
      toast.error('Failed to remove');
    }
  };

  const filtered = bookmarks.filter((b) => {
    const snap = b.snapshot || {};
    const hay = `${snap.question_text || ''} ${snap.chapter || ''} ${snap.subject || ''} ${snap.topic || ''} ${b.notes || ''}`.toLowerCase();
    return hay.includes(q.toLowerCase());
  });

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-5" data-testid="bookmarks-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <BookmarkIcon className="h-7 w-7 text-indigo-600" /> My Bookmarks
          </h1>
          <p className="text-sm text-slate-500 mt-1">Questions saved from PYQ practice and test reviews.</p>
        </div>
        <div className="relative w-full md:w-72">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            data-testid="bookmark-search"
            placeholder="Search your bookmarks…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-400">Loading…</div>
      ) : filtered.length === 0 ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="py-14 text-center space-y-3">
            <BookmarkIcon className="h-12 w-12 text-slate-300 mx-auto" />
            <p className="font-medium text-slate-600">
              {bookmarks.length === 0 ? 'No bookmarks yet' : 'No matching bookmarks'}
            </p>
            <p className="text-sm text-slate-400">
              {bookmarks.length === 0
                ? 'Tap the bookmark icon on any PYQ or test-review question to save it here.'
                : 'Try a different search.'}
            </p>
            {bookmarks.length === 0 && (
              <Link to="/pyq" className="inline-flex items-center gap-1 text-indigo-600 font-medium text-sm hover:underline">
                <PlayCircle className="h-4 w-4" /> Browse PYQ bank →
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3">
          {filtered.map((b) => {
            const snap = b.snapshot || {};
            const isTest = b.source === 'test_attempt';
            return (
              <Card key={b.bookmark_id} className="border-0 shadow-sm hover:shadow-md transition" data-testid={`bookmark-${b.bookmark_id}`}>
                <CardContent className="p-5 flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2 text-xs">
                      <span className={`px-2 py-0.5 rounded-full ${isTest ? 'bg-amber-50 text-amber-700' : 'bg-indigo-50 text-indigo-600'}`}>
                        {isTest ? <><FileText className="inline h-3 w-3 mr-0.5" />Test review</> : 'PYQ'}
                      </span>
                      {snap.subject && <span className="text-slate-500">{snap.subject}</span>}
                      {snap.chapter && <span className="text-slate-400 truncate">· {snap.chapter}</span>}
                      {snap.year && <span className="text-slate-400">· {snap.year}</span>}
                      {snap.difficulty && <span className="text-slate-400">· {snap.difficulty}</span>}
                    </div>
                    <div className="text-slate-800 line-clamp-3">
                      {snap.question_text ? renderMath(snap.question_text) : 'Question unavailable'}
                    </div>
                    {snap.question_image_url && (
                      <img
                        src={snap.question_image_url.startsWith('/') ? `${BACKEND}${snap.question_image_url}` : snap.question_image_url}
                        alt=""
                        className="mt-2 max-w-[240px] max-h-32 rounded border"
                      />
                    )}
                    {b.notes && <p className="text-xs text-slate-500 mt-2 italic">Note: {b.notes}</p>}
                    <p className="text-xs text-slate-400 mt-2">
                      Saved on {new Date(b.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => remove(b.bookmark_id)} data-testid={`remove-bookmark-${b.bookmark_id}`}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default BookmarksPage;
