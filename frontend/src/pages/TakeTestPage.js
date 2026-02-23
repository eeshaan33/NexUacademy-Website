import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { 
  Clock, ChevronLeft, ChevronRight, Flag, Check, 
  AlertCircle, CheckCircle, XCircle, ArrowLeft
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { useNavigate, useParams } from 'react-router-dom';

const TakeTestPage = () => {
  const navigate = useNavigate();
  const { testId } = useParams();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [test, setTest] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [flagged, setFlagged] = useState({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [startTime] = useState(Date.now());
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState(null);

  useEffect(() => {
    fetchTest();
  }, [testId]);

  const fetchTest = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/custom-tests/${testId}/questions`);
      setQuestions(response.data.questions || []);
      setTimeLeft((response.data.duration || 180) * 60); // Convert to seconds
      
      // Also get test info
      const testInfo = await api.get(`/custom-tests/${testId}`);
      setTest(testInfo.data);
    } catch (error) {
      console.error('Error fetching test:', error);
      toast.error('Failed to load test');
      navigate('/tests/my-tests');
    } finally {
      setLoading(false);
    }
  };

  // Timer
  useEffect(() => {
    if (timeLeft <= 0 || showResults) return;
    
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [timeLeft, showResults]);

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerSelect = (option) => {
    setAnswers(prev => ({
      ...prev,
      [questions[currentQuestion].questionNumber]: option
    }));
  };

  const handleFlagToggle = () => {
    setFlagged(prev => ({
      ...prev,
      [currentQuestion]: !prev[currentQuestion]
    }));
  };

  const handleSubmit = async () => {
    if (submitting) return;
    
    const unanswered = questions.filter(q => !answers[q.questionNumber]).length;
    
    if (unanswered > 0 && timeLeft > 0) {
      const confirm = window.confirm(
        `You have ${unanswered} unanswered questions. Are you sure you want to submit?`
      );
      if (!confirm) return;
    }
    
    setSubmitting(true);
    
    try {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      
      const response = await api.post(`/custom-tests/${testId}/submit`, {
        answers,
        timeSpent
      });
      
      if (response.data.success) {
        setResults(response.data);
        setShowResults(true);
        toast.success('Test submitted successfully!');
      }
    } catch (error) {
      console.error('Error submitting test:', error);
      toast.error('Failed to submit test');
    } finally {
      setSubmitting(false);
    }
  };

  const getQuestionStatus = (index) => {
    const qNum = questions[index]?.questionNumber;
    if (answers[qNum]) return 'answered';
    if (flagged[index]) return 'flagged';
    return 'unattempted';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (showResults && results) {
    return <TestResults results={results} questions={questions} answers={answers} onBack={() => navigate('/tests/my-tests')} />;
  }

  const currentQ = questions[currentQuestion];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-bold text-gray-800">
                {test?.test_name || 'Custom Test'}
              </h1>
              <p className="text-sm text-gray-600">
                Question {currentQuestion + 1} of {questions.length}
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Timer */}
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono font-bold ${
                timeLeft < 300 ? 'bg-red-100 text-red-700' : 'bg-indigo-100 text-indigo-700'
              }`}>
                <Clock className="w-5 h-5" />
                {formatTime(timeLeft)}
              </div>
              
              <Button
                onClick={handleSubmit}
                disabled={submitting}
                className="bg-green-600 hover:bg-green-700"
                data-testid="submit-test-btn"
              >
                {submitting ? 'Submitting...' : 'Submit Test'}
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Question Panel */}
          <div className="lg:col-span-3">
            <Card>
              <CardContent className="p-6">
                {/* Question Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary">
                      Q{currentQ?.questionNumber}
                    </Badge>
                    <Badge className={
                      currentQ?.subject === 'Physics' ? 'bg-blue-100 text-blue-700' :
                      currentQ?.subject === 'Chemistry' ? 'bg-green-100 text-green-700' :
                      'bg-red-100 text-red-700'
                    }>
                      {currentQ?.subject}
                    </Badge>
                    <Badge variant="outline">{currentQ?.marks || 4} marks</Badge>
                  </div>
                  
                  <Button
                    variant={flagged[currentQuestion] ? 'default' : 'outline'}
                    size="sm"
                    onClick={handleFlagToggle}
                  >
                    <Flag className={`w-4 h-4 mr-2 ${flagged[currentQuestion] ? 'fill-current' : ''}`} />
                    {flagged[currentQuestion] ? 'Flagged' : 'Flag'}
                  </Button>
                </div>
                
                {/* Question Text */}
                <div className="mb-8">
                  <p className="text-lg text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {currentQ?.questionText}
                  </p>
                </div>
                
                {/* Options */}
                {currentQ?.questionType === 'MCQ' && currentQ?.options && (
                  <div className="space-y-3 mb-8">
                    {['A', 'B', 'C', 'D'].map(opt => {
                      const isSelected = answers[currentQ.questionNumber] === opt;
                      const optionText = currentQ.options[opt];
                      
                      if (!optionText) return null;
                      
                      return (
                        <button
                          key={opt}
                          onClick={() => handleAnswerSelect(opt)}
                          className={`w-full p-4 rounded-lg border-2 text-left transition ${
                            isSelected
                              ? 'border-indigo-500 bg-indigo-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                          data-testid={`option-${opt}`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold flex-shrink-0 ${
                              isSelected
                                ? 'bg-indigo-600 border-indigo-600 text-white'
                                : 'border-gray-300 text-gray-600'
                            }`}>
                              {opt}
                            </div>
                            <span className="text-gray-800 pt-1">{optionText}</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
                
                {/* Numerical Input */}
                {currentQ?.questionType === 'Numerical' && (
                  <div className="mb-8">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Enter your answer:
                    </label>
                    <input
                      type="text"
                      value={answers[currentQ.questionNumber] || ''}
                      onChange={(e) => handleAnswerSelect(e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-500 outline-none text-lg"
                      placeholder="Enter numerical value"
                    />
                  </div>
                )}
                
                {/* Navigation */}
                <div className="flex justify-between">
                  <Button
                    variant="outline"
                    onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                    disabled={currentQuestion === 0}
                  >
                    <ChevronLeft className="w-5 h-5 mr-2" />
                    Previous
                  </Button>
                  
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setAnswers(prev => {
                          const newAnswers = { ...prev };
                          delete newAnswers[currentQ.questionNumber];
                          return newAnswers;
                        });
                      }}
                    >
                      Clear
                    </Button>
                    
                    <Button
                      onClick={() => setCurrentQuestion(prev => Math.min(questions.length - 1, prev + 1))}
                      disabled={currentQuestion === questions.length - 1}
                    >
                      Next
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* Question Palette */}
          <div>
            <Card className="sticky top-24">
              <CardContent className="p-4">
                <h3 className="font-bold text-gray-800 mb-4">Question Palette</h3>
                
                {/* Legend */}
                <div className="flex flex-wrap gap-2 mb-4 text-xs">
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 rounded bg-green-500"></div>
                    <span>Answered</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 rounded bg-orange-500"></div>
                    <span>Flagged</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 rounded bg-gray-300"></div>
                    <span>Not visited</span>
                  </div>
                </div>
                
                {/* Question Grid */}
                <div className="grid grid-cols-5 gap-2">
                  {questions.map((q, index) => {
                    const status = getQuestionStatus(index);
                    return (
                      <button
                        key={index}
                        onClick={() => setCurrentQuestion(index)}
                        className={`w-10 h-10 rounded-lg font-medium text-sm transition ${
                          index === currentQuestion
                            ? 'ring-2 ring-indigo-500 ring-offset-2'
                            : ''
                        } ${
                          status === 'answered'
                            ? 'bg-green-500 text-white'
                            : status === 'flagged'
                            ? 'bg-orange-500 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {index + 1}
                      </button>
                    );
                  })}
                </div>
                
                {/* Stats */}
                <div className="mt-6 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Answered:</span>
                    <span className="font-medium text-green-600">
                      {Object.keys(answers).length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Flagged:</span>
                    <span className="font-medium text-orange-600">
                      {Object.values(flagged).filter(Boolean).length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Remaining:</span>
                    <span className="font-medium text-gray-800">
                      {questions.length - Object.keys(answers).length}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          
        </div>
      </div>
    </div>
  );
};

// Test Results Component
const TestResults = ({ results, questions, answers, onBack }) => {
  const { correct, incorrect, unattempted, totalMarks, maxMarks, percentage, accuracy, timeSpent } = results.results;
  const questionResults = results.questionResults || [];

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 p-4 sm:p-6">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-block p-4 bg-white rounded-full shadow-lg mb-4">
            {percentage >= 60 ? (
              <CheckCircle className="w-16 h-16 text-green-500" />
            ) : (
              <AlertCircle className="w-16 h-16 text-orange-500" />
            )}
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Test Completed!</h1>
          <p className="text-gray-600">Here's how you performed</p>
        </div>
        
        {/* Score Card */}
        <Card className="mb-8 overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-8 text-white text-center">
            <p className="text-lg opacity-90 mb-2">Your Score</p>
            <p className="text-6xl font-bold mb-2">{totalMarks}</p>
            <p className="text-lg opacity-90">out of {maxMarks} marks</p>
          </div>
          
          <CardContent className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-green-600">{correct}</p>
                <p className="text-sm text-gray-600">Correct</p>
              </div>
              
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <XCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-red-600">{incorrect}</p>
                <p className="text-sm text-gray-600">Incorrect</p>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <AlertCircle className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-600">{unattempted}</p>
                <p className="text-sm text-gray-600">Skipped</p>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Clock className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-blue-600">{formatTime(timeSpent)}</p>
                <p className="text-sm text-gray-600">Time Taken</p>
              </div>
            </div>
            
            <div className="mt-6 grid grid-cols-2 gap-4">
              <div className="bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg p-4 text-white">
                <p className="text-sm opacity-90">Percentage</p>
                <p className="text-3xl font-bold">{percentage}%</p>
              </div>
              <div className="bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg p-4 text-white">
                <p className="text-sm opacity-90">Accuracy</p>
                <p className="text-3xl font-bold">{accuracy}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Question-wise Results */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Question-wise Analysis</h3>
            
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {questionResults.map((qr, index) => {
                const q = questions.find(q => q.questionNumber === qr.questionNumber);
                return (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border-2 ${
                      qr.status === 'correct'
                        ? 'border-green-200 bg-green-50'
                        : qr.status === 'incorrect'
                        ? 'border-red-200 bg-red-50'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                          qr.status === 'correct'
                            ? 'bg-green-500 text-white'
                            : qr.status === 'incorrect'
                            ? 'bg-red-500 text-white'
                            : 'bg-gray-400 text-white'
                        }`}>
                          {qr.questionNumber}
                        </div>
                        <div>
                          <p className="font-medium text-gray-800 line-clamp-1">
                            {q?.questionText?.substring(0, 80)}...
                          </p>
                          <p className="text-sm text-gray-600">
                            {q?.subject} • {q?.chapter}
                          </p>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <p className={`font-bold ${
                          qr.marks > 0 ? 'text-green-600' : qr.marks < 0 ? 'text-red-600' : 'text-gray-400'
                        }`}>
                          {qr.marks > 0 ? '+' : ''}{qr.marks}
                        </p>
                        <p className="text-xs text-gray-500">
                          Your: {qr.userAnswer || '-'} | Correct: {qr.correctAnswer}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
        
        {/* Actions */}
        <div className="flex justify-center gap-4">
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to My Tests
          </Button>
          <Button onClick={() => window.location.reload()}>
            Retake Test
          </Button>
        </div>
        
      </div>
    </div>
  );
};

export default TakeTestPage;
