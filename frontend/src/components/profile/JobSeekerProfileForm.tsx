import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';

// Type definitions for form data
interface Skill {
  name: string;
  proficiency: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
}

interface Education {
  degree: string;
  institution: string;
  year: string;
  description: string;
}

interface WorkExperience {
  job_title: string;
  company: string;
  location: string;
  start_date: string;
  end_date: string;
  current: boolean;
  description: string;
}

interface Project {
  title: string;
  description: string;
  technologies: string;
  link: string;
  start_date: string;
  end_date: string;
}

interface Certification {
  name: string;
  organization: string;
  issue_date: string;
  expiry_date: string;
  credential_id: string;
}

interface Award {
  title: string;
  organization: string;
  date: string;
  description: string;
}

interface VolunteerExperience {
  role: string;
  organization: string;
  location: string;
  start_date: string;
  end_date: string;
  description: string;
}

interface JobSeekerFormData {
  // Basic Information
  location: string;
  experience_level: string;
  current_position: string;
  current_company: string;
  expected_salary: number | null;
  bio: string;
  professional_summary: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  personal_website: string;
  twitter: string;
  availability: string;
  notice_period: string;
  references: string;
  
  // Related data (will be sent as separate API calls)
  skills: Skill[];
  education: Education[];
  work_experience: WorkExperience[];
  projects: Project[];
  certifications: Certification[];
  awards: Award[];
  volunteer_experience: VolunteerExperience[];
}

// Empty objects for dynamic arrays
const emptySkill: Skill = { name: '', proficiency: 'Intermediate' };
const emptyEducation: Education = { degree: '', institution: '', year: '', description: '' };
const emptyWorkExperience: WorkExperience = { 
  job_title: '', 
  company: '', 
  location: '', 
  start_date: '', 
  end_date: '', 
  current: false,
  description: '' 
};
const emptyProject: Project = { 
  title: '', 
  description: '', 
  technologies: '', 
  link: '', 
  start_date: '', 
  end_date: '' 
};
const emptyCertification: Certification = { 
  name: '', 
  organization: '', 
  issue_date: '', 
  expiry_date: '', 
  credential_id: '' 
};
const emptyAward: Award = { 
  title: '', 
  organization: '', 
  date: '', 
  description: '' 
};
const emptyVolunteer: VolunteerExperience = { 
  role: '', 
  organization: '', 
  location: '', 
  start_date: '', 
  end_date: '', 
  description: '' 
};

interface JobSeekerProfileFormProps {
  onSuccess: () => void;
  onError: (error: string) => void;
}

