import React from 'react';
import { Card, CardContent } from '../components/ui/Card';

interface JobDetailProps {
  job: any;
  onClose: () => void;
}

const JobDetail: React.FC<JobDetailProps> = ({ job, onClose }) => {
  if (!job) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg max-w-2xl w-full mx-4">
        <Card>
          <CardContent className="p-6">
            <button onClick={onClose} className="float-right text-gray-400 hover:text-gray-700 dark:hover:text-white">✕</button>
            <div className="flex items-center mb-4">
              <img src={job.logo} alt={job.company} className="w-14 h-14 rounded-lg mr-4" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{job.title}</h2>
                <p className="text-gray-600 dark:text-gray-300">{job.company} • {job.location}</p>
              </div>
            </div>
            <div className="mb-4">
              <span className="inline-block bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 px-3 py-1 rounded-full text-xs font-medium mr-2">{job.type}</span>
              <span className="inline-block bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 px-3 py-1 rounded-full text-xs font-medium">{job.salary}</span>
            </div>
            <div className="mb-4">
              <h3 className="font-semibold text-lg mb-1">Job Description</h3>
              <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">{job.description}</p>
            </div>
            <div className="mb-4">
              <h3 className="font-semibold text-lg mb-1">Requirements</h3>
              <ul className="list-disc pl-5 text-gray-700 dark:text-gray-300">
                {job.requirements?.map((req: string, idx: number) => (
                  <li key={idx}>{req}</li>
                ))}
              </ul>
            </div>
            {job.aiInterview && (
              <div className="mb-4">
                <span className="inline-flex items-center px-3 py-1 rounded-full bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 text-xs font-medium">
                  🤖 AI Interview Required
                </span>
              </div>
            )}
            <button onClick={onClose} className="mt-4 w-full py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700">Close</button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default JobDetail;
