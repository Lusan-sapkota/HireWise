export const mockUser = {
  id: 1,
  name: 'Alex Johnson',
  title: 'Senior Software Engineer',
  avatar: 'https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
  email: 'alex.johnson@email.com',
  location: 'San Francisco, CA',
  connections: 342,
  bio: 'Passionate full-stack developer with 5+ years of experience in React, Node.js, and cloud technologies. Love building scalable applications and mentoring junior developers.',
  skills: ['React', 'TypeScript', 'Node.js', 'AWS', 'GraphQL', 'Docker'],
  experience: [
    {
      id: 1,
      company: 'TechCorp',
      position: 'Senior Software Engineer',
      duration: '2022 - Present',
      description: 'Leading frontend development for enterprise applications'
    },
    {
      id: 2,
      company: 'StartupXYZ',
      position: 'Full Stack Developer',
      duration: '2020 - 2022',
      description: 'Built scalable web applications from ground up'
    }
  ]
};

export const mockJobs = [
  {
    id: 1,
    title: 'Senior React Developer',
    company: 'InnovateTech',
    location: 'San Francisco, CA',
    salary: '$120k - $150k',
    type: 'Full-time',
    aiMatch: 95,
    posted: '2 days ago',
    logo: 'https://images.pexels.com/photos/3747463/pexels-photo-3747463.jpeg?auto=compress&cs=tinysrgb&w=60&h=60&fit=crop',
    description: 'Lead the development of cutting-edge React applications for enterprise clients. Collaborate with cross-functional teams to deliver scalable solutions.',
    requirements: [
      '5+ years experience with React and TypeScript',
      'Experience with Redux or similar state management',
      'Strong understanding of RESTful APIs',
      'Excellent communication skills'
    ],
    aiInterview: true
  },
  {
    id: 2,
    title: 'Frontend Engineer',
    company: 'DataCorp',
    location: 'Remote',
    salary: '$100k - $130k',
    type: 'Full-time',
    aiMatch: 87,
    posted: '1 week ago',
    logo: 'https://images.pexels.com/photos/3184339/pexels-photo-3184339.jpeg?auto=compress&cs=tinysrgb&w=60&h=60&fit=crop',
    description: 'Work on modern frontend projects using React, Tailwind CSS, and TypeScript. Build reusable UI components and optimize performance.',
    requirements: [
      '3+ years experience in frontend development',
      'Proficiency in React and CSS frameworks',
      'Familiarity with TypeScript',
      'Remote work experience is a plus'
    ],
    aiInterview: false
  },
  {
    id: 3,
    title: 'Full Stack Developer',
    company: 'CloudStartup',
    location: 'New York, NY',
    salary: '$90k - $120k',
    type: 'Full-time',
    aiMatch: 82,
    posted: '3 days ago',
    logo: 'https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=60&h=60&fit=crop',
    description: 'Join a fast-growing startup to build scalable web applications. Work across the stack with Node.js, React, and cloud services.',
    requirements: [
      '2+ years experience with Node.js and React',
      'Experience with cloud platforms (AWS, GCP, or Azure)',
      'Understanding of CI/CD pipelines',
      'Startup experience preferred'
    ],
    aiInterview: true
  }
];

export const mockPosts = [
  {
    id: 1,
    author: 'Sarah Chen',
    avatar: 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
    title: 'Product Manager',
    content: 'Just completed an amazing AI interview session on HireWise! The personalized feedback helped me identify areas for improvement. Highly recommend! 🚀',
    likes: 24,
    comments: 5,
    timeAgo: '2h ago'
  },
  {
    id: 2,
    author: 'Michael Rodriguez',
    avatar: 'https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
    title: 'UX Designer',
    content: 'Sharing my experience with the HireWise AI assistant. It helped me practice behavioral questions and gave real-time confidence metrics. Game changer for interview prep!',
    likes: 18,
    comments: 3,
    timeAgo: '4h ago'
  }
];

export const mockAIQuestions = [
  "Tell me about yourself and your background in software engineering.",
  "Describe a challenging project you worked on recently. How did you overcome obstacles?",
  "What interests you most about this role and our company?",
  "How do you stay updated with the latest technology trends?",
  "Describe a time when you had to work with a difficult team member."
];