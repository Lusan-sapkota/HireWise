import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { 
  Mic, 
  MicOff, 
  Play, 
  Pause, 
  Square, 
  SkipForward, 
  Volume2,
  VolumeX,
  Bot,
  User,
  Clock,
  TrendingUp,
  Eye,
  MessageSquare,
  Activity,
  Zap
} from 'lucide-react';

interface Props {
  interviewSetup: any;
  currentQuestionIndex: number;
  setCurrentQuestionIndex: React.Dispatch<React.SetStateAction<number>>;
  isInterviewActive: boolean;
  setIsInterviewActive: React.Dispatch<React.SetStateAction<boolean>>;
  isRecording: boolean;
  setIsRecording: React.Dispatch<React.SetStateAction<boolean>>;
  timer: number;
  setTimer: React.Dispatch<React.SetStateAction<number>>;
  confidence: number;
  setConfidence: React.Dispatch<React.SetStateAction<number>>;
  isPaused: boolean;
  setIsPaused: React.Dispatch<React.SetStateAction<boolean>>;
  metrics: any;
  setMetrics: React.Dispatch<React.SetStateAction<any>>;
  questions: any[];
  formatTime: (seconds: number) => string;
  endInterview: () => void;
  nextQuestion: () => void;
  toggleRecording: () => void;
  togglePause: () => void;
  getMetricColor: (value: number) => string;
  interviewSession?: any;
}

