import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const emptyEducation = { degree: '', institution: '', year: '', description: '' };
const emptyLanguage = { language: '', proficiency: '' };
const emptyWorkExperience = { 
  jobTitle: '', 
  company: '', 
  location: '', 
  startDate: '', 
  endDate: '', 
  current: false,
  description: '' 
};
const emptyProject = { 
  title: '', 
  description: '', 
  technologies: '', 
  link: '', 
  startDate: '', 
  endDate: '' 
};
const emptyCertification = { 
  name: '', 
  organization: '', 
  issueDate: '', 
  expiryDate: '', 
  credentialId: '' 
};
const emptyAward = { 
  title: '', 
  organization: '', 
  date: '', 
  description: '' 
};
const emptyVolunteer = { 
  role: '', 
  organization: '', 
  location: '', 
  startDate: '', 
  endDate: '', 
  description: '' 
};

const CompleteProfile: React.FC = () => {
  const { user } = useAuth();
  const [darkMode, setDarkMode] = useState(false);
  const [form, setForm] = useState({
    fullName: '',
    mainRole: '',
    headline: '',
    professionalSummary: '',
    bio: '',
    location: '',
    currentPosition: '',
    company: '',
    skills: [{ name: '', proficiency: 'Intermediate' }],
    languages: [emptyLanguage],
    education: [emptyEducation],
    workExperience: [emptyWorkExperience],
    projects: [emptyProject],
    certifications: [emptyCertification],
    awards: [emptyAward],
    volunteerExperience: [emptyVolunteer],
    linkedin: '',
    github: '',
    portfolio: '',
    personalWebsite: '',
    twitter: '',
    availability: '',
    noticePeriod: '',
    references: '',
  });
  const [profilePicture, setProfilePicture] = useState<File | null>(null);
  const [profilePictureUrl, setProfilePictureUrl] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Initialize dark mode from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setDarkMode(true);
      document.documentElement.classList.add('dark');
    } else {
      setDarkMode(false);
      document.documentElement.classList.remove('dark');
    }
  }, []);

  // Toggle dark mode
  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  // Prefill fullName and profile picture from user (Google or form)
  useEffect(() => {
    if (user) {
      setForm((prev) => ({
        ...prev,
        fullName: user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.username || '',
      }));
      if (user.profile_picture) {
        setProfilePictureUrl(user.profile_picture);
      } else if ((window as any).googleUser && (window as any).googleUser.picture) {
        setProfilePictureUrl((window as any).googleUser.picture);
      }
    }
  }, [user]);

  // Handle simple fields
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // Profile picture
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setProfilePicture(e.target.files[0]);
    }
  };

  // Generic handler for array fields
  const handleArrayFieldChange = (
    fieldName: string,
    idx: number,
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const updated = [...(form as any)[fieldName]];
    if (e.target.type === 'checkbox') {
      updated[idx][e.target.name] = (e.target as HTMLInputElement).checked;
    } else {
      updated[idx][e.target.name] = e.target.value;
    }
    setForm({ ...form, [fieldName]: updated });
  };

  const addArrayField = (fieldName: string, emptyObj: any) => {
    setForm({ ...form, [fieldName]: [...(form as any)[fieldName], emptyObj] });
  };

  const removeArrayField = (fieldName: string, idx: number) => {
    setForm({ ...form, [fieldName]: (form as any)[fieldName].filter((_: any, i: number) => i !== idx) });
  };

  // Skills with proficiency
  const handleSkillChange = (idx: number, field: string, value: string) => {
    const updated = [...form.skills];
    updated[idx][field as keyof typeof updated[0]] = value;
    setForm({ ...form, skills: updated });
  };

  // Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      console.log('Form data:', form);
      console.log('Profile picture:', profilePicture);
      await new Promise((res) => setTimeout(res, 1000));
      window.location.href = '/dashboard';
    } catch {
      setError('Failed to complete profile.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 px-4 py-8 transition-colors duration-200">
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md max-w-6xl mx-auto transition-colors duration-200">
        
        {/* Header with Theme Toggle */}
        <div className="flex justify-center items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white text-center">Complete Your Professional Profile</h2>
        </div>
        
        {/* Profile Picture */}
        <div className="flex justify-center mb-8">
          <div className="relative w-32 h-32">
            {profilePicture ? (
              <img src={URL.createObjectURL(profilePicture)} alt="Profile" className="rounded-full w-full h-full object-cover border-4 border-indigo-200 dark:border-indigo-400" />
            ) : profilePictureUrl ? (
              <img src={profilePictureUrl} alt="Profile" className="rounded-full w-full h-full object-cover border-4 border-indigo-200 dark:border-indigo-400" />
            ) : (
              <div className="bg-gray-200 dark:bg-gray-600 rounded-full w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-300 text-5xl border-4 border-gray-300 dark:border-gray-500">?</div>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="absolute top-0 left-0 opacity-0 w-full h-full cursor-pointer"
              title="Upload profile picture"
            />
            <div className="absolute bottom-0 right-0 bg-indigo-600 dark:bg-indigo-500 text-white rounded-full p-2 cursor-pointer hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
          </div>
        </div>

        <div className="space-y-8">
          {/* Basic Information */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Full Name *</label>
                <input
                  name="fullName"
                  value={form.fullName}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                  required
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Main Role</label>
                <input
                  name="mainRole"
                  placeholder="e.g. Software Engineer, Teacher, Designer"
                  value={form.mainRole}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Professional Headline</label>
                <input
                  name="headline"
                  value={form.headline}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="e.g. Senior Marketing Specialist"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Location</label>
                <input
                  name="location"
                  value={form.location}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="City, Country"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Availability</label>
                <select
                  name="availability"
                  value={form.availability}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                >
                  <option value="">Select availability</option>
                  <option value="Immediately">Immediately</option>
                  <option value="1 week">1 week</option>
                  <option value="2 weeks">2 weeks</option>
                  <option value="1 month">1 month</option>
                  <option value="2+ months">2+ months</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Professional Summary</label>
                <textarea
                  name="professionalSummary"
                  value={form.professionalSummary}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  rows={3}
                  placeholder="Brief professional summary highlighting your experience and expertise"
                />
              </div>
            </div>
          </section>

          {/* Work Experience */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Work Experience</h3>
            {form.workExperience.map((exp, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4 bg-gray-50 dark:bg-gray-700/50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <input
                    name="jobTitle"
                    value={exp.jobTitle}
                    onChange={(e) => handleArrayFieldChange('workExperience', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Job Title"
                  />
                  <input
                    name="company"
                    value={exp.company}
                    onChange={(e) => handleArrayFieldChange('workExperience', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Company Name"
                  />
                  <input
                    name="location"
                    value={exp.location}
                    onChange={(e) => handleArrayFieldChange('workExperience', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Location"
                  />
                  <div className="flex gap-2 items-center">
                    <input
                      name="startDate"
                      type="month"
                      value={exp.startDate}
                      onChange={(e) => handleArrayFieldChange('workExperience', idx, e)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                    />
                    <input
                      name="endDate"
                      type="month"
                      value={exp.endDate}
                      onChange={(e) => handleArrayFieldChange('workExperience', idx, e)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                      disabled={exp.current}
                    />
                    <label className="flex items-center text-gray-700 dark:text-gray-300">
                      <input
                        name="current"
                        type="checkbox"
                        checked={exp.current}
                        onChange={(e) => handleArrayFieldChange('workExperience', idx, e)}
                        className="mr-2 text-indigo-600 focus:ring-indigo-500"
                      />
                      Current
                    </label>
                  </div>
                </div>
                <textarea
                  name="description"
                  value={exp.description}
                  onChange={(e) => handleArrayFieldChange('workExperience', idx, e)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 mb-2 transition-colors"
                  rows={3}
                  placeholder="Job responsibilities and achievements"
                />
                <button
                  type="button"
                  className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  onClick={() => removeArrayField('workExperience', idx)}
                  disabled={form.workExperience.length === 1}
                >
                  Remove Experience
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
              onClick={() => addArrayField('workExperience', emptyWorkExperience)}
            >
              + Add Work Experience
            </button>
          </section>

          {/* Skills */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Skills</h3>
            {form.skills.map((skill, idx) => (
              <div key={idx} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={skill.name}
                  onChange={(e) => handleSkillChange(idx, 'name', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="Skill name"
                />
                <select
                  value={skill.proficiency}
                  onChange={(e) => handleSkillChange(idx, 'proficiency', e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                >
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                  <option value="Expert">Expert</option>
                </select>
                <button
                  type="button"
                  className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  onClick={() => removeArrayField('skills', idx)}
                  disabled={form.skills.length === 1}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
              onClick={() => addArrayField('skills', { name: '', proficiency: 'Intermediate' })}
            >
              + Add Skill
            </button>
          </section>

          {/* Education */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Education</h3>
            {form.education.map((ed, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4 bg-gray-50 dark:bg-gray-700/50">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <input
                    name="degree"
                    value={ed.degree}
                    onChange={(e) => handleArrayFieldChange('education', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Degree/Qualification"
                  />
                  <input
                    name="institution"
                    value={ed.institution}
                    onChange={(e) => handleArrayFieldChange('education', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Institution"
                  />
                  <input
                    name="year"
                    value={ed.year}
                    onChange={(e) => handleArrayFieldChange('education', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Year (e.g., 2018-2022)"
                  />
                </div>
                <textarea
                  name="description"
                  value={ed.description}
                  onChange={(e) => handleArrayFieldChange('education', idx, e)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 mb-2 transition-colors"
                  rows={2}
                  placeholder="Additional details (optional)"
                />
                <button
                  type="button"
                  className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  onClick={() => removeArrayField('education', idx)}
                  disabled={form.education.length === 1}
                >
                  Remove Education
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
              onClick={() => addArrayField('education', emptyEducation)}
            >
              + Add Education
            </button>
          </section>

          {/* Projects */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Projects</h3>
            {form.projects.map((project, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4 bg-gray-50 dark:bg-gray-700/50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <input
                    name="title"
                    value={project.title}
                    onChange={(e) => handleArrayFieldChange('projects', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Project Title"
                  />
                  <input
                    name="link"
                    value={project.link}
                    onChange={(e) => handleArrayFieldChange('projects', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Project URL (optional)"
                  />
                  <input
                    name="technologies"
                    value={project.technologies}
                    onChange={(e) => handleArrayFieldChange('projects', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Technologies used"
                  />
                  <div className="flex gap-2">
                    <input
                      name="startDate"
                      type="month"
                      value={project.startDate}
                      onChange={(e) => handleArrayFieldChange('projects', idx, e)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                    />
                    <input
                      name="endDate"
                      type="month"
                      value={project.endDate}
                      onChange={(e) => handleArrayFieldChange('projects', idx, e)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                    />
                  </div>
                </div>
                <textarea
                  name="description"
                  value={project.description}
                  onChange={(e) => handleArrayFieldChange('projects', idx, e)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 mb-2 transition-colors"
                  rows={3}
                  placeholder="Project description and your role"
                />
                <button
                  type="button"
                  className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  onClick={() => removeArrayField('projects', idx)}
                  disabled={form.projects.length === 1}
                >
                  Remove Project
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
              onClick={() => addArrayField('projects', emptyProject)}
            >
              + Add Project
            </button>
          </section>

          {/* Certifications */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Certifications</h3>
            {form.certifications.map((cert, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4 bg-gray-50 dark:bg-gray-700/50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <input
                    name="name"
                    value={cert.name}
                    onChange={(e) => handleArrayFieldChange('certifications', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Certification Name"
                  />
                  <input
                    name="organization"
                    value={cert.organization}
                    onChange={(e) => handleArrayFieldChange('certifications', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Issuing Organization"
                  />
                  <input
                    name="issueDate"
                    type="month"
                    value={cert.issueDate}
                    onChange={(e) => handleArrayFieldChange('certifications', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                  />
                  <input
                    name="expiryDate"
                    type="month"
                    value={cert.expiryDate}
                    onChange={(e) => handleArrayFieldChange('certifications', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Expiry (optional)"
                  />
                  <input
                    name="credentialId"
                    value={cert.credentialId}
                    onChange={(e) => handleArrayFieldChange('certifications', idx, e)}
                    className="md:col-span-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Credential ID (optional)"
                  />
                </div>
                <button
                  type="button"
                  className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 mt-2 transition-colors"
                  onClick={() => removeArrayField('certifications', idx)}
                  disabled={form.certifications.length === 1}
                >
                  Remove Certification
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
              onClick={() => addArrayField('certifications', emptyCertification)}
            >
              + Add Certification
            </button>
          </section>

          {/* Languages */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Languages</h3>
            {form.languages.map((lang, idx) => (
              <div key={idx} className="flex gap-2 mb-2">
                <input
                  name="language"
                  value={lang.language}
                  onChange={(e) => handleArrayFieldChange('languages', idx, e)}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="Language"
                />
                <select
                  name="proficiency"
                  value={lang.proficiency}
                  onChange={(e) => handleArrayFieldChange('languages', idx, e)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                >
                  <option value="">Proficiency</option>
                  <option value="Native">Native</option>
                  <option value="Fluent">Fluent</option>
                  <option value="Professional">Professional</option>
                  <option value="Conversational">Conversational</option>
                  <option value="Basic">Basic</option>
                </select>
                <button
                  type="button"
                  className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  onClick={() => removeArrayField('languages', idx)}
                  disabled={form.languages.length === 1}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
              onClick={() => addArrayField('languages', emptyLanguage)}
            >
              + Add Language
            </button>
          </section>

          {/* Awards & Honors */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Awards & Honors</h3>
            {form.awards.map((award, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4 bg-gray-50 dark:bg-gray-700/50">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <input
                    name="title"
                    value={award.title}
                    onChange={(e) => handleArrayFieldChange('awards', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Award Title"
                  />
                  <input
                    name="organization"
                    value={award.organization}
                    onChange={(e) => handleArrayFieldChange('awards', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Issuing Organization"
                  />
                  <input
                    name="date"
                    type="month"
                    value={award.date}
                    onChange={(e) => handleArrayFieldChange('awards', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                  />
                </div>
                <textarea
                  name="description"
                  value={award.description}
                  onChange={(e) => handleArrayFieldChange('awards', idx, e)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 mb-2 transition-colors"
                  rows={2}
                  placeholder="Award description (optional)"
                />
                <button
                  type="button"
                  className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  onClick={() => removeArrayField('awards', idx)}
                  disabled={form.awards.length === 1}
                >
                  Remove Award
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
              onClick={() => addArrayField('awards', emptyAward)}
            >
              + Add Award
            </button>
          </section>

          {/* Volunteer Experience */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Volunteer Experience</h3>
            {form.volunteerExperience.map((vol, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4 bg-gray-50 dark:bg-gray-700/50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <input
                    name="role"
                    value={vol.role}
                    onChange={(e) => handleArrayFieldChange('volunteerExperience', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Volunteer Role"
                  />
                  <input
                    name="organization"
                    value={vol.organization}
                    onChange={(e) => handleArrayFieldChange('volunteerExperience', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Organization"
                  />
                  <input
                    name="location"
                    value={vol.location}
                    onChange={(e) => handleArrayFieldChange('volunteerExperience', idx, e)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                    placeholder="Location"
                  />
                  <div className="flex gap-2">
                    <input
                      name="startDate"
                      type="month"
                      value={vol.startDate}
                      onChange={(e) => handleArrayFieldChange('volunteerExperience', idx, e)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                    />
                    <input
                      name="endDate"
                      type="month"
                      value={vol.endDate}
                      onChange={(e) => handleArrayFieldChange('volunteerExperience', idx, e)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                    />
                  </div>
                </div>
                <textarea
                  name="description"
                  value={vol.description}
                  onChange={(e) => handleArrayFieldChange('volunteerExperience', idx, e)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 mb-2 transition-colors"
                  rows={3}
                  placeholder="Volunteer activities and impact"
                />
                <button
                  type="button"
                  className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  onClick={() => removeArrayField('volunteerExperience', idx)}
                  disabled={form.volunteerExperience.length === 1}
                >
                  Remove Volunteer Experience
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
              onClick={() => addArrayField('volunteerExperience', emptyVolunteer)}
            >
              + Add Volunteer Experience
            </button>
          </section>

          {/* Contact & Links */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Contact & Social Links</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">LinkedIn URL</label>
                <input
                  name="linkedin"
                  type="url"
                  value={form.linkedin}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="https://linkedin.com/in/yourprofile"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">GitHub URL</label>
                <input
                  name="github"
                  type="url"
                  value={form.github}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="https://github.com/yourusername"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Portfolio URL</label>
                <input
                  name="portfolio"
                  type="url"
                  value={form.portfolio}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="https://yourportfolio.com"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Personal Website</label>
                <input
                  name="personalWebsite"
                  type="url"
                  value={form.personalWebsite}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="https://yourwebsite.com"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Twitter/X URL</label>
                <input
                  name="twitter"
                  type="url"
                  value={form.twitter}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="https://twitter.com/yourusername"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Notice Period</label>
                <input
                  name="noticePeriod"
                  value={form.noticePeriod}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  placeholder="e.g. 30 days, Immediate"
                />
              </div>
            </div>
          </section>

          {/* Additional Information */}
          <section>
            <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">Additional Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Personal Bio</label>
                <textarea
                  name="bio"
                  value={form.bio}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  rows={3}
                  placeholder="Personal interests and additional information about yourself"
                />
              </div>
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">References (Optional)</label>
                <textarea
                  name="references"
                  value={form.references}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                  rows={3}
                  placeholder="Professional references with contact information"
                />
              </div>
            </div>
          </section>
        </div>

        {error && <div className="text-red-500 dark:text-red-400 mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">{error}</div>}
        
        <div className="mt-8 flex justify-center">
          <button
            type="submit"
            disabled={submitting}
            className="bg-indigo-600 dark:bg-indigo-500 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors font-medium text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Submitting...' : 'Complete Profile'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CompleteProfile;
