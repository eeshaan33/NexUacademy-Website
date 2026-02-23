import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { 
  Clock, Calendar, Video, FileText, Download, Play, 
  ArrowLeft, User, BookOpen, ExternalLink, Bell
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

// Subject color mapping
const subjectColors = {
  Physics: {
    gradient: 'from-blue-500 to-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-400',
    text: 'text-blue-700',
    badge: 'bg-blue-100 text-blue-700'
  },
  Chemistry: {
    gradient: 'from-green-500 to-green-600',
    bg: 'bg-green-50',
    border: 'border-green-400',
    text: 'text-green-700',
    badge: 'bg-green-100 text-green-700'
  },
  Mathematics: {
    gradient: 'from-red-500 to-red-600',
    bg: 'bg-red-50',
    border: 'border-red-400',
    text: 'text-red-700',
    badge: 'bg-red-100 text-red-700'
  },
  General: {
    gradient: 'from-purple-500 to-purple-600',
    bg: 'bg-purple-50',
    border: 'border-purple-400',
    text: 'text-purple-700',
    badge: 'bg-purple-100 text-purple-700'
  }
};

// Countdown timer component
const CountdownTimer = ({ scheduledDateTime, onCanJoin }) => {
  const [timeLeft, setTimeLeft] = useState('');
  const [canJoin, setCanJoin] = useState(false);

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const classTime = new Date(scheduledDateTime);
      const diff = classTime - now;

      // Can join 10 minutes before
      const joinable = diff <= 10 * 60 * 1000 && diff > -60 * 60 * 1000;
      setCanJoin(joinable);
      onCanJoin && onCanJoin(joinable);

      if (diff <= 0 && diff > -60 * 60 * 1000) {
        setTimeLeft('Class is ongoing!');
      } else if (diff > 0) {
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);

        if (days > 0) {
          setTimeLeft(`${days}d ${hours}h ${minutes}m`);
        } else if (hours > 0) {
          setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
        } else {
          setTimeLeft(`${minutes}m ${seconds}s`);
        }
      } else {
        setTimeLeft('Class ended');
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [scheduledDateTime, onCanJoin]);

  return { timeLeft, canJoin };
};

// Next Class Featured Card
const NextClassCard = ({ classData }) => {
  const [canJoin, setCanJoin] = useState(false);
  const { timeLeft } = CountdownTimer({ 
    scheduledDateTime: classData.scheduled_datetime,
    onCanJoin: setCanJoin
  });

  const colors = subjectColors[classData.subject] || subjectColors.General;

  const handleJoinClass = () => {
    window.open(classData.meeting_link, '_blank');
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      weekday: 'long',
      day: 'numeric',
      month: 'short'
    });
  };

  const formatTime = (dateStr) => {
    return new Date(dateStr).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={`bg-gradient-to-r ${colors.gradient} rounded-2xl shadow-2xl p-8 text-white`} data-testid="next-class-card">
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <Badge className="bg-white/20 text-white border-0 hover:bg-white/30">
              NEXT CLASS
            </Badge>
            <Badge className="bg-white/20 text-white border-0 hover:bg-white/30">
              {classData.subject}
            </Badge>
            {classData.chapter && (
              <Badge className="bg-white/20 text-white border-0 hover:bg-white/30">
                {classData.chapter}
              </Badge>
            )}
          </div>

          <h2 className="text-3xl font-bold mb-2">{classData.title}</h2>

          {classData.topic && (
            <p className="text-white/90 mb-4">
              <BookOpen className="w-4 h-4 inline mr-2" />
              {classData.chapter} → {classData.topic}
            </p>
          )}

          <div className="flex items-center gap-4 text-white/90 flex-wrap">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              <span>{formatDate(classData.scheduled_datetime)}</span>
            </div>

            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              <span>{formatTime(classData.scheduled_datetime)}</span>
            </div>

            <div className="flex items-center gap-2">
              <Video className="w-5 h-5" />
              <span>{classData.duration} mins</span>
            </div>
          </div>
        </div>

        {classData.teacher_photo && (
          <img
            src={classData.teacher_photo}
            alt={classData.teacher_name}
            className="w-20 h-20 rounded-full border-4 border-white/30 hidden sm:block"
          />
        )}
      </div>

      {/* Countdown */}
      <div className="bg-white/20 rounded-xl p-6 mb-6 text-center backdrop-blur-sm">
        <p className="text-sm mb-2 opacity-90">Starts in</p>
        <p className="text-4xl font-bold font-mono">{timeLeft}</p>
      </div>

      {/* Description */}
      {classData.description && (
        <p className="text-white/90 mb-6 line-clamp-2">
          {classData.description}
        </p>
      )}

      {/* Join Button */}
      <button
        onClick={handleJoinClass}
        disabled={!canJoin}
        className={`w-full py-4 rounded-xl font-bold text-lg transition transform ${
          canJoin
            ? 'bg-white text-indigo-600 hover:scale-105 hover:shadow-xl'
            : 'bg-white/20 text-white/50 cursor-not-allowed'
        }`}
        data-testid="join-class-btn"
      >
        {canJoin ? (
          <>
            <Video className="w-5 h-5 inline mr-2" />
            Join Class Now
          </>
        ) : (
          <>
            🔒 Available 10 mins before class
          </>
        )}
      </button>

      <p className="text-center text-white/70 text-sm mt-3">
        <User className="w-4 h-4 inline mr-1" />
        {classData.teacher_name} • {classData.meeting_platform}
      </p>
    </div>
  );
};

