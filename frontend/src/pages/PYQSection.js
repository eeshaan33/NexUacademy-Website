import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { BookOpen, ChevronRight, Award, Target, ArrowLeft } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

const PYQSection = () => {
  const [step, setStep] = useState(1); // 1: Exam Type, 2: Subject, 3: Chapter, 4: Practice Type, 5: Questions
  const [examType, setExamType] = useState('');
  const [subject, setSubject] = useState('');
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [practiceType, setPracticeType] = useState(''); // 'pyq' or 'topic'
  const [syllabus, setSyllabus] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showSolution, setShowSolution] = useState(false);
  const [answeredQuestions, setAnsweredQuestions] = useState({});

  useEffect(() => {
    fetchSyllabus();
  }, []);

  const fetchSyllabus = async () => {
    try {
      const response = await api.get('/questions/syllabus');
      setSyllabus(response.data);
    } catch (error) {
      console.error('Failed to fetch syllabus:', error);
      toast.error('Failed to load syllabus');
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

  const handleChapterSelect = (chapter) => {
    setSelectedChapter(chapter);
    setStep(4);
  };

  const handlePracticeTypeSelect = async (type) => {
    setPracticeType(type);
    await fetchQuestions(type);
    setStep(5);
  };

  const fetchQuestions = async (type) => {
    try {
      const params = {
        examType,
        subject,
        chapter: selectedChapter.chapter,
        limit: 100
      };

      const response = await api.get('/questions/', { params });
      
      // Sort by year (latest to oldest)
      const sorted = response.data.questions.sort((a, b) => b.year - a.year);
      setQuestions(sorted);
      setCurrentQuestionIndex(0);
      setAnsweredQuestions({});
    } catch (error) {
      console.error('Failed to fetch questions:', error);
      toast.error('Failed to load questions');
    }
  };

  const handleAnswerSelect = (option) => {
    if (showSolution) return;
    setSelectedAnswer(option);
  };

  const handleSubmitAnswer = () => {
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

    if (isCorrect) {
      toast.success('Correct! Well done!');
    } else {
      toast.error(`Incorrect. The correct answer is ${currentQ.correctAnswer}`);
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
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
      const url = `${currentQ.solutionYoutubeUrl}&t=${currentQ.solutionTimestamp}s`;
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
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setSelectedAnswer(null);
    setShowSolution(false);
    setAnsweredQuestions({});
  };

  const goBack = () => {
    if (step > 1) {
      setStep(step - 1);
      if (step === 2) {
        setExamType('');
      } else if (step === 3) {
        setSubject('');
      } else if (step === 4) {
        setSelectedChapter(null);
      } else if (step === 5) {
        setPracticeType('');
      }
    }
  };

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
            <p className="text-muted-foreground text-lg">How would you like to practice?</p>
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
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // Render Step 5: Question Viewer
  if (step === 5 && questions.length > 0) {
    const currentQ = questions[currentQuestionIndex];
    const isAnswered = answeredQuestions[currentQuestionIndex];

    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="flex justify-between items-center">
            <Button variant="ghost" onClick={resetFlow}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Button>
            <div className="text-sm text-muted-foreground">
              Question {currentQuestionIndex + 1} of {questions.length}
            </div>
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
              <div className="flex justify-between items-start">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge>Q{currentQ.questionNumber}</Badge>
                    <Badge variant="outline">{currentQ.year}</Badge>
                    <Badge variant="secondary">{currentQ.difficulty}</Badge>
                  </div>
                  <CardTitle className="text-xl">
                    {currentQ.questionText}
                  </CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                {['A', 'B', 'C', 'D'].map((option) => {
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
                            w-8 h-8 rounded-full border-2 flex items-center justify-center font-semibold
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
                        <div className="flex-1">{currentQ.options[option]}</div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {showSolution && (
                <div className="space-y-4 pt-4 border-t">
                  {currentQ.solution && (
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="font-semibold mb-2">Solution:</h4>
                      <p className="text-sm">{currentQ.solution}</p>
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
