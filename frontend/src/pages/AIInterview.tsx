import React, { useState, useEffect } from 'react';
import { mockAIQuestions } from '../data/mockData';
import { Setup } from '../components/ai-interview/Setup';
import { PreInterview } from '../components/ai-interview/PreInterview';
import { Interview } from '../components/ai-interview/Interview';
import { Results } from '../components/ai-interview/Results';

interface InterviewSetup {
  resumeSource: 'profile' | 'upload';
  interviewType: string;
  difficulty: string;
  duration: number;
  focusAreas: string[];
}

export const AIInterview: React.FC = () => {
  // Simulate authentication state
  const isLoggedIn = false; // Set to true if user is logged in
  const userName = isLoggedIn ? 'John Doe' : undefined;

  const [currentStep, setCurrentStep] = useState<'setup' | 'pre-interview' | 'interview' | 'results'>('setup');
  // Validation state for setup
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const [interviewSetup, setInterviewSetup] = useState<InterviewSetup>({
    resumeSource: isLoggedIn ? 'profile' : 'upload',
    interviewType: 'general',
    difficulty: 'intermediate',
    duration: 30,
    focusAreas: []
  });
  
  const [isInterviewActive, setIsInterviewActive] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [timer, setTimer] = useState(0);
  const [confidence, setConfidence] = useState(75);
  const [isPaused, setIsPaused] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);

  // Real-time metrics
  const [metrics, setMetrics] = useState({
    eyeContact: 85,
    speakingPace: 78,
    clarity: 92,
    enthusiasm: 88,
    bodyLanguage: 82
  });

  const interviewTypes = [
    { id: 'general', name: 'General Interview', description: 'Behavioral and general questions' },
    { id: 'technical', name: 'Technical Interview', description: 'Role-specific technical questions' },
    { id: 'behavioral', name: 'Behavioral Interview', description: 'STAR method and soft skills' },
    { id: 'leadership', name: 'Leadership Interview', description: 'Management and leadership scenarios' },
    { id: 'case-study', name: 'Case Study', description: 'Problem-solving and analytical thinking' }
  ];

  const focusAreaOptions = [
    'Communication Skills', 'Problem Solving', 'Leadership', 'Technical Expertise',
    'Team Collaboration', 'Adaptability', 'Project Management', 'Innovation'
  ];

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isInterviewActive && !isPaused) {
      interval = setInterval(() => {
        setTimer(prev => prev + 1);
        // Simulate real-time metrics fluctuation
        setConfidence(prev => Math.max(60, Math.min(95, prev + (Math.random() - 0.5) * 8)));
        setMetrics(prev => ({
          eyeContact: Math.max(70, Math.min(95, prev.eyeContact + (Math.random() - 0.5) * 6)),
          speakingPace: Math.max(65, Math.min(90, prev.speakingPace + (Math.random() - 0.5) * 5)),
          clarity: Math.max(75, Math.min(98, prev.clarity + (Math.random() - 0.5) * 4)),
          enthusiasm: Math.max(70, Math.min(95, prev.enthusiasm + (Math.random() - 0.5) * 7)),
          bodyLanguage: Math.max(65, Math.min(90, prev.bodyLanguage + (Math.random() - 0.5) * 6))
        }));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isInterviewActive, isPaused]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setIsAnalyzing(true);
      // Simulate AI analysis
      setTimeout(() => {
        setIsAnalyzing(false);
        setAnalysisComplete(true);
      }, 3000);
    }
  };

  const startInterview = () => {
    setCurrentStep('interview');
    setIsInterviewActive(true);
    setCurrentQuestionIndex(0);
    setTimer(0);
    setConfidence(75);
  };

  // Validation for setup step
  const validateSetup = () => {
    const errors: string[] = [];
    if (!interviewSetup.interviewType) errors.push('Please select an interview type.');
    if (!interviewSetup.difficulty) errors.push('Please select a difficulty level.');
    if (!interviewSetup.duration) errors.push('Please select a duration.');
    if (interviewSetup.resumeSource === 'upload' && !analysisComplete) errors.push('Please upload and analyze your resume.');
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSetupNext = () => {
    if (validateSetup()) {
      setCurrentStep('pre-interview');
    }
  };

  const endInterview = () => {
    setIsInterviewActive(false);
    setIsRecording(false);
    setIsPaused(false);
    setCurrentStep('results');
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < mockAIQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      endInterview();
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
  };

  const togglePause = () => {
    setIsPaused(!isPaused);
  };

  const getMetricColor = (value: number) => {
    if (value >= 85) return 'text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20';
    if (value >= 70) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
    return 'text-red-600 bg-red-100 dark:bg-red-900/20';
  };

  const toggleFocusArea = (area: string) => {
    setInterviewSetup(prev => ({
      ...prev,
      focusAreas: prev.focusAreas.includes(area)
        ? prev.focusAreas.filter(a => a !== area)
        : [...prev.focusAreas, area]
    }));
  };


  if (currentStep === 'setup') {
    return (
      <Setup
        interviewSetup={interviewSetup}
        setInterviewSetup={setInterviewSetup}
        uploadedFile={uploadedFile}
        isAnalyzing={isAnalyzing}
        analysisComplete={analysisComplete}
        handleFileUpload={handleFileUpload}
        focusAreaOptions={focusAreaOptions}
        interviewTypes={interviewTypes}
        toggleFocusArea={toggleFocusArea}
        onNext={handleSetupNext}
        validationErrors={validationErrors}
        isLoggedIn={isLoggedIn}
        userName={userName}
      />
    );
  }
  if (currentStep === 'pre-interview') {
    return (
      <PreInterview
        interviewSetup={interviewSetup}
        interviewTypes={interviewTypes}
        onBack={() => setCurrentStep('setup')}
        onStart={startInterview}
      />
    );
  }

  if (currentStep === 'interview') {
    return (
      <Interview
        interviewSetup={interviewSetup}
        currentQuestionIndex={currentQuestionIndex}
        setCurrentQuestionIndex={setCurrentQuestionIndex}
        isInterviewActive={isInterviewActive}
        setIsInterviewActive={setIsInterviewActive}
        isRecording={isRecording}
        setIsRecording={setIsRecording}
        timer={timer}
        setTimer={setTimer}
        confidence={confidence}
        setConfidence={setConfidence}
        isPaused={isPaused}
        setIsPaused={setIsPaused}
        metrics={metrics}
        setMetrics={setMetrics}
        mockAIQuestions={mockAIQuestions}
        formatTime={formatTime}
        endInterview={endInterview}
        nextQuestion={nextQuestion}
        toggleRecording={toggleRecording}
        togglePause={togglePause}
        getMetricColor={getMetricColor}
      />
    );
  }

  // Results Step
  return (
    <Results
      interviewSetup={interviewSetup}
      metrics={metrics}
      confidence={confidence}
      timer={timer}
      mockAIQuestions={mockAIQuestions}
      formatTime={formatTime}
      setCurrentStep={setCurrentStep}
      setTimer={setTimer}
      setCurrentQuestionIndex={setCurrentQuestionIndex}
    />
  );
};

