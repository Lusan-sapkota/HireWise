import React, { useState, useRef } from 'react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { apiService } from '../services/api';
import { 
  Download, 
  Upload, 
  Eye, 
  Save, 
  Plus, 
  Trash2, 
  Edit3, 
  FileText, 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Globe, 
  Briefcase, 
  GraduationCap, 
  Award, 
  Code, 
  Languages,
  Bot,
  Sparkles,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

interface PersonalInfo {
  full_name: string;
  email: string;
  phone: string;
  location: string;
  website?: string;
  linkedin?: string;
  github?: string;
  summary: string;
}

interface Experience {
  id: string;
  company: string;
  position: string;
  location: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  description: string;
}

interface Education {
  id: string;
  institution: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date: string;
  gpa?: string;
  description?: string;
}

interface Skill {
  id: string;
  name: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  category: string;
}

interface ResumeData {
  personal_info: PersonalInfo;
  experiences: Experience[];
  education: Education[];
  skills: Skill[];
  languages: string[];
  certifications: string[];
}

export const ResumeBuilder: React.FC = () => {
  const [resumeData, setResumeData] = useState<ResumeData>({
    personal_info: {
      full_name: '',
      email: '',
      phone: '',
      location: '',
      website: '',
      linkedin: '',
      github: '',
      summary: '',
    },
    experiences: [],
    education: [],
    skills: [],
    languages: [],
    certifications: [],
  });

  const [activeSection, setActiveSection] = useState<string>('personal');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sections = [
    { id: 'personal', name: 'Personal Info', icon: User },
    { id: 'experience', name: 'Experience', icon: Briefcase },
    { id: 'education', name: 'Education', icon: GraduationCap },
    { id: 'skills', name: 'Skills', icon: Code },
    { id: 'additional', name: 'Additional', icon: Award },
  ];

  const handlePersonalInfoChange = (field: keyof PersonalInfo, value: string) => {
    setResumeData(prev => ({
      ...prev,
      personal_info: {
        ...prev.personal_info,
        [field]: value,
      },
    }));
  };

  const addExperience = () => {
    const newExperience: Experience = {
      id: Date.now().toString(),
      company: '',
      position: '',
      location: '',
      start_date: '',
      end_date: '',
      is_current: false,
      description: '',
    };
    setResumeData(prev => ({
      ...prev,
      experiences: [...prev.experiences, newExperience],
    }));
  };

  const updateExperience = (id: string, field: keyof Experience, value: any) => {
    setResumeData(prev => ({
      ...prev,
      experiences: prev.experiences.map(exp =>
        exp.id === id ? { ...exp, [field]: value } : exp
      ),
    }));
  };

  const removeExperience = (id: string) => {
    setResumeData(prev => ({
      ...prev,
      experiences: prev.experiences.filter(exp => exp.id !== id),
    }));
  };

  const addEducation = () => {
    const newEducation: Education = {
      id: Date.now().toString(),
      institution: '',
      degree: '',
      field_of_study: '',
      start_date: '',
      end_date: '',
      gpa: '',
      description: '',
    };
    setResumeData(prev => ({
      ...prev,
      education: [...prev.education, newEducation],
    }));
  };

  const updateEducation = (id: string, field: keyof Education, value: string) => {
    setResumeData(prev => ({
      ...prev,
      education: prev.education.map(edu =>
        edu.id === id ? { ...edu, [field]: value } : edu
      ),
    }));
  };

  const removeEducation = (id: string) => {
    setResumeData(prev => ({
      ...prev,
      education: prev.education.filter(edu => edu.id !== id),
    }));
  };

  const addSkill = () => {
    const newSkill: Skill = {
      id: Date.now().toString(),
      name: '',
      level: 'intermediate',
      category: 'Technical',
    };
    setResumeData(prev => ({
      ...prev,
      skills: [...prev.skills, newSkill],
    }));
  };

  const updateSkill = (id: string, field: keyof Skill, value: any) => {
    setResumeData(prev => ({
      ...prev,
      skills: prev.skills.map(skill =>
        skill.id === id ? { ...skill, [field]: value } : skill
      ),
    }));
  };

  const removeSkill = (id: string) => {
    setResumeData(prev => ({
      ...prev,
      skills: prev.skills.filter(skill => skill.id !== id),
    }));
  };

  const generateAISuggestions = async (section: string) => {
    setIsGenerating(true);
    try {
      // TODO: Implement AI suggestions API call
      // const response = await apiService.generateResumeSuggestions(section, resumeData);
      
      // Mock AI suggestions
      const mockSuggestions = [
        "Quantify your achievements with specific numbers and metrics",
        "Use action verbs to start each bullet point",
        "Highlight relevant technologies and frameworks",
        "Include leadership and collaboration experiences",
      ];
      
      setAiSuggestions(mockSuggestions);
    } catch (error) {
      console.error('Failed to generate AI suggestions:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const saveResume = async () => {
    setIsSaving(true);
    try {
      // TODO: Implement save resume API call
      // await apiService.saveResume(resumeData);
      console.log('Resume saved:', resumeData);
    } catch (error) {
      console.error('Failed to save resume:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const exportResume = async (format: 'pdf' | 'docx') => {
    try {
      // TODO: Implement export resume API call
      // const response = await apiService.exportResume(resumeData, format);
      console.log(`Exporting resume as ${format}`);
    } catch (error) {
      console.error('Failed to export resume:', error);
    }
  };

  const importResume = async (file: File) => {
    try {
      // TODO: Implement import resume API call
      // const response = await apiService.parseResume(file);
      console.log('Importing resume:', file.name);
    } catch (error) {
      console.error('Failed to import resume:', error);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      importResume(file);
    }
  };

  const renderPersonalInfoSection = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Full Name *
          </label>
          <Input
            value={resumeData.personal_info.full_name}
            onChange={(e) => handlePersonalInfoChange('full_name', e.target.value)}
            placeholder="John Doe"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email *
          </label>
          <Input
            type="email"
            value={resumeData.personal_info.email}
            onChange={(e) => handlePersonalInfoChange('email', e.target.value)}
            placeholder="john@example.com"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Phone *
          </label>
          <Input
            value={resumeData.personal_info.phone}
            onChange={(e) => handlePersonalInfoChange('phone', e.target.value)}
            placeholder="+1 (555) 123-4567"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Location *
          </label>
          <Input
            value={resumeData.personal_info.location}
            onChange={(e) => handlePersonalInfoChange('location', e.target.value)}
            placeholder="San Francisco, CA"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Website
          </label>
          <Input
            value={resumeData.personal_info.website}
            onChange={(e) => handlePersonalInfoChange('website', e.target.value)}
            placeholder="https://johndoe.com"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            LinkedIn
          </label>
          <Input
            value={resumeData.personal_info.linkedin}
            onChange={(e) => handlePersonalInfoChange('linkedin', e.target.value)}
            placeholder="https://linkedin.com/in/johndoe"
          />
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Professional Summary *
        </label>
        <textarea
          className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
          rows={4}
          value={resumeData.personal_info.summary}
          onChange={(e) => handlePersonalInfoChange('summary', e.target.value)}
          placeholder="Write a compelling summary of your professional background and key achievements..."
        />
      </div>
    </div>
  );

  const renderExperienceSection = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Work Experience</h3>
        <Button onClick={addExperience} size="sm">
          <Plus className="w-4 h-4 mr-2" />
          Add Experience
        </Button>
      </div>
      
      {resumeData.experiences.map((experience, index) => (
        <Card key={experience.id}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-base font-medium text-gray-900 dark:text-white">
                Experience {index + 1}
              </h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeExperience(experience.id)}
                className="text-red-600 hover:text-red-700"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <Input
                placeholder="Company Name"
                value={experience.company}
                onChange={(e) => updateExperience(experience.id, 'company', e.target.value)}
              />
              <Input
                placeholder="Job Title"
                value={experience.position}
                onChange={(e) => updateExperience(experience.id, 'position', e.target.value)}
              />
              <Input
                placeholder="Location"
                value={experience.location}
                onChange={(e) => updateExperience(experience.id, 'location', e.target.value)}
              />
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`current-${experience.id}`}
                  checked={experience.is_current}
                  onChange={(e) => updateExperience(experience.id, 'is_current', e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor={`current-${experience.id}`} className="text-sm text-gray-700 dark:text-gray-300">
                  Current Position
                </label>
              </div>
              <Input
                type="date"
                placeholder="Start Date"
                value={experience.start_date}
                onChange={(e) => updateExperience(experience.id, 'start_date', e.target.value)}
              />
              {!experience.is_current && (
                <Input
                  type="date"
                  placeholder="End Date"
                  value={experience.end_date}
                  onChange={(e) => updateExperience(experience.id, 'end_date', e.target.value)}
                />
              )}
            </div>
            
            <textarea
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              rows={3}
              placeholder="Describe your responsibilities and achievements..."
              value={experience.description}
              onChange={(e) => updateExperience(experience.id, 'description', e.target.value)}
            />
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderSkillsSection = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Skills</h3>
        <Button onClick={addSkill} size="sm">
          <Plus className="w-4 h-4 mr-2" />
          Add Skill
        </Button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {resumeData.skills.map((skill) => (
          <Card key={skill.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <Input
                  placeholder="Skill name"
                  value={skill.name}
                  onChange={(e) => updateSkill(skill.id, 'name', e.target.value)}
                  className="flex-1 mr-2"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeSkill(skill.id)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
              
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={skill.level}
                  onChange={(e) => updateSkill(skill.id, 'level', e.target.value)}
                  className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                  <option value="expert">Expert</option>
                </select>
                
                <Input
                  placeholder="Category"
                  value={skill.category}
                  onChange={(e) => updateSkill(skill.id, 'category', e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Resume Builder</h1>
            <p className="text-gray-600 dark:text-gray-400">Create a professional resume with AI assistance</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.doc,.docx"
              className="hidden"
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="w-4 h-4 mr-2" />
              Import
            </Button>
            <Button
              variant="outline"
              onClick={() => setPreviewMode(!previewMode)}
            >
              <Eye className="w-4 h-4 mr-2" />
              {previewMode ? 'Edit' : 'Preview'}
            </Button>
            <Button onClick={saveResume} disabled={isSaving}>
              <Save className="w-4 h-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
            <Button onClick={() => exportResume('pdf')}>
              <Download className="w-4 h-4 mr-2" />
              Export PDF
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Sections</h3>
              </CardHeader>
              <CardContent className="p-0">
                <nav className="space-y-1">
                  {sections.map((section) => {
                    const Icon = section.icon;
                    return (
                      <button
                        key={section.id}
                        onClick={() => setActiveSection(section.id)}
                        className={`w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                          activeSection === section.id
                            ? 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 border-r-2 border-indigo-500'
                            : 'text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        <span className="font-medium">{section.name}</span>
                      </button>
                    );
                  })}
                </nav>
              </CardContent>
            </Card>

            {/* AI Suggestions */}
            <Card className="mt-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Bot className="w-5 h-5 text-violet-600" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Suggestions</h3>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => generateAISuggestions(activeSection)}
                    disabled={isGenerating}
                  >
                    <Sparkles className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isGenerating ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-violet-600 mx-auto mb-2"></div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Generating suggestions...</p>
                  </div>
                ) : aiSuggestions.length > 0 ? (
                  <div className="space-y-3">
                    {aiSuggestions.map((suggestion, index) => (
                      <div key={index} className="p-3 bg-violet-50 dark:bg-violet-900/20 rounded-lg border border-violet-200 dark:border-violet-800">
                        <p className="text-sm text-violet-800 dark:text-violet-200">{suggestion}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Click the sparkle icon to get AI-powered suggestions for improving your resume.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-9">
            <Card>
              <CardHeader>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {sections.find(s => s.id === activeSection)?.name}
                </h2>
              </CardHeader>
              <CardContent>
                {activeSection === 'personal' && renderPersonalInfoSection()}
                {activeSection === 'experience' && renderExperienceSection()}
                {activeSection === 'skills' && renderSkillsSection()}
                {/* Add other sections as needed */}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};