import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { 
  ChevronRight, ChevronLeft, ChevronDown, Save, Play, Clock, 
  FileText, Trash2, Star, Calendar, BookOpen, Search, X, 
  ArrowLeft, Check, AlertCircle
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

// Subject colors
const subjectColors = {
  Physics: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-400', gradient: 'from-blue-500 to-blue-600' },
  Chemistry: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-400', gradient: 'from-green-500 to-green-600' },
  Mathematics: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-400', gradient: 'from-red-500 to-red-600' }
};

const MyTestsPage = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [savedTemplates, setSavedTemplates] = useState([]);
  
  // Test Configuration State
  const [examType, setExamType] = useState('');
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [yearRange, setYearRange] = useState({ start: 2020, end: 2025 });
  const [duration, setDuration] = useState(180);
  
  // Syllabus data
  const [syllabus, setSyllabus] = useState(null);
  const [questionCounts, setQuestionCounts] = useState({});
  
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [syllabusRes, templatesRes] = await Promise.all([
        api.get('/custom-tests/syllabus'),
        api.get('/test-templates').catch(() => ({ data: [] }))
      ]);
      
      setSyllabus(syllabusRes.data);
      setSavedTemplates(templatesRes.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestionCounts = useCallback(async () => {
    try {
      const res = await api.get('/custom-tests/question-counts', {
        params: { examType: examType || undefined }
      });
      setQuestionCounts(res.data);
    } catch (error) {
      console.error('Error fetching counts:', error);
    }
  }, [examType]);

  useEffect(() => {
    if (examType) {
      fetchQuestionCounts();
    }
  }, [examType, fetchQuestionCounts]);

  const handleLoadTemplate = (template) => {
    setExamType(template.exam_type);
    setSelectedTopics(template.selected_topics.map(t => ({
      subject: t.subject,
      chapter: t.chapter,
      topic: t.topic,
      questionCount: t.questionCount,
      difficulty: t.difficulty || 'Mixed'
    })));
    setYearRange({ start: template.year_range.start, end: template.year_range.end });
    setDuration(template.duration);
    setStep(4);
    toast.success('Template loaded');
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Delete this template?')) return;
    
    try {
      await api.delete(`/test-templates/${templateId}`);
      setSavedTemplates(prev => prev.filter(t => t.template_id !== templateId));
      toast.success('Template deleted');
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const calculateTotals = () => {
    const totals = {
      questions: 0,
      marks: 0,
      Physics: { questions: 0, marks: 0 },
      Chemistry: { questions: 0, marks: 0 },
      Mathematics: { questions: 0, marks: 0 }
    };
    
    selectedTopics.forEach(topic => {
      const marks = topic.questionCount * 4;
      totals.questions += topic.questionCount;
      totals.marks += marks;
      if (totals[topic.subject]) {
        totals[topic.subject].questions += topic.questionCount;
        totals[topic.subject].marks += marks;
      }
    });
    
    return totals;
  };

  const handleSaveTemplate = async () => {
    const name = window.prompt('Enter template name:', 'My Test Template');
    if (!name) return;
    
    try {
      const totals = calculateTotals();
      
      await api.post('/test-templates', {
        templateName: name,
        examType,
        selectedTopics: selectedTopics.map(t => ({
          subject: t.subject,
          chapter: t.chapter,
          topic: t.topic,
          questionCount: t.questionCount,
          difficulty: t.difficulty
        })),
        yearRange: yearRange,
        duration,
        totalQuestions: totals.questions,
        totalMarks: totals.marks,
        subjectBreakdown: {
          Physics: totals.Physics,
          Chemistry: totals.Chemistry,
          Mathematics: totals.Mathematics
        }
      });
      
      toast.success('Template saved successfully!');
      fetchInitialData();
    } catch (error) {
      toast.error('Failed to save template');
    }
  };

  const handleGenerateTest = async () => {
    setGenerating(true);
    
    try {
      const totals = calculateTotals();
      
      const response = await api.post('/custom-tests/generate', {
        examType,
        selectedTopics: selectedTopics.map(t => ({
          subject: t.subject,
          chapter: t.chapter,
          topic: t.topic,
          questionCount: t.questionCount,
          difficulty: t.difficulty
        })),
        yearRange: yearRange,
        duration,
        totalQuestions: totals.questions,
        totalMarks: totals.marks
      });
      
      if (response.data.success) {
        toast.success(response.data.message);
        // Navigate to take test
        navigate(`/test/${response.data.test_id}/take`);
      }
    } catch (error) {
      const msg = error.response?.data?.detail || 'Failed to generate test';
      toast.error(msg);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 p-4 sm:p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
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
              🎯 Create Custom Test
            </h1>
            <p className="text-gray-600 mt-1">
              Build your personalized practice test by selecting topics and settings
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Builder Panel */}
          <div className="lg:col-span-2">
            
            {/* Progress Steps */}
            <Card className="mb-6">
              <CardContent className="p-4 sm:p-6">
                <div className="flex items-center justify-between overflow-x-auto">
                  {[
                    { num: 1, title: 'Exam Type' },
                    { num: 2, title: 'Select Topics' },
                    { num: 3, title: 'Configure' },
                    { num: 4, title: 'Preview' }
                  ].map((s, index) => (
                    <div key={s.num} className="flex items-center flex-shrink-0">
                      <div className="flex items-center">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition ${
                          step >= s.num 
                            ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white' 
                            : 'bg-gray-200 text-gray-500'
                        }`}>
                          {step > s.num ? <Check className="w-5 h-5" /> : s.num}
                        </div>
                        <span className={`ml-2 font-medium hidden sm:block ${
                          step >= s.num ? 'text-gray-800' : 'text-gray-400'
                        }`}>
                          {s.title}
                        </span>
                      </div>
                      {index < 3 && (
                        <ChevronRight className="w-6 h-6 text-gray-300 mx-2" />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            
            {/* Step Content */}
            <Card>
              <CardContent className="p-6 sm:p-8">
                
                {/* Step 1: Exam Type Selection */}
                {step === 1 && (
                  <Step1ExamType 
                    examType={examType}
                    setExamType={setExamType}
                    onNext={() => setStep(2)}
                  />
                )}
                
                {/* Step 2: Topic Selection */}
                {step === 2 && (
                  <Step2TopicSelection
                    syllabus={syllabus}
                    selectedTopics={selectedTopics}
                    setSelectedTopics={setSelectedTopics}
                    questionCounts={questionCounts}
                    onNext={() => setStep(3)}
                    onBack={() => setStep(1)}
                  />
                )}
                
                {/* Step 3: Configuration */}
                {step === 3 && (
                  <Step3Configuration
                    selectedTopics={selectedTopics}
                    setSelectedTopics={setSelectedTopics}
                    yearRange={yearRange}
                    setYearRange={setYearRange}
                    duration={duration}
                    setDuration={setDuration}
                    onNext={() => setStep(4)}
                    onBack={() => setStep(2)}
                  />
                )}
                
                {/* Step 4: Preview & Generate */}
                {step === 4 && (
                  <Step4Preview
                    examType={examType}
                    selectedTopics={selectedTopics}
                    yearRange={yearRange}
                    duration={duration}
                    calculateTotals={calculateTotals}
                    onSave={handleSaveTemplate}
                    onGenerate={handleGenerateTest}
                    onBack={() => setStep(3)}
                    generating={generating}
                  />
                )}
                
              </CardContent>
            </Card>
          </div>
          
          {/* Sidebar - Saved Templates & Summary */}
          <div className="space-y-6">
            
            {/* Saved Templates */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Save className="w-5 h-5" />
                  Saved Templates
                </CardTitle>
              </CardHeader>
              <CardContent>
                {savedTemplates.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No saved templates yet</p>
                    <p className="text-xs mt-1">Save your test configurations for quick access</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {savedTemplates.map(template => (
                      <TemplateCard
                        key={template.template_id}
                        template={template}
                        onLoad={() => handleLoadTemplate(template)}
                        onDelete={() => handleDeleteTemplate(template.template_id)}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* Quick Stats (when in preview) */}
            {step === 4 && selectedTopics.length > 0 && (
              <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-md p-6 text-white">
                <h3 className="text-lg font-bold mb-4">Test Summary</h3>
                
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="opacity-90">Total Questions:</span>
                    <span className="font-bold">{calculateTotals().questions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="opacity-90">Total Marks:</span>
                    <span className="font-bold">{calculateTotals().marks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="opacity-90">Duration:</span>
                    <span className="font-bold">{duration} mins</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="opacity-90">Avg per Question:</span>
                    <span className="font-bold">
                      {calculateTotals().questions > 0 
                        ? Math.floor(duration / calculateTotals().questions) 
                        : 0} mins
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
          
        </div>
      </div>
    </div>
  );
};

// Step 1: Exam Type Selection
const Step1ExamType = ({ examType, setExamType, onNext }) => {
  const examTypes = [
    { 
      value: 'JEE_Main', 
      title: 'JEE Main', 
      desc: 'National level entrance exam',
      icon: '📘',
      color: 'from-blue-500 to-blue-600'
    },
    { 
      value: 'JEE_Advanced', 
      title: 'JEE Advanced', 
      desc: 'IIT entrance examination',
      icon: '🎓',
      color: 'from-purple-500 to-purple-600'
    },
    { 
      value: 'Mixed', 
      title: 'Mixed Practice', 
      desc: 'Questions from both exams',
      icon: '🔀',
      color: 'from-green-500 to-green-600'
    }
  ];

  return (
    <div className="text-center">
      <h2 className="text-2xl font-bold text-gray-800 mb-3">Select Exam Type</h2>
      <p className="text-gray-600 mb-8">Choose the exam pattern for your custom test</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {examTypes.map(type => (
          <button
            key={type.value}
            onClick={() => setExamType(type.value)}
            className={`p-6 rounded-xl border-2 transition transform hover:scale-105 ${
              examType === type.value
                ? `bg-gradient-to-br ${type.color} text-white border-transparent shadow-xl`
                : 'bg-white border-gray-200 hover:border-gray-300'
            }`}
            data-testid={`exam-type-${type.value}`}
          >
            <div className="text-5xl mb-3">{type.icon}</div>
            <h3 className="text-xl font-bold mb-2">{type.title}</h3>
            <p className={`text-sm ${examType === type.value ? 'text-white/90' : 'text-gray-500'}`}>
              {type.desc}
            </p>
          </button>
        ))}
      </div>
      
      <Button
        onClick={onNext}
        disabled={!examType}
        className="px-8"
        data-testid="continue-to-topics-btn"
      >
        Continue to Topic Selection
        <ChevronRight className="w-5 h-5 ml-2" />
      </Button>
    </div>
  );
};

// Step 2: Topic Selection
const Step2TopicSelection = ({ 
  syllabus, selectedTopics, setSelectedTopics, 
  questionCounts, onNext, onBack 
}) => {
  const [expandedSubject, setExpandedSubject] = useState('Physics');
  const [expandedChapter, setExpandedChapter] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleTopicToggle = (subject, chapter, topic) => {
    const existing = selectedTopics.find(
      t => t.subject === subject && t.chapter === chapter && t.topic === topic
    );
    
    if (existing) {
      setSelectedTopics(selectedTopics.filter(t => t !== existing));
    } else {
      setSelectedTopics([
        ...selectedTopics,
        {
          subject,
          chapter,
          topic,
          questionCount: 5,
          difficulty: 'Mixed'
        }
      ]);
    }
  };

  const isTopicSelected = (subject, chapter, topic) => {
    return selectedTopics.some(
      t => t.subject === subject && t.chapter === chapter && t.topic === topic
    );
  };

  const getAvailableCount = (subject, chapter, topic) => {
    const key = `${subject}-${chapter}-${topic}`;
    return questionCounts[key] || 0;
  };

  const subjects = ['Physics', 'Chemistry', 'Mathematics'];

  const getAllChapters = (subject) => {
    if (!syllabus || !syllabus[subject]) return [];
    const class11 = syllabus[subject].Class11 || [];
    const class12 = syllabus[subject].Class12 || [];
    return [...class11, ...class12];
  };

  const filteredChapters = (subject) => {
    return getAllChapters(subject).filter(chap => 
      searchQuery === '' || 
      chap.chapter.toLowerCase().includes(searchQuery.toLowerCase()) ||
      chap.topics.some(t => t && t.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-3">Select Topics</h2>
      <p className="text-gray-600 mb-6">Choose topics across subjects for your custom test</p>
      
      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <Input
          type="text"
          placeholder="Search chapters or topics..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>
      
      {/* Selected Topics Summary */}
      {selectedTopics.length > 0 && (
        <div className="bg-indigo-50 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-indigo-900">
              Selected: {selectedTopics.length} topics
            </span>
            <button
              onClick={() => setSelectedTopics([])}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Clear All
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedTopics.slice(0, 5).map((topic, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="bg-white"
              >
                {topic.subject}: {topic.topic}
                <button
                  onClick={() => handleTopicToggle(topic.subject, topic.chapter, topic.topic)}
                  className="ml-2 text-red-500 hover:text-red-700"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            ))}
            {selectedTopics.length > 5 && (
              <Badge variant="secondary">+{selectedTopics.length - 5} more</Badge>
            )}
          </div>
        </div>
      )}
      
      {/* Subject Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {subjects.map(subject => {
          const colors = subjectColors[subject];
          return (
            <button
              key={subject}
              onClick={() => setExpandedSubject(subject)}
              className={`px-6 py-3 rounded-lg font-medium transition flex-shrink-0 ${
                expandedSubject === subject
                  ? `bg-gradient-to-r ${colors.gradient} text-white`
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {subject}
            </button>
          );
        })}
      </div>
      
      {/* Chapters & Topics */}
      <div className="space-y-3 mb-6 max-h-[400px] overflow-y-auto">
        {filteredChapters(expandedSubject).map((chapter, chIndex) => (
          <div key={chIndex} className="border border-gray-200 rounded-lg overflow-hidden">
            
            {/* Chapter Header */}
            <button
              onClick={() => setExpandedChapter(expandedChapter === chapter.chapter ? null : chapter.chapter)}
              className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-800">{chapter.chapter}</span>
                <Badge variant="secondary" className="text-xs">
                  {chapter.questionCount} questions
                </Badge>
              </div>
              <ChevronDown 
                className={`w-5 h-5 text-gray-500 transition ${
                  expandedChapter === chapter.chapter ? 'rotate-180' : ''
                }`}
              />
            </button>
            
            {/* Topics */}
            {expandedChapter === chapter.chapter && (
              <div className="p-4 space-y-2">
                {chapter.topics.filter(t => t).map((topic, tIndex) => {
                  const selected = isTopicSelected(expandedSubject, chapter.chapter, topic);
                  const available = getAvailableCount(expandedSubject, chapter.chapter, topic);
                  
                  return (
                    <div
                      key={tIndex}
                      onClick={() => handleTopicToggle(expandedSubject, chapter.chapter, topic)}
                      className={`flex items-center justify-between p-3 rounded-lg border-2 transition cursor-pointer ${
                        selected
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                          selected ? 'bg-indigo-600 border-indigo-600' : 'border-gray-300'
                        }`}>
                          {selected && <Check className="w-3 h-3 text-white" />}
                        </div>
                        <span className="text-gray-800">{topic}</span>
                      </div>
                      <Badge variant={available > 0 ? 'default' : 'destructive'} className="text-xs">
                        {available} available
                      </Badge>
                    </div>
                  );
                })}
              </div>
            )}
            
          </div>
        ))}
      </div>
      
      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ChevronLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        
        <Button
          onClick={onNext}
          disabled={selectedTopics.length === 0}
          data-testid="continue-to-config-btn"
        >
          Configure Test
          <ChevronRight className="w-5 h-5 ml-2" />
        </Button>
      </div>
    </div>
  );
};

// Step 3: Configuration
const Step3Configuration = ({ 
  selectedTopics, setSelectedTopics, yearRange, setYearRange, 
  duration, setDuration, onNext, onBack 
}) => {
  
  const handleQuestionCountChange = (index, value) => {
    const newTopics = [...selectedTopics];
    newTopics[index].questionCount = Math.max(1, Math.min(50, parseInt(value) || 1));
    setSelectedTopics(newTopics);
  };

  const handleDifficultyChange = (index, difficulty) => {
    const newTopics = [...selectedTopics];
    newTopics[index].difficulty = difficulty;
    setSelectedTopics(newTopics);
  };

  const handleRemoveTopic = (index) => {
    setSelectedTopics(selectedTopics.filter((_, i) => i !== index));
  };

  const totalQuestions = selectedTopics.reduce((sum, t) => sum + t.questionCount, 0);
  const recommendedDuration = Math.ceil(totalQuestions * 3);

  const years = Array.from({ length: 16 }, (_, i) => 2010 + i);

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-3">Configure Test Settings</h2>
      <p className="text-gray-600 mb-6">Set question counts and test parameters</p>
      
      {/* Question Configuration Table */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Question Distribution</h3>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Subject</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Topic</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Questions</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Difficulty</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Marks</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {selectedTopics.map((topic, index) => {
                const colors = subjectColors[topic.subject];
                return (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">
                      <Badge className={`${colors.bg} ${colors.text}`}>
                        {topic.subject}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-800">
                      {topic.topic}
                    </td>
                    <td className="px-4 py-3">
                      <Input
                        type="number"
                        value={topic.questionCount}
                        onChange={(e) => handleQuestionCountChange(index, e.target.value)}
                        min="1"
                        max="50"
                        className="w-20"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={topic.difficulty}
                        onChange={(e) => handleDifficultyChange(index, e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:border-indigo-500 outline-none text-sm"
                      >
                        <option value="Mixed">Mixed</option>
                        <option value="Easy">Easy</option>
                        <option value="Medium">Medium</option>
                        <option value="Hard">Hard</option>
                      </select>
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-800">
                      {topic.questionCount * 4}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleRemoveTopic(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Year Range */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Year Range</h3>
        <p className="text-sm text-gray-600 mb-4">
          Select the year span from which questions will be chosen
        </p>
        
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">From Year</label>
            <select
              value={yearRange.start}
              onChange={(e) => setYearRange({ ...yearRange, start: parseInt(e.target.value) })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-indigo-500 outline-none"
            >
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
          
          <span className="text-2xl text-gray-400 mt-8">→</span>
          
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">To Year</label>
            <select
              value={yearRange.end}
              onChange={(e) => setYearRange({ ...yearRange, end: parseInt(e.target.value) })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-indigo-500 outline-none"
            >
              {years.filter(year => year >= yearRange.start).map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      {/* Duration */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Test Duration</h3>
        
        <div className="flex items-center gap-6">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Duration (minutes)
            </label>
            <Input
              type="number"
              value={duration}
              onChange={(e) => setDuration(Math.max(15, parseInt(e.target.value) || 15))}
              min="15"
              step="5"
              className="text-lg font-medium"
            />
          </div>
          
          <div className="flex-1 bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-900 mb-1">
              ⏱️ Recommended Duration
            </p>
            <p className="text-2xl font-bold text-blue-600">
              {recommendedDuration} minutes
            </p>
            <p className="text-xs text-blue-700 mt-1">
              Based on 3 mins per question
            </p>
          </div>
        </div>
        
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <span>Time per question: {totalQuestions > 0 ? Math.floor(duration / totalQuestions) : 0} minutes</span>
          <span>Total Questions: {totalQuestions}</span>
        </div>
      </div>
      
      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ChevronLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        
        <Button onClick={onNext} data-testid="preview-test-btn">
          Preview Test
          <ChevronRight className="w-5 h-5 ml-2" />
        </Button>
      </div>
    </div>
  );
};

// Step 4: Preview & Generate
const Step4Preview = ({ 
  examType, selectedTopics, yearRange, duration, 
  calculateTotals, onSave, onGenerate, onBack, generating 
}) => {
  const totals = calculateTotals();
  
  const groupedBySubject = {
    Physics: selectedTopics.filter(t => t.subject === 'Physics'),
    Chemistry: selectedTopics.filter(t => t.subject === 'Chemistry'),
    Mathematics: selectedTopics.filter(t => t.subject === 'Mathematics')
  };

  const examTypeLabels = {
    'JEE_Main': 'JEE Main',
    'JEE_Advanced': 'JEE Advanced',
    'Mixed': 'Mixed Practice'
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-3">Test Preview</h2>
      <p className="text-gray-600 mb-6">Review your test configuration before generating</p>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-4 text-white">
          <p className="text-sm opacity-90 mb-1">Total Questions</p>
          <p className="text-3xl font-bold">{totals.questions}</p>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-4 text-white">
          <p className="text-sm opacity-90 mb-1">Total Marks</p>
          <p className="text-3xl font-bold">{totals.marks}</p>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-4 text-white">
          <p className="text-sm opacity-90 mb-1">Duration</p>
          <p className="text-3xl font-bold">{duration}</p>
          <p className="text-xs opacity-75">minutes</p>
        </div>
        
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg p-4 text-white">
          <p className="text-sm opacity-90 mb-1">Year Range</p>
          <p className="text-xl font-bold">{yearRange.start} - {yearRange.end}</p>
        </div>
      </div>
      
      {/* Subject-wise Breakdown */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Subject-wise Distribution</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {['Physics', 'Chemistry', 'Mathematics'].map(subject => {
            const colors = subjectColors[subject];
            return (
              <div key={subject} className={`bg-white border-2 ${colors.border} rounded-lg p-4`}>
                <h4 className={`font-bold ${colors.text} mb-3`}>{subject}</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Questions:</span>
                    <span className="font-bold">{totals[subject].questions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Marks:</span>
                    <span className="font-bold">{totals[subject].marks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Topics:</span>
                    <span className="font-bold">{groupedBySubject[subject].length}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Test Settings */}
      <div className="bg-blue-50 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-bold text-gray-800 mb-3">Test Settings</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Exam Type:</span>
            <span className="ml-2 font-medium text-gray-800">{examTypeLabels[examType]}</span>
          </div>
          <div>
            <span className="text-gray-600">Negative Marking:</span>
            <span className="ml-2 font-medium text-gray-800">Yes (-1 for wrong)</span>
          </div>
          <div>
            <span className="text-gray-600">Question Order:</span>
            <span className="ml-2 font-medium text-gray-800">Random</span>
          </div>
          <div>
            <span className="text-gray-600">Solutions:</span>
            <span className="ml-2 font-medium text-gray-800">Available after submission</span>
          </div>
        </div>
      </div>
      
      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-4">
        <Button variant="outline" onClick={onBack} className="sm:flex-none">
          <ChevronLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        
        <Button
          variant="outline"
          onClick={onSave}
          className="flex-1"
        >
          <Save className="w-5 h-5 mr-2" />
          Save Template
        </Button>
        
        <Button
          onClick={onGenerate}
          disabled={generating}
          className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
          data-testid="generate-test-btn"
        >
          {generating ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-white mr-2" />
              Generating...
            </>
          ) : (
            <>
              <Play className="w-5 h-5 mr-2" />
              Generate & Start Test
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

// Template Card Component
const TemplateCard = ({ template, onLoad, onDelete }) => {
  return (
    <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-bold text-gray-800 mb-1">{template.template_name}</h4>
          <p className="text-xs text-gray-500">{template.exam_type}</p>
        </div>
        <button
          onClick={onDelete}
          className="text-red-500 hover:text-red-700"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
      
      <div className="space-y-1 text-sm mb-3">
        <div className="flex justify-between text-gray-600">
          <span>Questions:</span>
          <span className="font-medium">{template.total_questions}</span>
        </div>
        <div className="flex justify-between text-gray-600">
          <span>Duration:</span>
          <span className="font-medium">{template.duration} mins</span>
        </div>
        <div className="flex justify-between text-gray-600">
          <span>Topics:</span>
          <span className="font-medium">{template.selected_topics?.length || 0}</span>
        </div>
      </div>
      
      <Button
        onClick={onLoad}
        className="w-full"
        size="sm"
      >
        Load Template
      </Button>
    </div>
  );
};

export default MyTestsPage;
