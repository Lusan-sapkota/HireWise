import React from 'react';

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
  mockAIQuestions: string[];
  formatTime: (seconds: number) => string;
  endInterview: () => void;
  nextQuestion: () => void;
  toggleRecording: () => void;
  togglePause: () => void;
  getMetricColor: (value: number) => string;
}

export const Interview: React.FC<Props> = ({
  currentQuestionIndex,
  mockAIQuestions
}) => {
  return (
    <div>
      {/* Interview UI goes here */}
      <div>
        <strong>Question {currentQuestionIndex + 1}:</strong> {mockAIQuestions[currentQuestionIndex]}
      </div>
    </div>
  );
};
