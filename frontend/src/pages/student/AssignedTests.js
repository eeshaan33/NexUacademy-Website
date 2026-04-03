import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { FileEdit, Clock, Calendar, Play, Eye } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';

const AssignedTests = () => {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    setPageTitle('Assigned Tests');
  }, []);

  const loadTests = async () => {
    try {
      const res = await api.get('/student/tests/assigned');
      setTests(res.data.tests || []);
    } catch { }
    finally { setLoading(false); }
  };

  useEffect(() => {
    loadTests();
    const interval = setInterval(loadTests, 30000);
    return () => clearInterval(interval);
  }, []);

  const startTest = async (testId) => {
    try {
      const res = await api.post(`/student/tests/${testId}/start`);
      navigate(`/take-test/${res.data.attempt.attempt_id}`, { state: { attempt: res.data.attempt, test: res.data.test } });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start test');
    }
  };

  const viewResults = (attemptId) => {
    navigate(`/test-results/${attemptId}`);
  };

  const formatDate = (dt) => {
    if (!dt) return '';
    return new Date(dt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6" data-testid="assigned-tests-page">
      <h1 className="text-2xl font-bold text-slate-900">Assigned Tests</h1>

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading tests...</div>
      ) : tests.length === 0 ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="py-16 text-center">
            <FileEdit className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No tests assigned yet</p>
            <p className="text-sm text-slate-400 mt-1">Your teacher will assign tests for your batch soon.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {tests.map((test) => {
            const isSubmitted = test.attempt_status === 'submitted';
            const isInProgress = test.attempt_status === 'in_progress';
            return (
              <Card key={test.test_id} className="border-0 shadow-sm hover:shadow-md transition-shadow" data-testid={`assigned-test-${test.test_id}`}>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-slate-900">{test.test_name}</h3>
                      <div className="flex flex-wrap gap-3 text-sm text-slate-500 mt-1">
                        <span>{test.subject}</span>
                        <span>{test.test_type}</span>
                        <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{test.duration} min</span>
                        <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{formatDate(test.scheduled_date_time)}</span>
                        <span>{test.total_questions} Q</span>
                        {test.test_pattern && (
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${test.test_pattern === 'JEE_Advanced_Pattern' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'}`}>
                            {test.test_pattern === 'JEE_Advanced_Pattern' ? 'JEE Advanced' : 'JEE Main'}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="ml-4 shrink-0">
                      {isSubmitted ? (
                        <div className="text-right">
                          <p className="text-sm font-semibold text-green-600">Score: {test.attempt_score}</p>
                          <Button size="sm" variant="outline" className="mt-1" onClick={() => viewResults(test.attempt_id)} data-testid={`view-results-${test.test_id}`}>
                            <Eye className="h-3.5 w-3.5 mr-1" /> View Results
                          </Button>
                        </div>
                      ) : isInProgress ? (
                        <Button size="sm" className="bg-amber-500 hover:bg-amber-600" onClick={() => startTest(test.test_id)}>
                          <Play className="h-3.5 w-3.5 mr-1" /> Continue
                        </Button>
                      ) : (
                        <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700" onClick={() => startTest(test.test_id)} data-testid={`start-test-${test.test_id}`}>
                          <Play className="h-3.5 w-3.5 mr-1" /> Start Test
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AssignedTests;
