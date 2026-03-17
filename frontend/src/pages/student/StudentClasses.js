import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Video, Calendar, Clock, ExternalLink, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../utils/api';

const StudentClasses = () => {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadClasses = async () => {
    try {
      const res = await api.get('/student/classes/my-classes');
      setClasses(res.data.classes || []);
    } catch { }
    finally { setLoading(false); }
  };

  useEffect(() => {
    loadClasses();
    const interval = setInterval(loadClasses, 30000);
    return () => clearInterval(interval);
  }, []);

  const markAttendance = async (classId) => {
    try {
      const res = await api.post(`/student/classes/${classId}/attendance`);
      toast.success(res.data.message);
    } catch { toast.error('Failed to mark attendance'); }
  };

  const formatDate = (dt) => {
    if (!dt) return '';
    return new Date(dt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  };

  const statusColors = { upcoming: 'bg-blue-100 text-blue-700', ongoing: 'bg-green-100 text-green-700', completed: 'bg-slate-100 text-slate-600' };

  const upcoming = classes.filter((c) => c.status === 'upcoming' || c.status === 'ongoing');
  const past = classes.filter((c) => c.status === 'completed');

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6" data-testid="student-classes-page">
      <h1 className="text-2xl font-bold text-slate-900">My Classes</h1>

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading classes...</div>
      ) : classes.length === 0 ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="py-16 text-center">
            <Video className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No classes scheduled yet</p>
            <p className="text-sm text-slate-400 mt-1">Your teacher will schedule classes for your batch soon.</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {upcoming.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-slate-700">Upcoming & Live</h2>
              {upcoming.map((cls) => (
                <Card key={cls.class_id} className="border-0 shadow-sm border-l-4 border-l-indigo-500" data-testid={`student-class-${cls.class_id}`}>
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-lg font-semibold">{cls.title}</h3>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[cls.status]}`}>{cls.status}</span>
                        </div>
                        <div className="flex flex-wrap gap-3 text-sm text-slate-500 mt-1">
                          <span className="flex items-center gap-1">{cls.subject}</span>
                          <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{formatDate(cls.scheduled_date_time)}</span>
                          <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{cls.duration} min</span>
                        </div>
                        {cls.description && <p className="text-sm text-slate-400 mt-2">{cls.description}</p>}
                        <p className="text-xs text-slate-400 mt-1">by {cls.teacher_name}</p>
                      </div>
                      <div className="flex flex-col gap-2 ml-4 shrink-0">
                        <a href={cls.meeting_link} target="_blank" rel="noreferrer">
                          <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 w-full" data-testid={`join-class-${cls.class_id}`}>
                            <ExternalLink className="h-3.5 w-3.5 mr-1" /> Join
                          </Button>
                        </a>
                        <Button size="sm" variant="outline" onClick={() => markAttendance(cls.class_id)}>
                          <CheckCircle className="h-3.5 w-3.5 mr-1" /> Attendance
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {past.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-slate-700">Past Classes</h2>
              {past.map((cls) => (
                <Card key={cls.class_id} className="border-0 shadow-sm opacity-80">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold">{cls.title}</h3>
                        <div className="flex gap-3 text-sm text-slate-400 mt-1">
                          <span>{cls.subject}</span>
                          <span>{formatDate(cls.scheduled_date_time)}</span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {cls.recording_url && (
                          <a href={cls.recording_url} target="_blank" rel="noreferrer">
                            <Button size="sm" variant="outline">Recording</Button>
                          </a>
                        )}
                        {cls.notes_url && (
                          <a href={cls.notes_url} target="_blank" rel="noreferrer">
                            <Button size="sm" variant="outline">Notes</Button>
                          </a>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default StudentClasses;
