import React from 'react';
import { Button } from '../../components/ui/Button';
import { Bot } from 'lucide-react';

interface InterviewSetup {
    position: string;
    company: string;
    date: string;
    // Add more fields as needed
}

interface InterviewType {
    id: string;
    name: string;
    description: string;
}

interface Props {
    interviewSetup: InterviewSetup;
    interviewTypes: InterviewType[];
    onBack: () => void;
    onStart: () => void;
}

export const PreInterview: React.FC<Props> = ({
    interviewSetup,
    interviewTypes,
    onBack,
    onStart,
}) => {
    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 flex items-center justify-center">
            <div className="max-w-lg w-full bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 sm:p-8 mx-2">
                <div className="text-center mb-6">
                    <Bot className="w-12 h-12 text-violet-600 mx-auto mb-3" />
                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-2">Ready to Begin?</h2>
                    <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300">Review your interview setup below and confirm to start.</p>
                </div>
                {/* Interview Setup Summary */}
                <div className="mb-4">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Interview Setup:</h3>
                    <ul className="list-inside text-gray-700 dark:text-gray-300">
                        <li>
                            <span className="font-medium">Position:</span> {interviewSetup.position}
                        </li>
                        <li>
                            <span className="font-medium">Company:</span> {interviewSetup.company}
                        </li>
                        <li>
                            <span className="font-medium">Date:</span> {interviewSetup.date}
                        </li>
                        {/* Add more fields as needed */}
                    </ul>
                </div>
                {/* Interview Types */}
                <div className="mb-4">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Interview Types:</h3>
                    <ul className="list-disc list-inside text-gray-700 dark:text-gray-300">
                        {interviewTypes.length > 0 ? (
                            interviewTypes.map((type) => (
                                <li key={type.id}>
                                    <span className="font-medium">{type.name}</span>
                                    {type.description && (
                                        <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">({type.description})</span>
                                    )}
                                </li>
                            ))
                        ) : (
                            <li>No interview types selected.</li>
                        )}
                    </ul>
                </div>
                <div className="flex gap-3 mt-6">
                    <Button variant="outline" className="w-1/2" onClick={onBack}>Back</Button>
                    <Button className="w-1/2" onClick={onStart}>
                        <Bot className="w-5 h-5 mr-2" />
                        Begin Interview
                    </Button>
                </div>
            </div>
        </div>
    );
};
