import React from 'react';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { User, Upload, Bot, CheckCircle } from 'lucide-react';

interface Props {
  interviewSetup: any;
  setInterviewSetup: any;
  uploadedFile: File | null;
  isAnalyzing: boolean;
  analysisComplete: boolean;
  handleFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  focusAreaOptions: string[];
  interviewTypes: any[];
  toggleFocusArea: (area: string) => void;
  onNext: () => void;
  validationErrors: string[];
  isLoggedIn: boolean;
  userName?: string;
}

export const Setup: React.FC<Props> = ({
  interviewSetup,
  setInterviewSetup,
  uploadedFile,
  isAnalyzing,
  analysisComplete,
  handleFileUpload,
  focusAreaOptions,
  interviewTypes,
  toggleFocusArea,
  onNext,
  validationErrors,
  isLoggedIn,
  userName
}) => {
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
        {validationErrors.length > 0 && (
          <div className="mb-4">
            {validationErrors.map((err, i) => (
              <div key={i} className="text-red-600 text-sm mb-1">{err}</div>
            ))}
          </div>
        )}
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
                  className={`p-3 sm:p-4 rounded-lg border-2 transition-all ${
                    interviewSetup.resumeSource === 'profile'
                      ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  } ${!isLoggedIn ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                  onClick={() => {
                    if (isLoggedIn) {
                      setInterviewSetup((prev: any) => ({ ...prev, resumeSource: 'profile' }));
                    }
                  }}
                  aria-disabled={!isLoggedIn}
                  tabIndex={isLoggedIn ? 0 : -1}
                  role="button"
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
                      {isLoggedIn ? (
                        <div className="mb-2">
                          <span className="text-xs text-green-600 font-medium">{userName ? `Logged in as ${userName}` : 'Logged in'}</span>
                        </div>
                      ) : (
                        <div className="mb-2">
                          <span className="text-xs text-red-500 font-medium">Log in first to use this feature.</span>
                        </div>
                      )}
                      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-3">
                        AI will analyze your HireWise profile and generate relevant questions
                      </p>
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
                  onClick={() => setInterviewSetup((prev: any) => ({ ...prev, resumeSource: 'upload' }))}
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
                    {interviewTypes.map((type: any) => (
                      <div
                        key={type.id}
                        className={`p-2 sm:p-3 rounded-lg border cursor-pointer transition-all ${
                          interviewSetup.interviewType === type.id
                            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }`}
                        onClick={() => setInterviewSetup((prev: any) => ({ ...prev, interviewType: type.id }))}
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
                    onChange={(e) => setInterviewSetup((prev: any) => ({ ...prev, difficulty: e.target.value }))}
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
                    onChange={(e) => setInterviewSetup((prev: any) => ({ ...prev, duration: parseInt(e.target.value) }))}
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
                    {focusAreaOptions.map((area: string) => (
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
            onClick={onNext} 
            size="lg" 
            className="px-6 sm:px-8 py-3 sm:py-4 w-full sm:w-auto"
            disabled={interviewSetup.resumeSource === 'upload' && !analysisComplete}
          >
            <Bot className="w-5 h-5 mr-2" />
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
};
