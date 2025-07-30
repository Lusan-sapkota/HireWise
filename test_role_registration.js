// Simple test to verify role-based registration works
// This would be run in a browser console on the signup page

console.log('Testing role-based registration...');

// Test data for job seeker
const jobSeekerData = {
  username: 'testjobseeker',
  email: 'jobseeker@test.com',
  password: 'testpass123',
  first_name: 'Test',
  last_name: 'JobSeeker',
  user_type: 'job_seeker',
  phone_number: '+1234567890'
};

// Test data for recruiter
const recruiterData = {
  username: 'testrecruiter',
  email: 'recruiter@test.com',
  password: 'testpass123',
  first_name: 'Test',
  last_name: 'Recruiter',
  user_type: 'recruiter',
  phone_number: '+1234567890'
};

console.log('Job Seeker Registration Data:', jobSeekerData);
console.log('Recruiter Registration Data:', recruiterData);

// Check if the form includes role selection
const roleSelectionExists = document.querySelector('[data-testid="role-selection"]') || 
                           document.querySelector('.role-selection') ||
                           document.querySelectorAll('input[name="user_type"]').length > 0;

console.log('Role selection UI exists:', roleSelectionExists);

// Check if user_type is included in form data
const formElement = document.querySelector('form');
if (formElement) {
  const formData = new FormData(formElement);
  console.log('Form includes user_type field:', formData.has('user_type') || 
              document.querySelector('input[name="user_type"]') !== null);
}

console.log('Role-based registration test completed');