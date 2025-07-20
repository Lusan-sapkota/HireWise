import React, { useState } from 'react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { mockUser } from '../data/mockData';
import { 
  Edit3, 
  MapPin, 
  Mail, 
  Users, 
  Award, 
  Briefcase,
  Plus,
  X,
  Check,
  Bot,
  FileText,
  Download,
  Sparkles,
  Calendar,
  Building,
  GraduationCap,
  Star,
  Eye,
  MessageSquare,
  Share2
} from 'lucide-react';

export const Profile: React.FC = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedUser, setEditedUser] = useState(mockUser);
  const [newSkill, setNewSkill] = useState('');
  const [showAIResumeModal, setShowAIResumeModal] = useState(false);
  const [isGeneratingResume, setIsGeneratingResume] = useState(false);

  const handleSave = () => {
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedUser(mockUser);
    setIsEditing(false);
  };

  const addSkill = () => {
    if (newSkill.trim() && !editedUser.skills.includes(newSkill.trim())) {
      setEditedUser({
        ...editedUser,
        skills: [...editedUser.skills, newSkill.trim()]
      });
      setNewSkill('');
    }
  };

  const removeSkill = (skillToRemove: string) => {
    setEditedUser({
      ...editedUser,
      skills: editedUser.skills.filter(skill => skill !== skillToRemove)
    });
  };

  const generateAIResume = async () => {
    setIsGeneratingResume(true);
    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 3000));
    setIsGeneratingResume(false);
    setShowAIResumeModal(false);
    // Show success message or download
  };

  const aiSuggestions = [
    {
      type: 'skill',
      title: 'Add "Machine Learning" skill',
      description: 'Based on your React experience, ML skills are trending in your field',
      confidence: 92
    },
    {
      type: 'experience',
      title: 'Quantify your achievements',
      description: 'Add metrics like "Improved app performance by 40%" to your experience',
      confidence: 88
    },
    {
      type: 'summary',
      title: 'Enhance your summary',
      description: 'Include keywords like "scalable applications" and "cloud architecture"',
      confidence: 85
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-3 sm:px-4 lg:px-6 xl:px-8 py-4 sm:py-6">
        
        {/* Profile Header */}
        <Card className="mb-4 sm:mb-6">
          <div className="relative">
            {/* Cover Photo */}
            <div className="h-32 sm:h-40 lg:h-48 bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 rounded-t-lg relative">
              <div className="absolute inset-0 bg-black bg-opacity-20 rounded-t-lg"></div>
              {isEditing && (
                <button className="absolute top-4 right-4 p-2 bg-white bg-opacity-20 rounded-lg text-white hover:bg-opacity-30">
                  <Edit3 className="w-4 h-4" />
                </button>
              )}
            </div>
            
            {/* Profile Content */}
            <div className="px-4 sm:px-6 lg:px-8 pb-6 sm:pb-8">
              <div className="flex flex-col lg:flex-row lg:items-end lg:space-x-8">
                {/* Avatar */}
                <div className="relative -mt-12 sm:-mt-16 mb-4 lg:mb-0">
                  <img
                    src={editedUser.avatar}
                    alt={editedUser.name}
                    className="w-24 sm:w-32 h-24 sm:h-32 rounded-full border-4 border-white dark:border-gray-800 shadow-xl"
                  />
                  {isEditing && (
                    <button className="absolute bottom-2 right-2 p-2 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700">
                      <Edit3 className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* Profile Info */}
                <div className="flex-1">
                  {isEditing ? (
                    <div className="space-y-3 sm:space-y-4">
                      <Input
                        value={editedUser.name}
                        onChange={(e) => setEditedUser({...editedUser, name: e.target.value})}
                        className="text-xl sm:text-2xl font-bold"
                        placeholder="Full Name"
                      />
                      <Input
                        value={editedUser.title}
                        onChange={(e) => setEditedUser({...editedUser, title: e.target.value})}
                        placeholder="Professional Title"
                      />
                      <Input
                        value={editedUser.location}
                        onChange={(e) => setEditedUser({...editedUser, location: e.target.value})}
                        placeholder="Location"
                      />
                    </div>
                  ) : (
                    <>
                      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        {editedUser.name}
                      </h1>
                      <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-400 mb-3 sm:mb-4">
                        {editedUser.title}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-500 dark:text-gray-400 mb-3 sm:mb-4">
                        <div className="flex items-center space-x-1">
                          <MapPin className="w-4 h-4" />
                          <span>{editedUser.location}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Mail className="w-4 h-4" />
                          <span>{editedUser.email}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Users className="w-4 h-4" />
                          <span>{editedUser.connections} connections</span>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mt-4 lg:mt-0">
                  {isEditing ? (
                    <>
                      <Button onClick={handleSave} variant="primary" className="w-full sm:w-auto">
                        <Check className="w-4 h-4 mr-2" />
                        Save Changes
                      </Button>
                      <Button onClick={handleCancel} variant="outline" className="w-full sm:w-auto">
                        <X className="w-4 h-4 mr-2" />
                        Cancel
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button onClick={() => setShowAIResumeModal(true)} variant="secondary" className="w-full sm:w-auto">
                        <Bot className="w-4 h-4 mr-2" />
                        <span className="hidden sm:inline">AI Resume Builder</span>
                        <span className="sm:hidden">AI Resume</span>
                      </Button>
                      <Button onClick={() => setIsEditing(true)} variant="outline" className="w-full sm:w-auto">
                        <Edit3 className="w-4 h-4 mr-2" />
                        <span className="hidden sm:inline">Edit Profile</span>
                        <span className="sm:hidden">Edit</span>
                      </Button>
                      <Button variant="ghost" className="w-full sm:w-auto">
                        <Share2 className="w-4 h-4 mr-2" />
                        Share
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            
            {/* AI Suggestions */}
            {!isEditing && (
              <Card className="border-2 border-violet-200 dark:border-violet-800">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-5 h-5 text-violet-600" />
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">AI Profile Optimizer</h2>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 sm:space-y-4">
                    {aiSuggestions.map((suggestion, index) => (
                      <div key={index} className="p-3 sm:p-4 bg-violet-50 dark:bg-violet-900/20 rounded-lg border border-violet-200 dark:border-violet-800">
                        <div className="flex flex-col sm:flex-row items-start justify-between space-y-2 sm:space-y-0">
                          <div className="flex-1">
                            <h3 className="text-sm sm:text-base font-medium text-violet-900 dark:text-violet-100 mb-1">
                              {suggestion.title}
                            </h3>
                            <p className="text-xs sm:text-sm text-violet-700 dark:text-violet-300 mb-2">
                              {suggestion.description}
                            </p>
                            <div className="flex items-center space-x-2">
                              <div className="flex items-center space-x-1">
                                <Star className="w-3 h-3 text-emerald-500" />
                                <span className="text-xs text-emerald-600 font-medium">
                                  {suggestion.confidence}% confidence
                                </span>
                              </div>
                            </div>
                          </div>
                          <Button size="sm" variant="outline" className="w-full sm:w-auto">
                            Apply
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* About Section */}
            <Card>
              <CardHeader>
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">About</h2>
              </CardHeader>
              <CardContent>
                {isEditing ? (
                  <textarea
                    value={editedUser.bio}
                    onChange={(e) => setEditedUser({...editedUser, bio: e.target.value})}
                    rows={4}
                    className="w-full p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Tell your professional story..."
                  />
                ) : (
                  <p className="text-sm sm:text-base text-gray-700 dark:text-gray-300 leading-relaxed">
                    {editedUser.bio}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Experience Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">Experience</h2>
                  {isEditing && (
                    <Button size="sm" variant="outline">
                      <Plus className="w-4 h-4 mr-2" />
                      <span className="hidden sm:inline">Add Experience</span>
                      <span className="sm:hidden">Add</span>
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 sm:space-y-6">
                  {editedUser.experience.map((exp) => (
                    <div key={exp.id} className="flex space-x-3 sm:space-x-4">
                      <div className="flex-shrink-0">
                        <div className="w-10 sm:w-12 h-10 sm:h-12 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-lg flex items-center justify-center">
                          <Building className="w-6 h-6 text-white" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between space-y-2 sm:space-y-0">
                          <div>
                            <h3 className="font-semibold text-gray-900 dark:text-white text-base sm:text-lg">
                              {exp.position}
                            </h3>
                            <p className="text-sm sm:text-base text-indigo-600 dark:text-indigo-400 font-medium">
                              {exp.company}
                            </p>
                            <div className="flex items-center space-x-2 mt-1">
                              <Calendar className="w-4 h-4 text-gray-400" />
                              <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                                {exp.duration}
                              </span>
                            </div>
                          </div>
                          {isEditing && (
                            <Button size="sm" variant="ghost">
                              <Edit3 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                        <p className="text-sm sm:text-base text-gray-700 dark:text-gray-300 mt-3 leading-relaxed">
                          {exp.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Skills Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">Skills & Expertise</h2>
                  {isEditing && (
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
                      <Input
                        placeholder="Add new skill"
                        value={newSkill}
                        onChange={(e) => setNewSkill(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && addSkill()}
                        className="w-full sm:w-32"
                      />
                      <Button onClick={addSkill} size="sm">
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  {editedUser.skills.map((skill, index) => (
                    <div
                      key={index}
                      className="inline-flex items-center px-3 sm:px-4 py-1 sm:py-2 rounded-full text-xs sm:text-sm bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 border border-indigo-200 dark:border-indigo-800"
                    >
                      <Award className="w-3 h-3 mr-2" />
                      <span className="font-medium">{skill}</span>
                      {isEditing && (
                        <button
                          onClick={() => removeSkill(skill)}
                          className="ml-2 text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-200"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column */}
          <div className="space-y-4 sm:space-y-6">
            
            {/* Profile Analytics */}
            <Card>
              <CardHeader>
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Profile Analytics</h3>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 sm:space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Eye className="w-4 h-4 text-gray-500" />
                      <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Profile views</span>
                    </div>
                    <span className="text-base sm:text-lg font-semibold text-indigo-600">142</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Users className="w-4 h-4 text-gray-500" />
                      <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Search appearances</span>
                    </div>
                    <span className="text-base sm:text-lg font-semibold text-emerald-600">89</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <MessageSquare className="w-4 h-4 text-gray-500" />
                      <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Post engagements</span>
                    </div>
                    <span className="text-base sm:text-lg font-semibold text-violet-600">234</span>
                  </div>

                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-2">Profile Strength</div>
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div className="bg-emerald-500 h-2 rounded-full w-4/5"></div>
                      </div>
                      <span className="text-xs sm:text-sm font-medium text-emerald-600">85%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI Career Insights */}
            <Card className="border-2 border-violet-200 dark:border-violet-800">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <Bot className="w-5 h-5 text-violet-600" />
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">AI Career Insights</h3>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 sm:space-y-4">
                  <div className="p-2 sm:p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                    <h4 className="text-sm sm:text-base font-medium text-emerald-800 dark:text-emerald-200 mb-1">
                      🎯 Career Trajectory
                    </h4>
                    <p className="text-xs sm:text-sm text-emerald-700 dark:text-emerald-300">
                      You're on track for Senior roles. Focus on leadership skills.
                    </p>
                  </div>
                  
                  <div className="p-2 sm:p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                    <h4 className="text-sm sm:text-base font-medium text-indigo-800 dark:text-indigo-200 mb-1">
                      📈 Market Demand
                    </h4>
                    <p className="text-xs sm:text-sm text-indigo-700 dark:text-indigo-300">
                      React developers are in high demand. 95% match rate.
                    </p>
                  </div>
                  
                  <div className="p-2 sm:p-3 bg-violet-50 dark:bg-violet-900/20 rounded-lg">
                    <h4 className="text-sm sm:text-base font-medium text-violet-800 dark:text-violet-200 mb-1">
                      🚀 Next Steps
                    </h4>
                    <p className="text-xs sm:text-sm text-violet-700 dark:text-violet-300">
                      Consider adding cloud certifications to boost your profile.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Recent Activity</h3>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 sm:space-y-4">
                  <div className="flex items-center space-x-3 p-2 sm:p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                    <div className="flex-1">
                      <span className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                        Completed AI interview with 85% confidence
                      </span>
                      <p className="text-xs text-gray-500 dark:text-gray-400">2 days ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-2 sm:p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                    <div className="flex-1">
                      <span className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                        Updated skills section
                      </span>
                      <p className="text-xs text-gray-500 dark:text-gray-400">1 week ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-2 sm:p-3 bg-violet-50 dark:bg-violet-900/20 rounded-lg">
                    <div className="w-2 h-2 bg-violet-500 rounded-full"></div>
                    <div className="flex-1">
                      <span className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                        Applied to 3 positions
                      </span>
                      <p className="text-xs text-gray-500 dark:text-gray-400">2 weeks ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* AI Resume Builder Modal */}
      <Modal
        isOpen={showAIResumeModal}
        onClose={() => setShowAIResumeModal(false)}
        title="AI Resume Builder"
      >
        <div className="space-y-4 sm:space-y-6">
          <div className="text-center">
            <Bot className="w-16 h-16 text-violet-600 mx-auto mb-4" />
            <h3 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Create Your Perfect Resume
            </h3>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Our AI will analyze your profile and create a tailored resume optimized for your target roles.
            </p>
          </div>

          <div className="space-y-3 sm:space-y-4">
            <div className="p-3 sm:p-4 bg-violet-50 dark:bg-violet-900/20 rounded-lg border border-violet-200 dark:border-violet-800">
              <h4 className="text-sm sm:text-base font-medium text-violet-900 dark:text-violet-100 mb-2">
                ✨ AI will include:
              </h4>
              <ul className="text-xs sm:text-sm text-violet-700 dark:text-violet-300 space-y-1">
                <li>• Optimized summary based on your experience</li>
                <li>• ATS-friendly formatting and keywords</li>
                <li>• Industry-specific achievements and metrics</li>
                <li>• Skills prioritized by market demand</li>
                <li>• Professional formatting and design</li>
              </ul>
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Target Role (Optional)
              </label>
              <Input
                placeholder="e.g., Senior React Developer, Full Stack Engineer"
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Resume Style
              </label>
              <select className="w-full p-2 sm:p-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <option>Modern Professional</option>
                <option>Creative Design</option>
                <option>ATS Optimized</option>
                <option>Executive Style</option>
              </select>
            </div>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3 mt-4 sm:mt-6">
          <Button 
            variant="outline" 
            onClick={() => setShowAIResumeModal(false)}
            className="w-full sm:flex-1"
          >
            Cancel
          </Button>
          <Button 
            onClick={generateAIResume}
            isLoading={isGeneratingResume}
            className="w-full sm:flex-1"
          >
            {isGeneratingResume ? (
              <>
                <Bot className="w-4 h-4 mr-2 animate-pulse" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Resume
              </>
            )}
          </Button>
        </div>
      </Modal>
    </div>
  );
};