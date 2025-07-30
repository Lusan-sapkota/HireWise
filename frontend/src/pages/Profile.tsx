import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
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
  Share2,
  Loader2
} from 'lucide-react';

export const Profile: React.FC = () => {
  const { user, userProfile, updateUser, updateProfile, refreshUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [editedUser, setEditedUser] = useState(user);
  const [editedProfile, setEditedProfile] = useState(userProfile);
  const [newSkill, setNewSkill] = useState('');
  const [showAIResumeModal, setShowAIResumeModal] = useState(false);
  const [isGeneratingResume, setIsGeneratingResume] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [profileAnalytics, setProfileAnalytics] = useState({
    profileViews: 0,
    searchAppearances: 0,
    postEngagements: 0,
    profileStrength: 0
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [aiSuggestions, setAiSuggestions] = useState([]);

  // Load profile data and analytics
  useEffect(() => {
    if (user) {
      loadProfileData();
      
      // Set up periodic refresh for profile data (fallback for WebSocket)
      const profileInterval = setInterval(() => {
        loadProfileData();
      }, 120000); // Refresh every 2 minutes

      return () => {
        clearInterval(profileInterval);
      };
    }
  }, [user]);

  const loadProfileData = async () => {
    setIsLoading(true);
    try {
      // Load profile analytics
      const analyticsResponse = await apiService.getProfileAnalytics();
      setProfileAnalytics(analyticsResponse.data);

      // Load recent activity
      const activityResponse = await apiService.getProfileActivity();
      setRecentActivity(activityResponse.data.results || []);

      // Load AI suggestions
      const suggestionsResponse = await apiService.getProfileSuggestions();
      setAiSuggestions(suggestionsResponse.data.suggestions || []);
    } catch (error) {
      console.error('Failed to load profile data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Update local state when auth context changes
  useEffect(() => {
    if (user) {
      setEditedUser(user);
    }
  }, [user]);

  useEffect(() => {
    if (userProfile) {
      setEditedProfile(userProfile);
    }
  }, [userProfile]);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      // Update user basic info
      if (editedUser && user) {
        await updateUser({
          first_name: editedUser.first_name,
          last_name: editedUser.last_name,
          email: editedUser.email,
          phone_number: editedUser.phone_number
        });
      }

      // Update profile data
      if (editedProfile) {
        await updateProfile(editedProfile);
      }

      setIsEditing(false);
      await refreshUser();
    } catch (error) {
      console.error('Failed to save profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setEditedUser(user);
    setEditedProfile(userProfile);
    setIsEditing(false);
  };

  const addSkill = () => {
    if (newSkill.trim() && editedProfile && !editedProfile.skills?.includes(newSkill.trim())) {
      setEditedProfile({
        ...editedProfile,
        skills: [...(editedProfile.skills || []), newSkill.trim()]
      });
      setNewSkill('');
    }
  };

  const removeSkill = (skillToRemove: string) => {
    if (editedProfile) {
      setEditedProfile({
        ...editedProfile,
        skills: editedProfile.skills?.filter(skill => skill !== skillToRemove) || []
      });
    }
  };

  const generateAIResume = async () => {
    setIsGeneratingResume(true);
    try {
      const response = await apiService.generateAIResume({
        target_role: '', // Could be from form input
        style: 'modern'
      });
      
      // Handle the generated resume (download or display)
      if (response.data.download_url) {
        window.open(response.data.download_url, '_blank');
      }
      
      setShowAIResumeModal(false);
    } catch (error) {
      console.error('Failed to generate AI resume:', error);
    } finally {
      setIsGeneratingResume(false);
    }
  };

  const applyAISuggestion = async (suggestionId: string) => {
    try {
      await apiService.applyProfileSuggestion(suggestionId);
      // Refresh suggestions and profile data
      await loadProfileData();
      await refreshUser();
    } catch (error) {
      console.error('Failed to apply AI suggestion:', error);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

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
                    src={editedUser?.profile_picture || `https://ui-avatars.io/api/?name=${encodeURIComponent((editedUser?.first_name || '') + ' ' + (editedUser?.last_name || ''))}&background=6366f1&color=fff`}
                    alt={`${editedUser?.first_name} ${editedUser?.last_name}`}
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
                      <div className="grid grid-cols-2 gap-3">
                        <Input
                          value={editedUser?.first_name || ''}
                          onChange={(e) => setEditedUser({...editedUser, first_name: e.target.value})}
                          placeholder="First Name"
                        />
                        <Input
                          value={editedUser?.last_name || ''}
                          onChange={(e) => setEditedUser({...editedUser, last_name: e.target.value})}
                          placeholder="Last Name"
                        />
                      </div>
                      <Input
                        value={editedUser?.email || ''}
                        onChange={(e) => setEditedUser({...editedUser, email: e.target.value})}
                        placeholder="Email"
                        type="email"
                      />
                      <Input
                        value={editedUser?.phone_number || ''}
                        onChange={(e) => setEditedUser({...editedUser, phone_number: e.target.value})}
                        placeholder="Phone Number"
                      />
                    </div>
                  ) : (
                    <>
                      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        {editedUser?.first_name} {editedUser?.last_name}
                      </h1>
                      <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-400 mb-3 sm:mb-4">
                        {editedProfile?.bio || `${editedUser?.user_type === 'job_seeker' ? 'Job Seeker' : 'Recruiter'}`}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-500 dark:text-gray-400 mb-3 sm:mb-4">
                        {editedProfile?.location && (
                          <div className="flex items-center space-x-1">
                            <MapPin className="w-4 h-4" />
                            <span>{editedProfile.location}</span>
                          </div>
                        )}
                        <div className="flex items-center space-x-1">
                          <Mail className="w-4 h-4" />
                          <span>{editedUser?.email}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Users className="w-4 h-4" />
                          <span>{profileAnalytics.searchAppearances} profile views</span>
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
            {!isEditing && aiSuggestions.length > 0 && (
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
                      <div key={suggestion.id || index} className="p-3 sm:p-4 bg-violet-50 dark:bg-violet-900/20 rounded-lg border border-violet-200 dark:border-violet-800">
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
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="w-full sm:w-auto"
                            onClick={() => applyAISuggestion(suggestion.id)}
                          >
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
                    value={editedProfile?.bio || ''}
                    onChange={(e) => setEditedProfile({...editedProfile, bio: e.target.value})}
                    rows={4}
                    className="w-full p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Tell your professional story..."
                  />
                ) : (
                  <p className="text-sm sm:text-base text-gray-700 dark:text-gray-300 leading-relaxed">
                    {editedProfile?.bio || 'No bio added yet. Click edit to add your professional story.'}
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
                  {editedProfile?.work_experience && editedProfile.work_experience.length > 0 ? (
                    editedProfile.work_experience.map((exp, index) => (
                      <div key={index} className="flex space-x-3 sm:space-x-4">
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
                                  {exp.start_date} - {exp.end_date || 'Present'}
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
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600 dark:text-gray-400">No work experience added yet.</p>
                      {isEditing && (
                        <Button className="mt-4" size="sm">
                          <Plus className="w-4 h-4 mr-2" />
                          Add Experience
                        </Button>
                      )}
                    </div>
                  )}
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
                  {editedProfile?.skills && editedProfile.skills.length > 0 ? (
                    editedProfile.skills.map((skill, index) => (
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
                    ))
                  ) : (
                    <div className="text-center py-4 w-full">
                      <p className="text-gray-600 dark:text-gray-400 mb-4">No skills added yet.</p>
                      {isEditing && (
                        <div className="flex items-center space-x-2 justify-center">
                          <Input
                            placeholder="Add your first skill"
                            value={newSkill}
                            onChange={(e) => setNewSkill(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && addSkill()}
                            className="w-48"
                          />
                          <Button onClick={addSkill} size="sm">
                            <Plus className="w-4 h-4" />
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
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
                    <span className="text-base sm:text-lg font-semibold text-indigo-600">{profileAnalytics.profileViews}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Users className="w-4 h-4 text-gray-500" />
                      <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Search appearances</span>
                    </div>
                    <span className="text-base sm:text-lg font-semibold text-emerald-600">{profileAnalytics.searchAppearances}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <MessageSquare className="w-4 h-4 text-gray-500" />
                      <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Post engagements</span>
                    </div>
                    <span className="text-base sm:text-lg font-semibold text-violet-600">{profileAnalytics.postEngagements}</span>
                  </div>

                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-2">Profile Strength</div>
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className="bg-emerald-500 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${profileAnalytics.profileStrength}%` }}
                        ></div>
                      </div>
                      <span className="text-xs sm:text-sm font-medium text-emerald-600">{profileAnalytics.profileStrength}%</span>
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
                  {recentActivity.length > 0 ? (
                    recentActivity.map((activity, index) => (
                      <div key={index} className="flex items-center space-x-3 p-2 sm:p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className={`w-2 h-2 rounded-full ${
                          activity.type === 'interview' ? 'bg-emerald-500' :
                          activity.type === 'profile_update' ? 'bg-indigo-500' :
                          activity.type === 'application' ? 'bg-violet-500' :
                          'bg-gray-500'
                        }`}></div>
                        <div className="flex-1">
                          <span className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                            {activity.description}
                          </span>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {formatTimeAgo(activity.created_at)}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                        No recent activity
                      </p>
                    </div>
                  )}
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