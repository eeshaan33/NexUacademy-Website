import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Trash2, Bookmark as BookmarkIcon, Search, PlayCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { setPageTitle } from '../utils/pageTitle';

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
    const hay = `${b.question_details?.question_text || ''} ${b.question_details?.chapter || ''} ${b.question_details?.subject || ''} ${b.notes || ''}`.toLowerCase();
    return hay.includes(q.toLowerCase());
  });

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-5" data-testid="bookmarks-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <BookmarkIcon className="h-7 w-7 text-indigo-600" /> My Bookmarks
          </h1>
          <p className="text-sm text-slate-500 mt-1">Questions you've saved for later review.</p>
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
                ? 'Save questions from PYQ or Test Results to revisit them later.'
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
          {filtered.map((b) => (
            <Card key={b.bookmark_id} className="border-0 shadow-sm hover:shadow-md transition" data-testid={`bookmark-${b.bookmark_id}`}>
              <CardContent className="p-5 flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1 text-xs text-slate-500">
                    <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600">{b.question_details?.subject || 'Subject'}</span>
                    <span className="truncate">{b.question_details?.chapter || 'Chapter'}</span>
                  </div>
                  <p className="text-slate-800 line-clamp-3">
                    {b.question_details?.question_text || 'Question unavailable'}
                  </p>
                  {b.notes && (
                    <p className="text-xs text-slate-500 mt-2 italic">Note: {b.notes}</p>
                  )}
                  <p className="text-xs text-slate-400 mt-2">
                    Saved on {new Date(b.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={() => remove(b.bookmark_id)} data-testid={`remove-bookmark-${b.bookmark_id}`}>
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default BookmarksPage;
