import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
// TODO: Replace with real API/service
const mockCandidates = [
  {
    id: '1',
    name: 'Alex Johnson',
    jobTitle: 'Senior React Developer',
    aiScore: 92,
    resume: 'alex_resume.pdf',
    status: 'Qualified',
    interview: { score: 92, feedback: 'Excellent communication and technical skills.' }
  },
  {
    id: '2',
    name: 'Maria Lee',
    jobTitle: 'Frontend Engineer',
    aiScore: 78,
    resume: 'maria_resume.pdf',
    status: 'Unqualified',
    interview: { score: 78, feedback: 'Good skills, but needs improvement in problem solving.' }
  }
];

const RecruiterCandidates: React.FC = () => {
  const [candidates, setCandidates] = useState(mockCandidates);
  const [filter, setFilter] = useState<'all' | 'qualified' | 'unqualified'>('all');
  const [selected, setSelected] = useState<any | null>(null);

  const filtered = candidates.filter(c =>
    filter === 'all' ? true : filter === 'qualified' ? c.status === 'Qualified' : c.status === 'Unqualified'
  );

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Candidate Applications</h1>
      <div className="mb-4 flex gap-2">
        <Button variant={filter==='all'?undefined:'outline'} onClick={()=>setFilter('all')}>All</Button>
        <Button variant={filter==='qualified'?undefined:'outline'} onClick={()=>setFilter('qualified')}>Qualified</Button>
        <Button variant={filter==='unqualified'?undefined:'outline'} onClick={()=>setFilter('unqualified')}>Unqualified</Button>
      </div>
      <div className="space-y-4">
        {filtered.map(c => (
          <div
            key={c.id}
            className="cursor-pointer"
            onClick={() => setSelected(c)}
          >
            <Card>
              <CardContent className="flex justify-between items-center p-4">
            <div>
              <div className="font-semibold text-lg">{c.name}</div>
              <div className="text-gray-500 text-sm">{c.jobTitle}</div>
            </div>
            <div className="text-right">
              <div className="font-bold text-indigo-600">AI Score: {c.aiScore}</div>
              <div className={`text-xs ${c.status === 'Qualified' ? 'text-emerald-600' : 'text-red-500'}`}>{c.status}</div>
            </div>
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
      {selected && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg max-w-md w-full p-6 relative">
            <button className="absolute top-2 right-2 text-gray-400 hover:text-gray-700" onClick={()=>setSelected(null)}>✕</button>
            <h2 className="text-xl font-bold mb-2">{selected.name}</h2>
            <div className="mb-2 text-gray-600">Applied for: {selected.jobTitle}</div>
            <div className="mb-2">AI Interview Score: <span className="font-semibold">{selected.aiScore}</span></div>
            <div className="mb-2">Status: <span className={`font-semibold ${selected.status==='Qualified'?'text-emerald-600':'text-red-500'}`}>{selected.status}</span></div>
            <div className="mb-2">Resume: <a href={`/${selected.resume}`} className="text-indigo-600 underline">{selected.resume}</a></div>
            <div className="mb-2">Interview Feedback: <span className="italic">{selected.interview.feedback}</span></div>
            <Button className="mt-4 w-full" onClick={()=>setSelected(null)}>Close</Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecruiterCandidates;