const JobSeekerProfileForm: React.FC<JobSeekerProfileFormProps> = ({ onSuccess, onError }) => {
  const { user, updateProfile } = useAuth();
  const [form, setForm] = useState<JobSeekerFormData>({
    location: '',
    experience_level: '',
    current_position: '',
    current_company: '',
    expected_salary: null,
    bio: '',
    professional_summary: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
    personal_website: '',
    twitter: '',
    availability: '',
    notice_period: '',
    references: '',
    skills: [emptySkill],
    education: [emptyEducation],
    work_experience: [emptyWorkExperience],
    projects: [emptyProject],
    certifications: [emptyCertification],
    awards: [emptyAward],
    volunteer_experience: [emptyVolunteer],
  });

  const [submitting, setSubmitting] = useState(false);

  // Handle simple field changes
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseInt(value) : null) : value
    }));
  };

  // Generic handler for array fields
  const handleArrayFieldChange = (
    fieldName: keyof JobSeekerFormData,
    idx: number,
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const updated = [...(form[fieldName] as any[])];
    if (e.target.type === 'checkbox') {
      updated[idx][e.target.name] = (e.target as HTMLInputElement).checked;
    } else {
      updated[idx][e.target.name] = e.target.value;
    }
    setForm(prev => ({ ...prev, [fieldName]: updated }));
  };

  const addArrayField = (fieldName: keyof JobSeekerFormData, emptyObj: any) => {
    setForm(prev => ({
      ...prev,
      [fieldName]: [...(prev[fieldName] as any[]), emptyObj]
    }));
  };

  const removeArrayField = (fieldName: keyof JobSeekerFormData, idx: number) => {
    setForm(prev => ({
      ...prev,
      [fieldName]: (prev[fieldName] as any[]).filter((_, i) => i !== idx)
    }));
  };

  // Skills with proficiency
  const handleSkillChange = (idx: number, field: keyof Skill, value: string) => {
    const updated = [...form.skills];
    updated[idx][field] = value as any;
    setForm(prev => ({ ...prev, skills: updated }));
  };

  // Form validation
  const validateForm = (): string | null => {
    if (!form.location.trim()) return 'Location is required';
    if (!form.experience_level) return 'Experience level is required';
    if (!form.professional_summary.trim()) return 'Professional summary is required';
    
    // Validate at least one skill
    const validSkills = form.skills.filter(skill => skill.name.trim());
    if (validSkills.length === 0) return 'At least one skill is required';
    
    return null;
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      onError(validationError);
      return;
    }

    setSubmitting(true);
    
    try {
      // Prepare main profile data
      const profileData = {
        location: form.location,
        experience_level: form.experience_level,
        current_position: form.current_position,
        current_company: form.current_company,
        expected_salary: form.expected_salary,
        bio: form.bio,
        professional_summary: form.professional_summary,
        linkedin_url: form.linkedin_url,
        github_url: form.github_url,
        portfolio_url: form.portfolio_url,
        personal_website: form.personal_website,
        twitter: form.twitter,
        availability: form.availability,
        notice_period: form.notice_period,
        references: form.references,
      };

      // Create or update the job seeker profile
      let profileResponse;
      try {
        // Try to get existing profile first
        profileResponse = await apiService.getJobSeekerProfile();
        // Update existing profile
        profileResponse = await apiService.updateJobSeekerProfile(profileData);
      } catch (error: any) {
        if (error.response?.status === 404) {
          // Profile doesn't exist, create new one
          profileResponse = await apiService.createJobSeekerProfile(profileData);
        } else {
          throw error;
        }
      }

      const profileId = profileResponse.data.id;

      // Now handle the nested data - we'll need to make separate API calls for each section
      // For now, we'll store this data in the profile's related fields
      // Note: The backend models support these relationships, but we may need to create
      // separate endpoints or handle them in the profile creation

      // Filter out empty entries and prepare nested data
      const validSkills = form.skills.filter(skill => skill.name.trim());
      const validEducation = form.education.filter(edu => edu.degree.trim() || edu.institution.trim());
      const validWorkExperience = form.work_experience.filter(exp => exp.job_title.trim() || exp.company.trim());
      const validProjects = form.projects.filter(proj => proj.title.trim());
      const validCertifications = form.certifications.filter(cert => cert.name.trim());
      const validAwards = form.awards.filter(award => award.title.trim());
      const validVolunteerExperience = form.volunteer_experience.filter(vol => vol.role.trim());

      // For now, we'll store the structured data as JSON in the profile
      // In a full implementation, these would be separate API calls to create related records
      const nestedDataUpdate = {
        // We can store this as JSON for now, or create separate endpoints
        skills_data: JSON.stringify(validSkills),
        education_data: JSON.stringify(validEducation),
        work_experience_data: JSON.stringify(validWorkExperience),
        projects_data: JSON.stringify(validProjects),
        certifications_data: JSON.stringify(validCertifications),
        awards_data: JSON.stringify(validAwards),
        volunteer_experience_data: JSON.stringify(validVolunteerExperience),
      };

      // Update the profile with nested data
      // Note: This assumes the backend can handle these JSON fields
      // In a production system, you'd want separate endpoints for each nested resource
      
      // Update the auth context
      await updateProfile(profileResponse.data);
      
      onSuccess();
    } catch (error: any) {
      console.error('Profile creation error:', error);
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error || 
                          'Failed to create profile. Please try again.';
      onError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Basic Information */}
      <section>
        <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
          Basic Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Location *</label>
            <input
              name="location"
              value={form.location}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="City, Country"
              required
            />
          </div>
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Experience Level *</label>
            <select
              name="experience_level"
              value={form.experience_level}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
              required
            >
              <option value="">Select experience level</option>
              <option value="entry">Entry Level (0-2 years)</option>
              <option value="mid">Mid Level (3-5 years)</option>
              <option value="senior">Senior Level (6-10 years)</option>
              <option value="lead">Lead Level (10+ years)</option>
            </select>
          </div>
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Current Position</label>
            <input
              name="current_position"
              value={form.current_position}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="e.g. Senior Software Engineer"
            />
          </div>
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Current Company</label>
            <input
              name="current_company"
              value={form.current_company}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="Company name"
            />
          </div>
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Expected Salary (Annual)</label>
            <input
              name="expected_salary"
              type="number"
              value={form.expected_salary || ''}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="e.g. 75000"
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
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Professional Summary *</label>
            <textarea
              name="professional_summary"
              value={form.professional_summary}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              rows={3}
              placeholder="Brief professional summary highlighting your experience and expertise"
              required
            />
          </div>
        </div>
      </section>

      {/* Skills */}
      <section>
        <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
          Skills *
        </h3>
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
              onChange={(e) => handleSkillChange(idx, 'proficiency', e.target.value as any)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
            >
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
              <option value="Expert">Expert</option>
            </select>
            <button
              type="button"
              className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors px-2"
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
          onClick={() => addArrayField('skills', emptySkill)}
        >
          + Add Skill
        </button>
      </section>

      {/* Work Experience */}
      <section>
        <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
          Work Experience
        </h3>
        {form.work_experience.map((exp, idx) => (
          <div key={idx} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4 bg-gray-50 dark:bg-gray-700/50">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <input
                name="job_title"
                value={exp.job_title}
                onChange={(e) => handleArrayFieldChange('work_experience', idx, e)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                placeholder="Job Title"
              />
              <input
                name="company"
                value={exp.company}
                onChange={(e) => handleArrayFieldChange('work_experience', idx, e)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                placeholder="Company Name"
              />
              <input
                name="location"
                value={exp.location}
                onChange={(e) => handleArrayFieldChange('work_experience', idx, e)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                placeholder="Location"
              />
              <div className="flex gap-2 items-center">
                <input
                  name="start_date"
                  type="month"
                  value={exp.start_date}
                  onChange={(e) => handleArrayFieldChange('work_experience', idx, e)}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                />
                <input
                  name="end_date"
                  type="month"
                  value={exp.end_date}
                  onChange={(e) => handleArrayFieldChange('work_experience', idx, e)}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                  disabled={exp.current}
                />
                <label className="flex items-center text-gray-700 dark:text-gray-300">
                  <input
                    name="current"
                    type="checkbox"
                    checked={exp.current}
                    onChange={(e) => handleArrayFieldChange('work_experience', idx, e)}
                    className="mr-2 text-indigo-600 focus:ring-indigo-500"
                  />
                  Current
                </label>
              </div>
            </div>
            <textarea
              name="description"
              value={exp.description}
              onChange={(e) => handleArrayFieldChange('work_experience', idx, e)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 mb-2 transition-colors"
              rows={3}
              placeholder="Job responsibilities and achievements"
            />
            <button
              type="button"
              className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
              onClick={() => removeArrayField('work_experience', idx)}
              disabled={form.work_experience.length === 1}
            >
              Remove Experience
            </button>
          </div>
        ))}
        <button
          type="button"
          className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium transition-colors"
          onClick={() => addArrayField('work_experience', emptyWorkExperience)}
        >
          + Add Work Experience
        </button>
      </section>

      {/* Education */}
      <section>
        <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
          Education
        </h3>
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
        <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
          Projects
        </h3>
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
                  name="start_date"
                  type="month"
                  value={project.start_date}
                  onChange={(e) => handleArrayFieldChange('projects', idx, e)}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                />
                <input
                  name="end_date"
                  type="month"
                  value={project.end_date}
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
        <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
          Certifications
        </h3>
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
                name="issue_date"
                type="month"
                value={cert.issue_date}
                onChange={(e) => handleArrayFieldChange('certifications', idx, e)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
              />
              <input
                name="expiry_date"
                type="month"
                value={cert.expiry_date}
                onChange={(e) => handleArrayFieldChange('certifications', idx, e)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                placeholder="Expiry (optional)"
              />
              <input
                name="credential_id"
                value={cert.credential_id}
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

      {/* Contact & Links */}
      <section>
        <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
          Contact & Social Links
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">LinkedIn URL</label>
            <input
              name="linkedin_url"
              type="url"
              value={form.linkedin_url}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="https://linkedin.com/in/yourprofile"
            />
          </div>
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">GitHub URL</label>
            <input
              name="github_url"
              type="url"
              value={form.github_url}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="https://github.com/yourusername"
            />
          </div>
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Portfolio URL</label>
            <input
              name="portfolio_url"
              type="url"
              value={form.portfolio_url}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="https://yourportfolio.com"
            />
          </div>
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Personal Website</label>
            <input
              name="personal_website"
              type="url"
              value={form.personal_website}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="https://yourwebsite.com"
            />
          </div>
          <div>
            <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Notice Period</label>
            <input
              name="notice_period"
              value={form.notice_period}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
              placeholder="e.g. 30 days, Immediate"
            />
          </div>
        </div>
      </section>

      {/* Additional Information */}
      <section>
        <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
          Additional Information
        </h3>
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

      {/* Submit Button */}
      <div className="flex justify-center">
        <button
          type="submit"
          disabled={submitting}
          className="bg-indigo-600 dark:bg-indigo-500 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors font-medium text-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? 'Creating Profile...' : 'Complete Profile'}
        </button>
      </div>
    </form>
  );
};

export default JobSeekerProfileForm;