export const Interview: React.FC<Props> = ({
  interviewSetup,
  currentQuestionIndex,
  isInterviewActive,
  isRecording,
  timer,
  confidence,
  isPaused,
  metrics,
  questions,
  formatTime,
  endInterview,
  nextQuestion,
  toggleRecording,
  togglePause,
  getMetricColor
}) => {
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [currentResponse, setCurrentResponse] = useState('');
  const [aiSpeaking, setAiSpeaking] = useState(false);
  const [micPermission, setMicPermission] = useState<'granted' | 'denied' | 'prompt'>('prompt');
  const [audioLevel, setAudioLevel] = useState(0);
  const [conversationHistory, setConversationHistory] = useState<Array<{
    type: 'ai' | 'user';
    content: string;
    timestamp: Date;
  }>>([]);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const speechSynthesisRef = useRef<SpeechSynthesisUtterance | null>(null);
  const recognitionRef = useRef<any>(null);

  const currentQuestion = questions[currentQuestionIndex];

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(finalTranscript + interimTranscript);
        if (finalTranscript) {
          setCurrentResponse(prev => prev + finalTranscript);
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  // Request microphone permission and setup audio analysis
  const requestMicrophoneAccess = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      setMicPermission('granted');
      
      // Setup audio context for level monitoring
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);
      
      microphoneRef.current.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;
      
      // Setup media recorder
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioChunks(prev => [...prev, event.data]);
        }
      };
      
      setMediaRecorder(recorder);
      
      // Start audio level monitoring
      monitorAudioLevel();
      
    } catch (error) {
      console.error('Microphone access denied:', error);
      setMicPermission('denied');
    }
  };

  // Monitor audio input level
  const monitorAudioLevel = () => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const updateLevel = () => {
      if (analyserRef.current && isListening) {
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average);
        requestAnimationFrame(updateLevel);
      }
    };
    
    updateLevel();
  };

  // Start/stop speech recognition
  const toggleSpeechRecognition = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
      monitorAudioLevel();
    }
  };

  // AI speech synthesis
  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      // Stop any current speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.8;
      
      // Try to use a more natural voice
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(voice => 
        voice.name.includes('Google') || 
        voice.name.includes('Microsoft') ||
        voice.lang.startsWith('en')
      );
      
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      utterance.onstart = () => setAiSpeaking(true);
      utterance.onend = () => setAiSpeaking(false);
      utterance.onerror = () => setAiSpeaking(false);

      speechSynthesisRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Speak current question when it changes
  useEffect(() => {
    if (currentQuestion && isInterviewActive) {
      const questionText = currentQuestion.question || currentQuestion;
      speakText(questionText);
      
      // Add to conversation history
      setConversationHistory(prev => [...prev, {
        type: 'ai',
        content: questionText,
        timestamp: new Date()
      }]);
    }
  }, [currentQuestionIndex, currentQuestion, isInterviewActive]);

  // Submit response and move to next question
  const submitResponse = () => {
    if (currentResponse.trim()) {
      // Add user response to conversation history
      setConversationHistory(prev => [...prev, {
        type: 'user',
        content: currentResponse,
        timestamp: new Date()
      }]);

      // Simulate AI feedback
      const feedbackMessages = [
        "Great answer! I can see you have strong experience in this area.",
        "Interesting perspective. Can you elaborate on that approach?",
        "Good example. Your communication skills are showing well.",
        "I appreciate the specific details you provided.",
        "That's a solid response. Let's move to the next question."
      ];
      
      const feedback = feedbackMessages[Math.floor(Math.random() * feedbackMessages.length)];
      
      setTimeout(() => {
        speakText(feedback);
        setConversationHistory(prev => [...prev, {
          type: 'ai',
          content: feedback,
          timestamp: new Date()
        }]);
        
        setTimeout(() => {
          nextQuestion();
          setCurrentResponse('');
          setTranscript('');
        }, 3000);
      }, 1000);
    }
  };

  // Initialize microphone on component mount
  useEffect(() => {
    if (isInterviewActive && micPermission === 'prompt') {
      requestMicrophoneAccess();
    }
  }, [isInterviewActive]);

  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Bot className="w-16 h-16 text-indigo-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Loading Interview Questions...
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Please wait while we prepare your personalized interview.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Bot className="w-8 h-8 text-indigo-600" />
                <div>
                  <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                    AI Interview Session
                  </h1>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <Clock className="w-4 h-4" />
                <span>{formatTime(timer)}</span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button onClick={togglePause} variant="outline" size="sm">
                  {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                </Button>
                <Button onClick={endInterview} variant="outline" size="sm">
                  <Square className="w-4 h-4 mr-2" />
                  End Interview
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Main Interview Area */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Current Question */}
            <Card className="border-2 border-indigo-200 dark:border-indigo-800">
              <CardContent className="p-8">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                      aiSpeaking ? 'bg-green-100 dark:bg-green-900' : 'bg-indigo-100 dark:bg-indigo-900'
                    }`}>
                      <Bot className={`w-6 h-6 ${
                        aiSpeaking ? 'text-green-600 dark:text-green-400' : 'text-indigo-600 dark:text-indigo-400'
                      }`} />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="font-semibold text-gray-900 dark:text-white">AI Interviewer</h3>
                      {aiSpeaking && (
                        <div className="flex items-center space-x-1">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-xs text-green-600 dark:text-green-400">Speaking...</span>
                        </div>
                      )}
                    </div>
                    <p className="text-lg text-gray-800 dark:text-gray-200 leading-relaxed">
                      {currentQuestion.question || currentQuestion}
                    </p>
                  </div>
                  <Button
                    onClick={() => speakText(currentQuestion.question || currentQuestion)}
                    variant="ghost"
                    size="sm"
                    className="flex-shrink-0"
                  >
                    {aiSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Voice Input Area */}
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  {micPermission === 'denied' ? (
                    <div className="py-8">
                      <MicOff className="w-16 h-16 text-red-500 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Microphone Access Required
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Please enable microphone access to participate in the voice interview.
                      </p>
                      <Button onClick={requestMicrophoneAccess}>
                        Enable Microphone
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* Microphone Button */}
                      <div className="relative">
                        <button
                          onClick={toggleSpeechRecognition}
                          className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-200 ${
                            isListening
                              ? 'bg-red-500 hover:bg-red-600 shadow-lg scale-110'
                              : 'bg-indigo-600 hover:bg-indigo-700 shadow-md'
                          }`}
                        >
                          {isListening ? (
                            <MicOff className="w-8 h-8 text-white" />
                          ) : (
                            <Mic className="w-8 h-8 text-white" />
                          )}
                        </button>
                        
                        {/* Audio Level Indicator */}
                        {isListening && (
                          <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping"></div>
                        )}
                        
                        {/* Audio Level Bar */}
                        {isListening && (
                          <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2">
                            <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-red-500 transition-all duration-100"
                                style={{ width: `${Math.min(audioLevel * 2, 100)}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </div>

                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {isListening ? 'Listening... Speak your answer' : 'Click to start speaking'}
                        </p>
                        
                        {/* Live Transcript */}
                        {transcript && (
                          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Live transcript:</p>
                            <p className="text-gray-900 dark:text-white">{transcript}</p>
                          </div>
                        )}

                        {/* Current Response */}
                        {currentResponse && (
                          <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 mb-4">
                            <p className="text-sm text-indigo-600 dark:text-indigo-400 mb-1">Your response:</p>
                            <p className="text-indigo-900 dark:text-indigo-100">{currentResponse}</p>
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex justify-center space-x-4">
                          <Button
                            onClick={submitResponse}
                            disabled={!currentResponse.trim()}
                            className="px-6"
                          >
                            Submit Answer
                          </Button>
                          <Button
                            onClick={() => {
                              setCurrentResponse('');
                              setTranscript('');
                            }}
                            variant="outline"
                          >
                            Clear
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Conversation History */}
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Conversation History</h3>
                <div className="space-y-4 max-h-64 overflow-y-auto">
                  {conversationHistory.map((message, index) => (
                    <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.type === 'user'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                      }`}>
                        <div className="flex items-center space-x-2 mb-1">
                          {message.type === 'user' ? (
                            <User className="w-4 h-4" />
                          ) : (
                            <Bot className="w-4 h-4" />
                          )}
                          <span className="text-xs opacity-75">
                            {message.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm">{message.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Real-time Metrics */}
          <div className="space-y-6">
            
            {/* Confidence Score */}
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Confidence Score</h3>
                  <div className="relative w-24 h-24 mx-auto mb-4">
                    <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        className="text-gray-200 dark:text-gray-700"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        strokeDasharray={`${2 * Math.PI * 40}`}
                        strokeDashoffset={`${2 * Math.PI * 40 * (1 - confidence / 100)}`}
                        className="text-emerald-500 transition-all duration-300"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-2xl font-bold text-gray-900 dark:text-white">
                        {Math.round(confidence)}%
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {confidence >= 85 ? 'Excellent!' : confidence >= 70 ? 'Good' : 'Keep going!'}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Real-time Metrics */}
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Performance Metrics</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Eye className="w-4 h-4 text-blue-500" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">Eye Contact</span>
                    </div>
                    <span className={`text-sm font-medium ${getMetricColor(metrics.eyeContact)}`}>
                      {Math.round(metrics.eyeContact)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <MessageSquare className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">Speaking Pace</span>
                    </div>
                    <span className={`text-sm font-medium ${getMetricColor(metrics.speakingPace)}`}>
                      {Math.round(metrics.speakingPace)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Volume2 className="w-4 h-4 text-purple-500" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">Clarity</span>
                    </div>
                    <span className={`text-sm font-medium ${getMetricColor(metrics.clarity)}`}>
                      {Math.round(metrics.clarity)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Zap className="w-4 h-4 text-yellow-500" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">Enthusiasm</span>
                    </div>
                    <span className={`text-sm font-medium ${getMetricColor(metrics.enthusiasm)}`}>
                      {Math.round(metrics.enthusiasm)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Activity className="w-4 h-4 text-red-500" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">Body Language</span>
                    </div>
                    <span className={`text-sm font-medium ${getMetricColor(metrics.bodyLanguage)}`}>
                      {Math.round(metrics.bodyLanguage)}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <Button 
                    onClick={() => speakText(currentQuestion.question || currentQuestion)}
                    variant="outline" 
                    className="w-full justify-start"
                    size="sm"
                  >
                    <Volume2 className="w-4 h-4 mr-2" />
                    Repeat Question
                  </Button>
                  
                  <Button 
                    onClick={() => {
                      if (currentQuestionIndex < questions.length - 1) {
                        nextQuestion();
                      }
                    }}
                    variant="outline" 
                    className="w-full justify-start"
                    size="sm"
                    disabled={currentQuestionIndex >= questions.length - 1}
                  >
                    <SkipForward className="w-4 h-4 mr-2" />
                    Skip Question
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
