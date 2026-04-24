import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  BookOpen, ChevronRight, Award, Target, ArrowLeft, Search, 
  Calendar, CheckCircle, XCircle, List, Filter, X, Bookmark, BookmarkCheck
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

import { setPageTitle } from '../utils/pageTitle';

const PYQSection = () => {
  // Navigation state
  const [step, setStep] = useState(1);

  useEffect(() => {
    setPageTitle('PYQ Section');
  }, []);
  const [examType, setExamType] = useState('');
  const [subject, setSubject] = useState('');
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [practiceType, setPracticeType] = useState('');
  const [selectedTopic, setSelectedTopic] = useState(null);
  
  // Data state
  const [syllabus, setSyllabus] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [allQuestions, setAllQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  
  // Question interaction state
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showSolution, setShowSolution] = useState(false);
  const [answeredQuestions, setAnsweredQuestions] = useState({});
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const [yearFilter, setYearFilter] = useState('');
  const [showQuestionList, setShowQuestionList] = useState(false);

  // Bookmark state
  const [bookmarkedIds, setBookmarkedIds] = useState(new Set());
  const [bookmarkBusy, setBookmarkBusy] = useState(false);

  useEffect(() => {
    const loadBookmarkedIds = async () => {
      try {
        const res = await api.get('/bookmarks/ids');
        setBookmarkedIds(new Set(res.data.pyq_question_ids || []));
      } catch { /* ignore */ }
    };
    loadBookmarkedIds();
  }, []);

  const toggleBookmark = async (question) => {
    if (!question?.question_id || bookmarkBusy) return;
    setBookmarkBusy(true);
    const qid = question.question_id;
    const isBookmarked = bookmarkedIds.has(qid);
    try {
      if (isBookmarked) {
        await api.delete(`/bookmarks/by-question`, { params: { source: 'pyq', question_id: qid } });
        const next = new Set(bookmarkedIds); next.delete(qid); setBookmarkedIds(next);
        toast.success('Removed from bookmarks');
      } else {
        await api.post('/bookmarks/', {
          source: 'pyq',
          question_id: qid,
          snapshot: {
            question_text: question.questionText,
            question_image_url: question.questionImageUrl,
            question_type: question.questionType || 'MCQ_Single',
            options: question.options || {},
            correct_answer: question.correctAnswer,
            subject: question.subject,
            chapter: question.chapter,
            topic: question.topic,
            year: question.year,
            difficulty: question.difficulty,
          },
        });
        setBookmarkedIds(new Set(bookmarkedIds).add(qid));
        toast.success('Saved to bookmarks');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to update bookmark');
    } finally {
      setBookmarkBusy(false);
    }
  };
  
  // Available years for filter
  const availableYears = useMemo(() => {
    const years = [...new Set(questions.map(q => q.year))].sort((a, b) => b - a);
    return years;
  }, [questions]);

  // Filtered questions based on year
  const filteredQuestions = useMemo(() => {
    if (!yearFilter) return questions;
    return questions.filter(q => q.year === parseInt(yearFilter));
  }, [questions, yearFilter]);

  // Topics from current chapter
  const chapterTopics = useMemo(() => {
    if (!questions.length) return [];
    const topics = [...new Set(questions.map(q => q.topic).filter(Boolean))];
    return topics;
  }, [questions]);

  useEffect(() => {
    fetchSyllabus();
  }, []);

  // Search effect with debounce
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      setShowSearchDropdown(false);
      return;
    }

    const timeoutId = setTimeout(() => {
      const query = searchQuery.toLowerCase();
      const results = questions.filter(q => 
        q.questionText?.toLowerCase().includes(query) ||
        q.year?.toString().includes(query) ||
        q.topic?.toLowerCase().includes(query)
      ).slice(0, 10);
      
      setSearchResults(results);
      setShowSearchDropdown(results.length > 0);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, questions]);

  const fetchSyllabus = async () => {
    try {
      const response = await api.get('/questions/syllabus');
      setSyllabus(response.data);
    } catch (error) {
      console.error('Failed to fetch syllabus:', error);
      toast.error('Failed to load syllabus');
    }
  };

  const fetchQuestions = async (chapterName) => {
    try {
      // Build params object, only including non-empty values
      const params = { limit: 300 };
      if (subject) params.subject = subject;
      if (chapterName) params.chapter = chapterName;

      const response = await api.get('/questions/', { params });
      const sorted = response.data.questions.sort((a, b) => b.year - a.year);
      setAllQuestions(sorted);
      setQuestions(sorted);
      return sorted;
    } catch (error) {
      console.error('Failed to fetch questions:', error);
      toast.error('Failed to load questions');
      return [];
    }
  };

  const handleExamTypeSelect = (type) => {
    setExamType(type);
    setStep(2);
  };

  const handleSubjectSelect = (subj) => {
    setSubject(subj);
    setStep(3);
  };

  const handleChapterSelect = async (chapter) => {
    setSelectedChapter(chapter);
    await fetchQuestions(chapter.chapter);
    setStep(4);
  };

  const handlePracticeTypeSelect = (type) => {
    setPracticeType(type);
    if (type === 'pyq') {
      // Show question list for PYQ mode
      setStep(5);
    } else {
      // Show topic selection for topic-wise mode
      setStep(5);
    }
  };

  const handleTopicSelect = (topic) => {
    setSelectedTopic(topic);
    const topicQuestions = allQuestions.filter(q => q.topic === topic);
    setQuestions(topicQuestions);
    setStep(6);
  };

  const handleQuestionSelect = (index) => {
    setCurrentQuestionIndex(index);
    setSelectedAnswer(null);
    setShowSolution(false);
    setShowQuestionList(false);
    setSearchQuery('');
    setShowSearchDropdown(false);
    if (step === 5) setStep(6);
  };

  const handleSearchResultClick = (question) => {
    const index = questions.findIndex(q => q.question_id === question.question_id);
    if (index !== -1) {
      handleQuestionSelect(index);
    }
  };

  const handleAnswerSelect = (option) => {
    if (showSolution) return;
    setSelectedAnswer(option);
  };

  const handleSubmitAnswer = async () => {
    if (!selectedAnswer) {
      toast.error('Please select an answer');
      return;
    }

    const currentQ = questions[currentQuestionIndex];
    const isCorrect = selectedAnswer === currentQ.correctAnswer;

    setAnsweredQuestions({
      ...answeredQuestions,
      [currentQuestionIndex]: {
        selected: selectedAnswer,
        correct: isCorrect
      }
    });

    setShowSolution(true);

    // Record the attempt for analytics
    try {
      await api.post('/analytics/record-attempt', {
        question_id: currentQ.question_id,
        selected_answer: selectedAnswer,
        is_correct: isCorrect,
        time_taken: 0
      });
    } catch (error) {
      console.error('Failed to record attempt:', error);
    }

    if (isCorrect) {
      toast.success('Correct! Well done!');
    } else {
      toast.error(`Incorrect. The correct answer is ${currentQ.correctAnswer}`);
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < filteredQuestions.length - 1) {
      const nextIndex = questions.indexOf(filteredQuestions[currentQuestionIndex + 1]);
      setCurrentQuestionIndex(nextIndex);
      setSelectedAnswer(null);
      setShowSolution(false);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setSelectedAnswer(null);
      setShowSolution(false);
    }
  };

  const handleViewSolution = () => {
    const currentQ = questions[currentQuestionIndex];
    if (currentQ.solutionYoutubeUrl) {
      const url = currentQ.solutionTimestamp 
        ? `${currentQ.solutionYoutubeUrl}&t=${currentQ.solutionTimestamp}s`
        : currentQ.solutionYoutubeUrl;
      window.open(url, '_blank');
    } else {
      toast.info('Video solution coming soon!');
    }
  };

  const resetFlow = () => {
    setStep(1);
    setExamType('');
    setSubject('');
    setSelectedChapter(null);
    setPracticeType('');
    setSelectedTopic(null);
    setQuestions([]);
    setAllQuestions([]);
    setCurrentQuestionIndex(0);
    setSelectedAnswer(null);
    setShowSolution(false);
    setAnsweredQuestions({});
    setSearchQuery('');
    setYearFilter('');
    setShowQuestionList(false);
  };

  const goBack = () => {
    if (step === 6 && practiceType === 'topic') {
      setStep(5);
      setSelectedTopic(null);
      setQuestions(allQuestions);
    } else if (step === 6) {
      setStep(5);
    } else if (step === 5) {
      setStep(4);
      setPracticeType('');
    } else if (step === 4) {
      setStep(3);
      setSelectedChapter(null);
    } else if (step === 3) {
      setStep(2);
      setSubject('');
    } else if (step === 2) {
      setStep(1);
      setExamType('');
    }
  };

  // Question List Sidebar Component
  const QuestionListSidebar = () => (
    <div className={`fixed inset-y-0 right-0 w-96 bg-white shadow-2xl transform transition-transform duration-300 z-50 ${showQuestionList ? 'translate-x-0' : 'translate-x-full'}`}>
      <div className="h-full flex flex-col">
        <div className="p-4 border-b flex items-center justify-between bg-gray-50">
          <h3 className="font-semibold text-lg">All Questions ({filteredQuestions.length})</h3>
          <Button variant="ghost" size="sm" onClick={() => setShowQuestionList(false)}>
            <X className="h-5 w-5" />
          </Button>
        </div>
        
        {/* Search in sidebar */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search questions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="sidebar-search-input"
            />
          </div>
          
          {/* Year Filter */}
          <div className="mt-3 flex gap-2 flex-wrap">
            <Badge
              variant={yearFilter === '' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setYearFilter('')}
            >
              All Years
            </Badge>
            {availableYears.slice(0, 5).map(year => (
              <Badge
                key={year}
                variant={yearFilter === year.toString() ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => setYearFilter(yearFilter === year.toString() ? '' : year.toString())}
              >
                {year}
              </Badge>
            ))}
          </div>
        </div>
        
        {/* Questions List */}
        <ScrollArea className="flex-1">
          <div className="p-2">
            {filteredQuestions.map((q, idx) => {
              const originalIndex = questions.indexOf(q);
              const isAnswered = answeredQuestions[originalIndex];
              const isCurrent = originalIndex === currentQuestionIndex;
              
              return (
                <div
                  key={q.question_id || idx}
                  onClick={() => handleQuestionSelect(originalIndex)}
                  className={`p-3 mb-2 rounded-lg cursor-pointer transition-all ${
                    isCurrent 
                      ? 'bg-blue-100 border-2 border-blue-500' 
                      : isAnswered?.correct 
                        ? 'bg-green-50 border border-green-200' 
                        : isAnswered 
                          ? 'bg-red-50 border border-red-200'
                          : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
                  }`}
                  data-testid={`question-item-${idx}`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      isCurrent ? 'bg-blue-500 text-white' :
                      isAnswered?.correct ? 'bg-green-500 text-white' :
                      isAnswered ? 'bg-red-500 text-white' :
                      'bg-gray-200 text-gray-600'
                    }`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 line-clamp-2">
                        {q.questionText?.substring(0, 80)}...
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">{q.year}</Badge>
                        <Badge variant="secondary" className="text-xs">{q.difficulty}</Badge>
                      </div>
                    </div>
                    {isAnswered && (
                      isAnswered.correct 
                        ? <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                        : <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </div>
    </div>
  );

  // Render Step 1: Exam Type Selection
  if (step === 1) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-heading font-bold">Practice Previous Year Questions</h1>
            <p className="text-muted-foreground text-lg">Select exam type to begin</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
            <Card 
              className="cursor-pointer hover:shadow-hover transition-all hover:-translate-y-1 border-2 hover:border-primary"
              onClick={() => handleExamTypeSelect('JEE_Main')}
              data-testid="jee-main-card"
            >
              <CardContent className="p-8 text-center space-y-4">
                <div className="mx-auto bg-blue-100 p-4 rounded-full w-fit">
                  <Target className="h-12 w-12 text-blue-600" />
                </div>
                <h2 className="text-2xl font-heading font-bold">JEE Main</h2>
                <p className="text-muted-foreground">
                  Practice questions from JEE Main previous papers
                </p>
                <Badge variant="outline" className="mt-2">Most Popular</Badge>
              </CardContent>
            </Card>

            <Card 
              className="cursor-pointer hover:shadow-hover transition-all hover:-translate-y-1 border-2 hover:border-primary"
              onClick={() => handleExamTypeSelect('JEE_Advanced')}
              data-testid="jee-advanced-card"
            >
              <CardContent className="p-8 text-center space-y-4">
                <div className="mx-auto bg-purple-100 p-4 rounded-full w-fit">
                  <Award className="h-12 w-12 text-purple-600" />
                </div>
                <h2 className="text-2xl font-heading font-bold">JEE Advanced</h2>
                <p className="text-muted-foreground">
                  Practice questions from JEE Advanced previous papers
                </p>
                <Badge variant="outline" className="mt-2">For IIT Aspirants</Badge>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // Render Step 2: Subject Selection
  if (step === 2) {
    const subjects = ['Physics', 'Chemistry', 'Mathematics'];
    const subjectColors = {
      Physics: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
      Chemistry: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
      Mathematics: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' }
    };

    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <Button variant="ghost" onClick={goBack} className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>

          <div className="text-center space-y-2">
            <Badge variant="outline">{examType.replace('_', ' ')}</Badge>
            <h1 className="text-4xl font-heading font-bold">Select Subject</h1>
            <p className="text-muted-foreground text-lg">Choose a subject to practice</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            {subjects.map((subj) => {
              const colors = subjectColors[subj];
              return (
                <Card
                  key={subj}
                  className={`cursor-pointer hover:shadow-hover transition-all hover:-translate-y-1 border-2 ${colors.border}`}
                  onClick={() => handleSubjectSelect(subj)}
                  data-testid={`${subj.toLowerCase()}-card`}
                >
                  <CardContent className={`p-8 text-center space-y-4 ${colors.bg}`}>
                    <BookOpen className={`h-12 w-12 mx-auto ${colors.text}`} />
                    <h2 className={`text-2xl font-heading font-bold ${colors.text}`}>{subj}</h2>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Render Step 3: Chapter Selection
  if (step === 3 && syllabus) {
    const chapters = [
      ...(syllabus[subject]?.Class11 || []).map(ch => ({ ...ch, class: 'Class 11' })),
      ...(syllabus[subject]?.Class12 || []).map(ch => ({ ...ch, class: 'Class 12' }))
    ];

    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-6xl mx-auto space-y-6">
          <Button variant="ghost" onClick={goBack} className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>

          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline">{examType.replace('_', ' ')}</Badge>
              <ChevronRight className="h-4 w-4" />
              <Badge variant="outline">{subject}</Badge>
            </div>
            <h1 className="text-4xl font-heading font-bold">Select Chapter</h1>
            <p className="text-muted-foreground text-lg">Choose a chapter to practice</p>
          </div>

          <Tabs defaultValue="class11" className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="class11">Class 11</TabsTrigger>
              <TabsTrigger value="class12">Class 12</TabsTrigger>
            </TabsList>
            
            <TabsContent value="class11" className="mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {chapters.filter(ch => ch.class === 'Class 11').map((chapter, idx) => (
                  <Card
                    key={idx}
                    className="cursor-pointer hover:shadow-hover transition-all hover:-translate-y-1"
                    onClick={() => handleChapterSelect(chapter)}
                  >
                    <CardHeader>
                      <CardTitle className="text-lg">{chapter.chapter}</CardTitle>
                      <CardDescription>
                        {chapter.topics?.length || 0} topics
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button className="w-full" size="sm">
                        Practice <ChevronRight className="h-4 w-4 ml-2" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
            
            <TabsContent value="class12" className="mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {chapters.filter(ch => ch.class === 'Class 12').map((chapter, idx) => (
                  <Card
                    key={idx}
                    className="cursor-pointer hover:shadow-hover transition-all hover:-translate-y-1"
                    onClick={() => handleChapterSelect(chapter)}
                  >
                    <CardHeader>
                      <CardTitle className="text-lg">{chapter.chapter}</CardTitle>
                      <CardDescription>
                        {chapter.topics?.length || 0} topics
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button className="w-full" size="sm">
                        Practice <ChevronRight className="h-4 w-4 ml-2" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    );
  }

  // Render Step 4: Practice Type Selection  
  if (step === 4) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <Button variant="ghost" onClick={goBack} className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>

          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline">{examType.replace('_', ' ')}</Badge>
              <ChevronRight className="h-4 w-4" />
              <Badge variant="outline">{subject}</Badge>
              <ChevronRight className="h-4 w-4" />
              <Badge variant="outline">{selectedChapter?.chapter}</Badge>
            </div>
            <h1 className="text-4xl font-heading font-bold">Choose Practice Mode</h1>
            <p className="text-muted-foreground text-lg">
              {questions.length} questions available
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
            <Card
              className="cursor-pointer hover:shadow-hover transition-all hover:-translate-y-1 border-2 hover:border-primary"
              onClick={() => handlePracticeTypeSelect('pyq')}
              data-testid="pyq-practice-card"
            >
              <CardContent className="p-8 text-center space-y-4">
                <div className="mx-auto bg-orange-100 p-4 rounded-full w-fit">
                  <BookOpen className="h-12 w-12 text-orange-600" />
                </div>
                <h2 className="text-2xl font-heading font-bold">PYQs (Year-wise)</h2>
                <p className="text-muted-foreground">
                  Practice all previous year questions sorted from latest to oldest
                </p>
                <Badge variant="secondary">{questions.length} Questions</Badge>
              </CardContent>
            </Card>

            <Card
              className="cursor-pointer hover:shadow-hover transition-all hover:-translate-y-1 border-2 hover:border-primary"
              onClick={() => handlePracticeTypeSelect('topic')}
              data-testid="topic-practice-card"
            >
              <CardContent className="p-8 text-center space-y-4">
                <div className="mx-auto bg-teal-100 p-4 rounded-full w-fit">
                  <Target className="h-12 w-12 text-teal-600" />
                </div>
                <h2 className="text-2xl font-heading font-bold">Topic-wise</h2>
                <p className="text-muted-foreground">
                  Practice specific topics within this chapter
                </p>
                <Badge variant="secondary">{chapterTopics.length} Topics</Badge>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // Render Step 5: Question List / Topic Selection
  if (step === 5) {
    if (practiceType === 'topic') {
      // Topic Selection
      return (
        <div className="min-h-screen bg-background p-8">
          <div className="max-w-6xl mx-auto space-y-6">
            <Button variant="ghost" onClick={goBack} className="mb-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>

            <div className="space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="outline">{examType.replace('_', ' ')}</Badge>
                <ChevronRight className="h-4 w-4" />
                <Badge variant="outline">{subject}</Badge>
                <ChevronRight className="h-4 w-4" />
                <Badge variant="outline">{selectedChapter?.chapter}</Badge>
              </div>
              <h1 className="text-4xl font-heading font-bold">Select Topic</h1>
              <p className="text-muted-foreground text-lg">Choose a topic to practice</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
              {chapterTopics.map((topic, idx) => {
                const topicCount = allQuestions.filter(q => q.topic === topic).length;
                return (
                  <Card
                    key={idx}
                    className="cursor-pointer hover:shadow-hover transition-all hover:-translate-y-1"
                    onClick={() => handleTopicSelect(topic)}
                    data-testid={`topic-card-${idx}`}
                  >
                    <CardHeader>
                      <CardTitle className="text-lg">{topic}</CardTitle>
                      <CardDescription>{topicCount} questions</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button className="w-full" size="sm">
                        Practice <ChevronRight className="h-4 w-4 ml-2" />
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </div>
      );
    }

    // PYQ Mode - Show scrollable question list
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-6xl mx-auto space-y-6">
          <Button variant="ghost" onClick={goBack} className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>

          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline">{examType.replace('_', ' ')}</Badge>
              <ChevronRight className="h-4 w-4" />
              <Badge variant="outline">{subject}</Badge>
              <ChevronRight className="h-4 w-4" />
              <Badge variant="outline">{selectedChapter?.chapter}</Badge>
            </div>
            <h1 className="text-4xl font-heading font-bold">Previous Year Questions</h1>
          </div>

          {/* Search Bar */}
          <div className="relative max-w-xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              placeholder="Search by question text or year..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 pr-4 py-3 text-lg"
              data-testid="search-input"
            />
            
            {/* Search Dropdown */}
            {showSearchDropdown && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-50 max-h-96 overflow-auto">
                {searchResults.map((q, idx) => (
                  <div
                    key={q.question_id || idx}
                    className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                    onClick={() => handleSearchResultClick(q)}
                    data-testid={`search-result-${idx}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-xs">{q.year}</Badge>
                      <Badge variant="secondary" className="text-xs">{q.topic}</Badge>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-2">{q.questionText}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Year Filter Pills */}
          <div className="flex gap-2 flex-wrap items-center">
            <span className="text-sm text-muted-foreground mr-2">Filter by year:</span>
            <Badge
              variant={yearFilter === '' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setYearFilter('')}
            >
              All ({questions.length})
            </Badge>
            {availableYears.map(year => {
              const count = questions.filter(q => q.year === year).length;
              return (
                <Badge
                  key={year}
                  variant={yearFilter === year.toString() ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => setYearFilter(yearFilter === year.toString() ? '' : year.toString())}
                >
                  {year} ({count})
                </Badge>
              );
            })}
          </div>

          {/* Questions Grid */}
          <ScrollArea className="h-[600px] border rounded-lg">
            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredQuestions.map((q, idx) => {
                const originalIndex = questions.indexOf(q);
                const isAnswered = answeredQuestions[originalIndex];
                
                return (
                  <Card
                    key={q.question_id || idx}
                    className={`cursor-pointer hover:shadow-lg transition-all ${
                      isAnswered?.correct 
                        ? 'border-green-300 bg-green-50' 
                        : isAnswered 
                          ? 'border-red-300 bg-red-50'
                          : 'hover:border-blue-300'
                    }`}
                    onClick={() => handleQuestionSelect(originalIndex)}
                    data-testid={`question-card-${idx}`}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                            isAnswered?.correct ? 'bg-green-500 text-white' :
                            isAnswered ? 'bg-red-500 text-white' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {idx + 1}
                          </div>
                          <Badge variant="outline">{q.year}</Badge>
                          <Badge variant="secondary">{q.difficulty}</Badge>
                        </div>
                        {isAnswered && (
                          isAnswered.correct 
                            ? <CheckCircle className="h-5 w-5 text-green-500" />
                            : <XCircle className="h-5 w-5 text-red-500" />
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-700 line-clamp-3">
                        {q.questionText?.substring(0, 150)}...
                      </p>
                      <div className="mt-2">
                        <Badge variant="outline" className="text-xs">{q.topic}</Badge>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </ScrollArea>
        </div>
      </div>
    );
  }

  // Render Step 6: Question Viewer
  if (step === 6 && questions.length > 0) {
    const currentQ = questions[currentQuestionIndex];
    const isAnswered = answeredQuestions[currentQuestionIndex];

    return (
      <div className="min-h-screen bg-background p-8">
        <QuestionListSidebar />
        
        {/* Overlay when sidebar is open */}
        {showQuestionList && (
          <div 
            className="fixed inset-0 bg-black/30 z-40"
            onClick={() => setShowQuestionList(false)}
          />
        )}
        
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="flex justify-between items-center">
            <Button variant="ghost" onClick={goBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                Question {currentQuestionIndex + 1} of {questions.length}
              </span>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowQuestionList(true)}
                data-testid="show-question-list"
              >
                <List className="h-4 w-4 mr-2" />
                All Questions
              </Button>
            </div>
          </div>

          {/* Search Bar in Question View */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Jump to question..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="question-view-search"
            />
            
            {showSearchDropdown && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-50 max-h-64 overflow-auto">
                {searchResults.map((q, idx) => (
                  <div
                    key={q.question_id || idx}
                    className="p-2 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 text-sm"
                    onClick={() => handleSearchResultClick(q)}
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">{q.year}</Badge>
                      <span className="line-clamp-1">{q.questionText?.substring(0, 60)}...</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline">{examType.replace('_', ' ')}</Badge>
              <ChevronRight className="h-4 w-4" />
              <Badge variant="outline">{subject}</Badge>
              <ChevronRight className="h-4 w-4" />
              <Badge variant="outline">{currentQ.chapter}</Badge>
              <ChevronRight className="h-4 w-4" />
              <Badge variant="outline">{currentQ.topic}</Badge>
            </div>
          </div>

          <Card className="shadow-card">
            <CardHeader>
              <div className="flex justify-between items-start gap-3">
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge>Q{currentQ.questionNumber || currentQuestionIndex + 1}</Badge>
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {currentQ.year}
                    </Badge>
                    <Badge variant="secondary">{currentQ.difficulty}</Badge>
                  </div>
                  <CardTitle className="text-xl">
                    {currentQ.questionText}
                  </CardTitle>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleBookmark(currentQ)}
                  disabled={bookmarkBusy}
                  data-testid="pyq-bookmark-btn"
                  title={bookmarkedIds.has(currentQ.question_id) ? 'Remove bookmark' : 'Save to bookmarks'}
                  className="shrink-0"
                >
                  {bookmarkedIds.has(currentQ.question_id)
                    ? <BookmarkCheck className="h-5 w-5 text-indigo-600" />
                    : <Bookmark className="h-5 w-5 text-slate-400" />}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Check if this is a Numerical question or MCQ with empty options */}
              {currentQ.questionType === 'Numerical' || !Object.values(currentQ.options || {}).some(v => v && v.trim()) ? (
                // Numerical Question UI
                <div className="space-y-4">
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline" className="bg-amber-100">Numerical Type</Badge>
                    </div>
                    <p className="text-sm text-amber-800">
                      This is a numerical answer type question. Enter your answer below.
                    </p>
                  </div>
                  
                  <div className="flex gap-3">
                    <Input
                      type="text"
                      placeholder="Enter your numerical answer"
                      value={selectedAnswer || ''}
                      onChange={(e) => setSelectedAnswer(e.target.value)}
                      className="text-lg"
                      disabled={showSolution}
                      data-testid="numerical-input"
                    />
                  </div>
                  
                  {showSolution && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <span className="font-semibold text-green-800">
                          Correct Answer: {currentQ.correctAnswer}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                // MCQ Options UI
                <div className="space-y-3">
                  {['A', 'B', 'C', 'D'].map((option) => {
                    const optionText = currentQ.options?.[option] || '';
                    if (!optionText) return null;
                    
                    const isSelected = selectedAnswer === option;
                    const isCorrectAnswer = currentQ.correctAnswer === option;
                    const showCorrect = showSolution && isCorrectAnswer;
                    const showIncorrect = showSolution && isSelected && !isCorrectAnswer;

                    return (
                      <div
                        key={option}
                        onClick={() => handleAnswerSelect(option)}
                        className={`
                          p-4 rounded-lg border-2 cursor-pointer transition-all
                          ${
                            showCorrect
                              ? 'bg-green-50 border-green-500'
                              : showIncorrect
                              ? 'bg-red-50 border-red-500'
                              : isSelected
                              ? 'bg-blue-50 border-blue-500'
                              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                          }
                        `}
                        data-testid={`option-${option}`}
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={`
                              w-8 h-8 rounded-full border-2 flex items-center justify-center font-semibold flex-shrink-0
                              ${
                                showCorrect
                                  ? 'bg-green-500 text-white border-green-500'
                                  : showIncorrect
                                  ? 'bg-red-500 text-white border-red-500'
                                  : isSelected
                                  ? 'bg-blue-500 text-white border-blue-500'
                                  : 'border-gray-300'
                              }
                            `}
                          >
                            {option}
                          </div>
                          <div className="flex-1">{optionText}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {showSolution && (
                <div className="space-y-4 pt-4 border-t">
                  {currentQ.solution && (
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="font-semibold mb-2">Solution:</h4>
                      <p className="text-sm whitespace-pre-wrap">{currentQ.solution}</p>
                    </div>
                  )}

                  <Button
                    onClick={handleViewSolution}
                    variant="outline"
                    className="w-full"
                  >
                    View Detailed Solution on YouTube
                  </Button>
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  onClick={handlePrevious}
                  disabled={currentQuestionIndex === 0}
                  variant="outline"
                  className="flex-1"
                >
                  Previous
                </Button>
                
                {!showSolution ? (
                  <Button
                    onClick={handleSubmitAnswer}
                    disabled={!selectedAnswer}
                    className="flex-1"
                    data-testid="submit-answer"
                  >
                    Submit Answer
                  </Button>
                ) : (
                  <Button
                    onClick={handleNext}
                    disabled={currentQuestionIndex === questions.length - 1}
                    className="flex-1"
                    data-testid="next-question"
                  >
                    Next Question
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Quick Navigation */}
          <Card>
            <CardContent className="p-4">
              <h4 className="text-sm font-medium mb-3">Quick Navigation</h4>
              <div className="flex flex-wrap gap-2">
                {questions.slice(0, 20).map((_, idx) => {
                  const isAnsweredQ = answeredQuestions[idx];
                  const isCurrent = idx === currentQuestionIndex;
                  
                  return (
                    <button
                      key={idx}
                      onClick={() => handleQuestionSelect(idx)}
                      className={`w-8 h-8 rounded text-sm font-medium transition-all ${
                        isCurrent 
                          ? 'bg-blue-500 text-white' 
                          : isAnsweredQ?.correct 
                            ? 'bg-green-100 text-green-700 border border-green-300' 
                            : isAnsweredQ 
                              ? 'bg-red-100 text-red-700 border border-red-300'
                              : 'bg-gray-100 hover:bg-gray-200'
                      }`}
                    >
                      {idx + 1}
                    </button>
                  );
                })}
                {questions.length > 20 && (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setShowQuestionList(true)}
                  >
                    +{questions.length - 20} more
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Loading or empty state
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
};

export default PYQSection;
