import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../components/ui/Button';

const AIInterviewSetup: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const job = location.state?.job;

  const handleStartInterview = () => {
    // TODO: Call backend to create interview session, then navigate
    navigate('/ai-interview', { state: { job } });
  };


  // If no job, allow general/practice interview

  return (
    <div className="max-w-lg mx-auto mt-10 p-6 bg-white dark:bg-gray-900 rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">AI Interview Setup</h2>
      {job ? (
        <>
          <div className="mb-2 text-gray-800 dark:text-gray-200 font-semibold">{job.title} at {job.company}</div>
          <p className="mb-4 text-gray-700 dark:text-gray-300">This job requires an AI-powered interview. Please ensure you are ready before starting.</p>
        </>
      ) : (
        <p className="mb-4 text-gray-700 dark:text-gray-300">Practice your interview skills with our AI-powered system. You can start a general or technical interview session anytime.</p>
      )}
      <ul className="mb-6 list-disc pl-6 text-gray-700 dark:text-gray-300">
        <li>Find a quiet environment</li>
        <li>Check your internet connection</li>
        <li>Prepare your camera and microphone (if required)</li>
        {job && <li>Have your resume and job description handy</li>}
      </ul>
      <Button onClick={handleStartInterview} className="w-full">Start Interview</Button>
    </div>
  );
};

export default AIInterviewSetup;