// Upcoming Class Card
const UpcomingClassCard = ({ classData }) => {
  const [timeLeft, setTimeLeft] = useState('');
  const colors = subjectColors[classData.subject] || subjectColors.General;

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const classTime = new Date(classData.scheduled_datetime);
      const diff = classTime - now;

      if (diff > 0) {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

        if (hours > 24) {
          const days = Math.floor(hours / 24);
          setTimeLeft(`in ${days} day${days > 1 ? 's' : ''}`);
        } else if (hours > 0) {
          setTimeLeft(`in ${hours}h ${minutes}m`);
        } else {
          setTimeLeft(`in ${minutes} min${minutes > 1 ? 's' : ''}`);
        }
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 60000);
    return () => clearInterval(interval);
  }, [classData.scheduled_datetime]);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short'
    });
  };

  const formatTime = (dateStr) => {
    return new Date(dateStr).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card className={`${colors.bg} border-l-4 ${colors.border} hover:shadow-lg transition-shadow`} data-testid="upcoming-class-card">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-3">
          <Badge className={colors.badge}>
            {classData.subject}
          </Badge>
          <span className="text-sm text-gray-500">{timeLeft}</span>
        </div>

        <h3 className="text-lg font-bold text-gray-800 mb-2 line-clamp-2">
          {classData.title}
        </h3>

        <div className="space-y-2 text-sm text-gray-600 mb-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(classData.scheduled_datetime)}</span>
            <Clock className="w-4 h-4 ml-2" />
            <span>{formatTime(classData.scheduled_datetime)}</span>
          </div>

          <div className="flex items-center gap-2">
            <User className="w-4 h-4" />
            <span>{classData.teacher_name}</span>
          </div>
        </div>

        <Button
          onClick={() => window.open(classData.meeting_link, '_blank')}
          variant="outline"
          className="w-full"
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          View Details
        </Button>
      </CardContent>
    </Card>
  );
};

