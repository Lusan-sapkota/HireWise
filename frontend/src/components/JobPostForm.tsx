import React, { useState } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card, CardContent } from './ui/Card';

interface JobPostFormProps {
  onSubmit: (data: any) => void;
  initialValues?: any;
  loading?: boolean;
}

const defaultValues = {
  title: '',
  description: '',
  requirements: '',
  location: '',
  salary: '',
  aiInterview: false,
  minScore: 70,
};

const JobPostForm: React.FC<JobPostFormProps> = ({ onSubmit, initialValues, loading }) => {
  const [form, setForm] = useState({ ...defaultValues, ...initialValues });
  const [errors, setErrors] = useState<any>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setForm((f) => ({
      ...f,
      [name]: type === 'checkbox'
        ? (e.target as HTMLInputElement).checked
        : value
    }));
  };

  const validate = () => {
    const errs: any = {};
    if (!form.title) errs.title = 'Title is required';
    if (!form.description) errs.description = 'Description is required';
    if (!form.requirements) errs.requirements = 'Requirements are required';
    if (!form.location) errs.location = 'Location is required';
    if (!form.salary) errs.salary = 'Salary is required';
    if (form.aiInterview && (!form.minScore || isNaN(Number(form.minScore)))) errs.minScore = 'Minimum score required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) onSubmit(form);
  };

  return (
    <Card className="max-w-xl mx-auto mt-8">
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block font-medium mb-1">Title</label>
            <Input name="title" value={form.title} onChange={handleChange} disabled={loading} />
            {errors.title && <div className="text-red-500 text-xs mt-1">{errors.title}</div>}
          </div>
          <div>
            <label className="block font-medium mb-1">Description</label>
            <textarea name="description" value={form.description} onChange={handleChange} rows={4} className="w-full p-2 border rounded bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white" disabled={loading} />
            {errors.description && <div className="text-red-500 text-xs mt-1">{errors.description}</div>}
          </div>
          <div>
            <label className="block font-medium mb-1">Requirements</label>
            <textarea name="requirements" value={form.requirements} onChange={handleChange} rows={3} className="w-full p-2 border rounded bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white" disabled={loading} />
            {errors.requirements && <div className="text-red-500 text-xs mt-1">{errors.requirements}</div>}
          </div>
          <div>
            <label className="block font-medium mb-1">Location</label>
            <Input name="location" value={form.location} onChange={handleChange} disabled={loading} />
            {errors.location && <div className="text-red-500 text-xs mt-1">{errors.location}</div>}
          </div>
          <div>
            <label className="block font-medium mb-1">Salary</label>
            <Input name="salary" value={form.salary} onChange={handleChange} disabled={loading} />
            {errors.salary && <div className="text-red-500 text-xs mt-1">{errors.salary}</div>}
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" name="aiInterview" checked={form.aiInterview} onChange={handleChange} disabled={loading} id="aiInterview" />
            <label htmlFor="aiInterview" className="font-medium">Enable AI Interview</label>
          </div>
          {form.aiInterview && (
            <div>
              <label className="block font-medium mb-1">Minimum AI Interview Score (%)</label>
              <Input name="minScore" type="number" value={form.minScore} onChange={handleChange} disabled={loading} min={0} max={100} />
              {errors.minScore && <div className="text-red-500 text-xs mt-1">{errors.minScore}</div>}
            </div>
          )}
          <Button type="submit" className="w-full" disabled={loading}>{loading ? 'Posting...' : 'Post Job'}</Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default JobPostForm;
