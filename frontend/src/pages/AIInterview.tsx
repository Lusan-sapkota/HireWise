import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { mockAIQuestions, mockUser } from '../data/mockData';
import { 
  Bot, 
  Play, 
  Pause, 
  Square, 
  Mic, 
  MicOff, 
  Timer,
  Activity,
  FileText,
  Award,
  Upload,
  User,
  Sparkles,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Camera,
  Volume2,
  Settings
} from 'lucide-react';

interface InterviewSetup {
  resumeSource: 'profile' | 'upload';
  interviewType: string;
  difficulty: string;
  duration: number;
  focusAreas: string[];
}

export const AIInterview: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<'setup' | 'interview' | 'results'>('setup');
  const [interviewSetup, setInterviewSetup] = useState<InterviewSetup>({
    resumeSource: 'profile',
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
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-4 sm:py-6 lg:py-8">
        <div className="max-w-4xl mx-auto px-3 sm:px-4 lg:px-6 xl:px-8">
          <div className="text-center mb-6 sm:mb-8">
            <div className="w-16 h-16 bg-gradient-to-r from-violet-600 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-4">
              AI Interview Assistant
            </h1>
            <p className="text-base sm:text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto px-4">
              Get personalized interview practice with real-time feedback, confidence tracking, and detailed performance analytics.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
            {/* Resume Source Selection */}
            <Card className="h-fit">
              <CardHeader>
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  Choose Your Resume Source
                </h2>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  AI will tailor questions based on your background
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 sm:space-y-4">
                  {/* Profile Option */}
                  <div 
                    className={`p-3 sm:p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      interviewSetup.resumeSource === 'profile'
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                    onClick={() => setInterviewSetup(prev => ({ ...prev, resumeSource: 'profile' }))}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`w-5 h-5 rounded-full border-2 mt-0.5 ${
                        interviewSetup.resumeSource === 'profile'
                          ? 'border-indigo-500 bg-indigo-500'
                          : 'border-gray-300 dark:border-gray-600'
                      }`}>
                        {interviewSetup.resumeSource === 'profile' && (
                          <div className="w-full h-full rounded-full bg-white scale-50"></div>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <User className="w-5 h-5 text-indigo-600" />
                          <h3 className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">Use My Profile</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-3">
                          AI will analyze your HireWise profile and generate relevant questions
                        </p>
                        <div className="flex items-center space-x-2">
                          <img src={mockUser.avatar} alt="" className="w-6 h-6 rounded-full" />
                          <span className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                            {mockUser.name} - {mockUser.title}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Upload Option */}
                  <div 
                    className={`p-3 sm:p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      interviewSetup.resumeSource === 'upload'
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                    onClick={() => setInterviewSetup(prev => ({ ...prev, resumeSource: 'upload' }))}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`w-5 h-5 rounded-full border-2 mt-0.5 ${
                        interviewSetup.resumeSource === 'upload'
                          ? 'border-indigo-500 bg-indigo-500'
                          : 'border-gray-300 dark:border-gray-600'
                      }`}>
                        {interviewSetup.resumeSource === 'upload' && (
                          <div className="w-full h-full rounded-full bg-white scale-50"></div>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Upload className="w-5 h-5 text-violet-600" />
                          <h3 className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">Upload Resume</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-3">
                          Upload a specific resume for targeted interview preparation
                        </p>
                        
                        {interviewSetup.resumeSource === 'upload' && (
                          <div className="mt-3">
                            {!uploadedFile ? (
                              <label className="block">
                                <input
                                  type="file"
                                  accept=".pdf,.doc,.docx"
                                  onChange={handleFileUpload}
                                  className="hidden"
                                />
                                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4 text-center hover:border-indigo-400 dark:hover:border-indigo-500 cursor-pointer">
                                  <Upload className="w-6 h-6 text-gray-400 mx-auto mb-2" />
                                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                                    Click to upload PDF, DOC, or DOCX
                                  </p>
                                </div>
                              </label>
                            ) : (
                              <div className="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                                {isAnalyzing ? (
                                  <>
                                    <Bot className="w-5 h-5 text-violet-600 animate-pulse" />
                                    <div className="flex-1">
                                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                                        Analyzing resume...
                                      </p>
                                      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                                        AI is extracting key information
                                      </p>
                                    </div>
                                  </>
                                ) : (
                                  <>
                                    <CheckCircle className="w-5 h-5 text-green-600" />
                                    <div className="flex-1">
                                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                                        {uploadedFile.name}
                                      </p>
                                      <p className="text-xs sm:text-sm text-green-600">
                                        Resume analyzed successfully
                                      </p>
                                    </div>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Interview Configuration */}
            <Card className="h-fit">
              <CardHeader>
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  Interview Configuration
                </h2>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  Customize your interview experience
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 sm:space-y-6">
                  {/* Interview Type */}
                  <div>
                    <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 sm:mb-3">
                      Interview Type
                    </label>
                    <div className="grid grid-cols-1 gap-2">
                      {interviewTypes.map((type) => (
                        <div
                          key={type.id}
                          className={`p-2 sm:p-3 rounded-lg border cursor-pointer transition-all ${
                            interviewSetup.interviewType === type.id
                              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }`}
                          onClick={() => setInterviewSetup(prev => ({ ...prev, interviewType: type.id }))}
                        >
                          <h4 className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">{type.name}</h4>
                          <p className="text-xs text-gray-600 dark:text-gray-400">{type.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Difficulty */}
                  <div>
                    <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Difficulty Level
                    </label>
                    <select 
                      value={interviewSetup.difficulty}
                      onChange={(e) => setInterviewSetup(prev => ({ ...prev, difficulty: e.target.value }))}
                      className="w-full p-2 sm:p-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                      <option value="expert">Expert</option>
                    </select>
                  </div>

                  {/* Duration */}
                  <div>
                    <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Duration (minutes)
                    </label>
                    <select 
                      value={interviewSetup.duration}
                      onChange={(e) => setInterviewSetup(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
                      className="w-full p-2 sm:p-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value={15}>15 minutes</option>
                      <option value={30}>30 minutes</option>
                      <option value={45}>45 minutes</option>
                      <option value={60}>60 minutes</option>
                    </select>
                  </div>

                  {/* Focus Areas */}
                  <div>
                    <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Focus Areas (Optional)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {focusAreaOptions.map((area) => (
                        <button
                          key={area}
                          onClick={() => toggleFocusArea(area)}
                          className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium transition-all ${
                            interviewSetup.focusAreas.includes(area)
                              ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 border border-indigo-300 dark:border-indigo-700'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600'
                          }`}
                        >
                          {area}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Start Button */}
          <div className="text-center mt-6 sm:mt-8">
            <Button 
              onClick={startInterview} 
              size="lg" 
              className="px-6 sm:px-8 py-3 sm:py-4 w-full sm:w-auto"
              disabled={interviewSetup.resumeSource === 'upload' && !analysisComplete}
            >
              <Play className="w-5 h-5 mr-2" />
              Start AI Interview
            </Button>
            {interviewSetup.resumeSource === 'upload' && !analysisComplete && (
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-2">
                Please upload and analyze your resume first
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (currentStep === 'interview') {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Interview Header */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 lg:px-8 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-3 sm:space-x-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">AI Interview</h1>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                    {interviewSetup.interviewType.charAt(0).toUpperCase() + interviewSetup.interviewType.slice(1)} Interview
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2 sm:space-x-4 text-xs sm:text-sm">
                <div className="flex items-center space-x-2">
                  <Timer className="w-4 h-4 text-gray-500" />
                  <span className="font-mono text-sm sm:text-lg text-gray-900 dark:text-white">
                    {formatTime(timer)}
                  </span>
                </div>
                
                <div className="hidden sm:flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-600 dark:text-gray-400">
                    Question {currentQuestionIndex + 1} of {mockAIQuestions.length}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2 sm:space-x-3">
              <Button
                variant="ghost"
                onClick={togglePause}
                size="sm"
                className="hidden sm:flex"
              >
                {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                <span className="ml-2">{isPaused ? 'Resume' : 'Pause'}</span>
              </Button>
              
              <Button
                variant="outline"
                onClick={endInterview}
                size="sm"
              >
                <Square className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">End Interview</span>
                <span className="sm:hidden">End</span>
              </Button>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 xl:px-8 py-4 sm:py-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
            
            {/* Main Interview Area */}
            <div className="lg:col-span-2 space-y-4 sm:space-y-6">
              {/* AI Interviewer */}
              <Card>
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="w-10 sm:w-12 h-10 sm:h-12 bg-gradient-to-r from-violet-600 to-purple-600 rounded-full flex items-center justify-center">
                      <Bot className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                        AI Interviewer
                      </h2>
                      <p className="text-xs sm:text-sm text-violet-600 dark:text-violet-400">
                        Listening and analyzing your response...
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-900/20 dark:to-purple-900/20 p-4 sm:p-6 rounded-xl mb-4 sm:mb-6 border border-violet-200 dark:border-violet-800">
                    <p className="text-base sm:text-lg text-violet-900 dark:text-violet-100 leading-relaxed">
                      {mockAIQuestions[currentQuestionIndex]}
                    </p>
                  </div>
                  
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-3 sm:space-y-0">
                    <div className="flex items-center space-x-3 sm:space-x-4">
                      <Button
                        variant={isRecording ? "secondary" : "outline"}
                        onClick={toggleRecording}
                        className="flex items-center space-x-2 text-sm"
                      >
                        {isRecording ? (
                          <>
                            <MicOff className="w-4 h-4" />
                            <span className="hidden sm:inline">Stop Recording</span>
                            <span className="sm:hidden">Stop</span>
                          </>
                        ) : (
                          <>
                            <Mic className="w-4 h-4" />
                            <span className="hidden sm:inline">Start Recording</span>
                            <span className="sm:hidden">Record</span>
                          </>
                        )}
                      </Button>
                      
                      {isRecording && (
                        <div className="flex items-center space-x-2 text-sm">
                          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                          <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Recording...</span>
                        </div>
                      )}
                    </div>

                    <Button onClick={nextQuestion} className="w-full sm:w-auto">
                      <span className="hidden sm:inline">
                        {currentQuestionIndex < mockAIQuestions.length - 1 ? 'Next Question' : 'Finish Interview'}
                      </span>
                      <span className="sm:hidden">
                        {currentQuestionIndex < mockAIQuestions.length - 1 ? 'Next' : 'Finish'}
                      </span>
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Video Preview */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Video Preview</h3>
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm">
                        <Camera className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Volume2 className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
                    <div className="text-center text-white">
                      <Camera className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p className="text-xs sm:text-sm opacity-75">Camera feed would appear here</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Real-time Analytics */}
            <div className="space-y-4 sm:space-y-6">
              {/* Confidence Meter */}
              <Card className="border-2 border-emerald-200 dark:border-emerald-800">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Target className="w-5 h-5 text-emerald-600" />
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                      Confidence Level
                    </h3>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-center mb-4">
                    <div className="text-2xl sm:text-3xl font-bold text-emerald-600 mb-2">
                      {Math.round(confidence)}%
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                      <div 
                        className="bg-emerald-500 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${confidence}%` }}
                      ></div>
                    </div>
                  </div>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 text-center">
                    {confidence >= 85 ? 'Excellent confidence!' : 
                     confidence >= 70 ? 'Good confidence level' : 
                     'Try to speak more confidently'}
                  </p>
                </CardContent>
              </Card>

              {/* Real-time Metrics */}
              <Card>
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="w-5 h-5 text-indigo-600" />
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                      Performance Metrics
                    </h3>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 sm:space-y-4">
                    {Object.entries(metrics).map(([key, value]) => (
                      <div key={key}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 capitalize">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </span>
                          <span className={`text-xs sm:text-sm font-medium px-2 py-1 rounded ${getMetricColor(value)}`}>
                            {Math.round(value)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-500 ${
                              value >= 85 ? 'bg-emerald-500' :
                              value >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${value}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* AI Tips */}
              <Card className="border-2 border-violet-200 dark:border-violet-800">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-5 h-5 text-violet-600" />
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                      AI Tips
                    </h3>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 sm:space-y-3">
                    <div className="p-2 sm:p-3 bg-violet-50 dark:bg-violet-900/20 rounded-lg">
                      <div className="flex items-start space-x-2">
                        <AlertCircle className="w-4 h-4 text-violet-600 mt-0.5" />
                        <div>
                          <p className="text-xs sm:text-sm font-medium text-violet-900 dark:text-violet-100">
                            Speaking Pace
                          </p>
                          <p className="text-xs text-violet-700 dark:text-violet-300">
                            Try to slow down slightly for better clarity
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="p-2 sm:p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                      <div className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5" />
                        <div>
                          <p className="text-xs sm:text-sm font-medium text-emerald-900 dark:text-emerald-100">
                            Eye Contact
                          </p>
                          <p className="text-xs text-emerald-700 dark:text-emerald-300">
                            Great eye contact! Keep it up
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Results Step
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-4 sm:py-6 lg:py-8">
      <div className="max-w-6xl mx-auto px-3 sm:px-4 lg:px-6 xl:px-8">
        <div className="text-center mb-6 sm:mb-8">
          <Award className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Interview Complete!
          </h1>
          <p className="text-base sm:text-lg text-gray-600 dark:text-gray-300 px-4">
            Here's your comprehensive performance analysis
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Overall Score */}
          <Card className="lg:col-span-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white">
            <CardContent className="p-4 sm:p-6 lg:p-8">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 text-center">
                <div>
                  <div className="text-2xl sm:text-3xl font-bold mb-1 sm:mb-2">{Math.round(confidence)}%</div>
                  <div className="text-sm sm:text-base text-emerald-100">Overall Score</div>
                </div>
                <div>
                  <div className="text-2xl sm:text-3xl font-bold mb-1 sm:mb-2">{formatTime(timer)}</div>
                  <div className="text-sm sm:text-base text-emerald-100">Duration</div>
                </div>
                <div>
                  <div className="text-2xl sm:text-3xl font-bold mb-1 sm:mb-2">{mockAIQuestions.length}</div>
                  <div className="text-sm sm:text-base text-emerald-100">Questions</div>
                </div>
                <div>
                  <div className="text-2xl sm:text-3xl font-bold mb-1 sm:mb-2">A-</div>
                  <div className="text-sm sm:text-base text-emerald-100">Grade</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Metrics */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                Performance Breakdown
              </h2>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 sm:space-y-6">
                {Object.entries(metrics).map(([key, value]) => (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm sm:text-base font-medium text-gray-900 dark:text-white capitalize">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </span>
                      <span className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
                        {Math.round(value)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                      <div 
                        className={`h-3 rounded-full ${
                          value >= 85 ? 'bg-emerald-500' :
                          value >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${value}%` }}
                      ></div>
                    </div>
                    <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {value >= 85 ? 'Excellent performance' :
                       value >= 70 ? 'Good, with room for improvement' :
                       'Needs significant improvement'}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* AI Insights */}
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Bot className="w-5 h-5 text-violet-600" />
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  AI Insights
                </h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 sm:space-y-4">
                <div className="p-3 sm:p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                  <h3 className="text-sm sm:text-base font-medium text-emerald-900 dark:text-emerald-100 mb-2">
                    🎯 Strengths
                  </h3>
                  <ul className="text-xs sm:text-sm text-emerald-800 dark:text-emerald-200 space-y-1">
                    <li>• Excellent technical knowledge</li>
                    <li>• Clear communication style</li>
                    <li>• Good use of examples</li>
                  </ul>
                </div>
                
                <div className="p-3 sm:p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                  <h3 className="text-sm sm:text-base font-medium text-yellow-900 dark:text-yellow-100 mb-2">
                    📈 Areas to Improve
                  </h3>
                  <ul className="text-xs sm:text-sm text-yellow-800 dark:text-yellow-200 space-y-1">
                    <li>• Slow down speaking pace</li>
                    <li>• Add more quantified achievements</li>
                    <li>• Practice STAR method responses</li>
                  </ul>
                </div>
                
                <div className="p-3 sm:p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg border border-indigo-200 dark:border-indigo-800">
                  <h3 className="text-sm sm:text-base font-medium text-indigo-900 dark:text-indigo-100 mb-2">
                    🚀 Next Steps
                  </h3>
                  <ul className="text-xs sm:text-sm text-indigo-800 dark:text-indigo-200 space-y-1">
                    <li>• Practice behavioral questions</li>
                    <li>• Record yourself for review</li>
                    <li>• Focus on leadership examples</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center mt-6 sm:mt-8">
          <Button variant="outline" className="flex items-center space-x-2 w-full sm:w-auto">
            <FileText className="w-4 h-4" />
            <span>Download Report</span>
          </Button>
          <Button onClick={() => {
            setCurrentStep('setup');
            setTimer(0);
            setCurrentQuestionIndex(0);
          }} className="w-full sm:w-auto">
            <Bot className="w-4 h-4 mr-2" />
            Start New Interview
          </Button>
          <Button variant="secondary" className="w-full sm:w-auto">
            <Award className="w-4 h-4 mr-2" />
            Share Results
          </Button>
        </div>
      </div>
    </div>
  );
};