// Past Class Card
const PastClassCard = ({ classData }) => {
  const colors = subjectColors[classData.subject] || subjectColors.General;

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const hasResources = classData.recording_url || classData.notes_url || classData.slides_url;

  return (
    <Card className="hover:shadow-lg transition-shadow" data-testid="past-class-card">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-3">
          <Badge variant="secondary" className="bg-gray-100 text-gray-700">
            {classData.subject}
          </Badge>
          <span className="text-sm text-gray-500">
            {formatDate(classData.scheduled_datetime)}
          </span>
        </div>

        <h3 className="text-lg font-bold text-gray-800 mb-2 line-clamp-2">
          {classData.title}
        </h3>

        <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
          <User className="w-4 h-4" />
          <span>{classData.teacher_name}</span>
        </div>

        <div className="space-y-2">
          {classData.recording_url && (
            <a
              href={classData.recording_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-red-600 hover:text-red-700 font-medium text-sm"
            >
              <Play className="w-4 h-4" />
              Watch Recording
            </a>
          )}

          {classData.notes_url && (
            <a
              href={classData.notes_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium text-sm"
            >
              <FileText className="w-4 h-4" />
              Download Notes
            </a>
          )}

          {classData.slides_url && (
            <a
              href={classData.slides_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-green-600 hover:text-green-700 font-medium text-sm"
            >
              <Download className="w-4 h-4" />
              Download Slides
            </a>
          )}
        </div>

        {!hasResources && (
          <p className="text-gray-400 text-sm italic">
            Materials will be uploaded soon
          </p>
        )}
      </CardContent>
    </Card>
  );
};

// Main Classes Page
const ClassesPage = () => {
  const navigate = useNavigate();
  const [upcomingClasses, setUpcomingClasses] = useState([]);
  const [pastClasses, setPastClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('timeline');

  const fetchClasses = useCallback(async () => {
    try {
      const response = await api.get('/classes');
      const allClasses = response.data.classes || [];

      const now = new Date();
      const upcoming = allClasses.filter(c => new Date(c.scheduled_datetime) > now && c.status !== 'cancelled');
      const past = allClasses.filter(c => new Date(c.scheduled_datetime) <= now);

      // Sort upcoming by date (earliest first)
      upcoming.sort((a, b) => new Date(a.scheduled_datetime) - new Date(b.scheduled_datetime));

      // Sort past by date (latest first)
      past.sort((a, b) => new Date(b.scheduled_datetime) - new Date(a.scheduled_datetime));

      setUpcomingClasses(upcoming);
      setPastClasses(past);
    } catch (error) {
      console.error('Error fetching classes:', error);
      toast.error('Failed to load classes');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClasses();

    // Refresh every 30 seconds
    const interval = setInterval(fetchClasses, 30000);
    return () => clearInterval(interval);
  }, [fetchClasses]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4 sm:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/dashboard')}
              className="rounded-full"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-800">
                📚 My Live Classes
              </h1>
              <p className="text-gray-600 mt-1">
                {upcomingClasses.length} upcoming • {pastClasses.length} completed
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={() => setView('timeline')}
              variant={view === 'timeline' ? 'default' : 'outline'}
            >
              Timeline
            </Button>
            <Button
              onClick={() => setView('calendar')}
              variant={view === 'calendar' ? 'default' : 'outline'}
            >
              Calendar
            </Button>
          </div>
        </div>

        {/* Upcoming Classes Section */}
        {upcomingClasses.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
              <Bell className="w-6 h-6 text-indigo-600" />
              Upcoming Classes
            </h2>

            {/* Next Class - Featured */}
            <NextClassCard classData={upcomingClasses[0]} />

            {/* Other Upcoming Classes */}
            {upcomingClasses.length > 1 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
                {upcomingClasses.slice(1).map(cls => (
                  <UpcomingClassCard key={cls.class_id} classData={cls} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Past Classes Section */}
        {pastClasses.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
              <Video className="w-6 h-6 text-gray-600" />
              Past Classes & Recordings
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pastClasses.map(cls => (
                <PastClassCard key={cls.class_id} classData={cls} />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {upcomingClasses.length === 0 && pastClasses.length === 0 && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📅</div>
            <h3 className="text-2xl font-bold text-gray-700 mb-2">
              No Classes Scheduled Yet
            </h3>
            <p className="text-gray-500 mb-6">
              Check back soon for upcoming live classes!
            </p>
            <Button onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClassesPage;
