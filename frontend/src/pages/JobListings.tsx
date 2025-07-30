import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { mockJobs } from '../data/mockData';
import JobDetail from '../components/JobDetail';
import { 
  Search, 
  MapPin, 
  DollarSign, 
  Clock, 
  Star, 
  Filter,
  Bookmark,
  ExternalLink,
  Building,
  Users
} from 'lucide-react';


export const JobListings: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [savedJobs, setSavedJobs] = useState<number[]>([]);
  const [selectedJob, setSelectedJob] = useState<any | null>(null);
  const navigate = useNavigate();

  const toggleSaveJob = (jobId: number) => {
    setSavedJobs(prev => 
      prev.includes(jobId) 
        ? prev.filter(id => id !== jobId)
        : [...prev, jobId]
    );
  };

  const getMatchColor = (match: number) => {
    if (match >= 90) return 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20';
    if (match >= 75) return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20';
    return 'text-orange-600 bg-orange-50 dark:bg-orange-900/20';
  };

  return (
    <div className="max-w-6xl mx-auto px-3 sm:px-4 lg:px-6 xl:px-8 py-4 sm:py-6 lg:py-8">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2 sm:mb-4">
          Find Your Perfect Job
        </h1>
        <p className="text-base sm:text-lg text-gray-600 dark:text-gray-300">
          Discover AI-matched opportunities tailored to your skills and preferences
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 sm:mb-8 space-y-3 sm:space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search jobs, companies, or keywords..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              icon={<Search className="w-4 h-4" />}
            />
          </div>
          <div className="w-full md:w-64">
            <Input
              placeholder="Location"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              icon={<MapPin className="w-4 h-4" />}
            />
          </div>
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 w-full md:w-auto"
          >
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </Button>
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <Card>
            <CardContent className="p-4 sm:p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Job Type
                  </label>
                  <select className="w-full p-2 sm:p-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                    <option>All Types</option>
                    <option>Full-time</option>
                    <option>Part-time</option>
                    <option>Contract</option>
                    <option>Remote</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Experience Level
                  </label>
                  <select className="w-full p-2 sm:p-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                    <option>All Levels</option>
                    <option>Entry Level</option>
                    <option>Mid Level</option>
                    <option>Senior Level</option>
                    <option>Executive</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Salary Range
                  </label>
                  <select className="w-full p-2 sm:p-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                    <option>Any Salary</option>
                    <option>$50k - $75k</option>
                    <option>$75k - $100k</option>
                    <option>$100k - $150k</option>
                    <option>$150k+</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Results Summary */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6 space-y-2 sm:space-y-0">
        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
          Showing {mockJobs.length} jobs • Sorted by AI match
        </p>
        <select className="p-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-full sm:w-auto">
          <option>Best Match</option>
          <option>Most Recent</option>
          <option>Salary: High to Low</option>
          <option>Salary: Low to High</option>
        </select>
      </div>

      {/* Job Listings */}
      <div className="space-y-4 sm:space-y-6">
        {mockJobs.map((job) => (
          <Card key={job.id} hover className="transition-all duration-200">
            <CardContent className="p-4 sm:p-6">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between space-y-4 lg:space-y-0">
                <div className="flex space-x-3 sm:space-x-4 flex-1">
                  <img
                    src={job.logo}
                    alt={job.company}
                    className="w-12 sm:w-16 h-12 sm:h-16 rounded-lg object-cover flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-2 space-y-2 sm:space-y-0">
                      <h3 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 cursor-pointer">
                        {job.title}
                        {job.aiInterview && (
                          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 text-xs font-medium">
                            🤖 AI Interview
                          </span>
                        )}
                      </h3>
                      <div className={`px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium self-start ${getMatchColor(job.aiMatch)}`}>
                        <Star className="w-3 h-3 inline mr-1" />
                        {job.aiMatch}% match
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-3">
                      <div className="flex items-center space-x-1">
                        <Building className="w-4 h-4" />
                        <span className="font-medium text-gray-900 dark:text-white">{job.company}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <MapPin className="w-4 h-4" />
                        <span>{job.location}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <DollarSign className="w-4 h-4" />
                        <span>{job.salary}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="w-4 h-4" />
                        <span>{job.posted}</span>
                      </div>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex items-center px-2 sm:px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200">
                          {job.type}
                        </span>
                        <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                          Remote Friendly
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex flex-row lg:flex-col space-x-2 lg:space-x-0 lg:space-y-2 lg:ml-4">
                  <Button
                    onClick={() => toggleSaveJob(job.id)}
                    variant="ghost"
                    size="sm"
                    className="flex items-center space-x-2"
                  >
                    <Bookmark 
                      className={`w-4 h-4 ${savedJobs.includes(job.id) 
                        ? 'fill-current text-indigo-600' 
                        : 'text-gray-400'
                      }`} 
                    />
                  </Button>
                  <Button 
                    size="sm" 
                    className="whitespace-nowrap flex-1 lg:flex-none"
                    onClick={() => {
                      if (job.aiInterview) {
                        navigate('/ai-interview', { state: { job } });
                      } else {
                        // TODO: Open standard application form/modal
                        alert('Standard application form coming soon!');
                      }
                    }}
                  >
                    Apply Now
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="whitespace-nowrap flex-1 lg:flex-none"
                    onClick={() => setSelectedJob(job)}
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    <span className="hidden sm:inline">View Details</span>
                    <span className="sm:hidden">Details</span>
                  </Button>
                </div>
              </div>
              {/* AI Match Explanation */}
              <div className="mt-4 p-2 sm:p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium text-indigo-600 dark:text-indigo-400">Why this matches:</span>
                  {' '}Your React and TypeScript skills align perfectly with this role. 
                  The company culture matches your preferences for collaborative environments.
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {/* Job Detail Modal */}
      {selectedJob && (
        <JobDetail job={selectedJob} onClose={() => setSelectedJob(null)} />
      )}

      {/* Load More */}
      <div className="text-center mt-6 sm:mt-8">
        <Button variant="outline" size="lg">
          <Users className="w-4 h-4 mr-2" />
          Load More Jobs
        </Button>
      </div>
    </div>
  );
};