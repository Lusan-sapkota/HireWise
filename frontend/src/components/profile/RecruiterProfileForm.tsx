import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';

interface RecruiterFormData {
    company_name: string;
    company_website: string;
    company_size: string;
    industry: string;
    company_description: string;
    location: string;
}

interface RecruiterProfileFormProps {
    onSuccess: () => void;
    onError: (error: string) => void;
}

const RecruiterProfileForm: React.FC<RecruiterProfileFormProps> = ({ onSuccess, onError }) => {
    const { updateProfile } = useAuth();
    const [form, setForm] = useState<RecruiterFormData>({
        company_name: '',
        company_website: '',
        company_size: '',
        industry: '',
        company_description: '',
        location: '',
    });

    const [companyLogo, setCompanyLogo] = useState<File | null>(null);
    const [submitting, setSubmitting] = useState(false);

    // Handle simple field changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setForm(prev => ({ ...prev, [name]: value }));
    };

    // Handle file upload
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];

            // Validate file type
            if (!file.type.startsWith('image/')) {
                onError('Please select a valid image file');
                return;
            }

            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                onError('File size must be less than 5MB');
                return;
            }

            setCompanyLogo(file);
        }
    };

    // Form validation
    const validateForm = (): string | null => {
        if (!form.company_name.trim()) return 'Company name is required';
        if (!form.industry.trim()) return 'Industry is required';
        if (!form.company_description.trim()) return 'Company description is required';
        if (!form.location.trim()) return 'Location is required';

        // Validate website URL if provided
        if (form.company_website && !isValidUrl(form.company_website)) {
            return 'Please enter a valid website URL';
        }

        return null;
    };

    const isValidUrl = (url: string): boolean => {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
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
            // Prepare form data for multipart upload (if logo is included)
            let profileData: any = { ...form };

            if (companyLogo) {
                // Create FormData for file upload
                const formData = new FormData();
                Object.entries(form).forEach(([key, value]) => {
                    formData.append(key, value);
                });
                formData.append('company_logo', companyLogo);

                // Use FormData for the request
                profileData = formData;
            }

            // Create or update the recruiter profile
            let profileResponse;
            try {
                // Try to get existing profile first
                profileResponse = await apiService.getRecruiterProfile();
                // Update existing profile
                if (companyLogo) {
                    // For file uploads, we need to use the direct API call with FormData
                    profileResponse = await apiService.api.patch('/recruiter-profiles/me/', profileData, {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                        },
                    });
                } else {
                    profileResponse = await apiService.updateRecruiterProfile(profileData);
                }
            } catch (error: any) {
                if (error.response?.status === 404) {
                    // Profile doesn't exist, create new one
                    if (companyLogo) {
                        profileResponse = await apiService.api.post('/recruiter-profiles/', profileData, {
                            headers: {
                                'Content-Type': 'multipart/form-data',
                            },
                        });
                    } else {
                        profileResponse = await apiService.createRecruiterProfile(profileData);
                    }
                } else {
                    throw error;
                }
            }

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
            {/* Company Logo Upload */}
            <section>
                <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
                    Company Logo
                </h3>
                <div className="flex justify-center mb-6">
                    <div className="relative w-32 h-32">
                        {companyLogo ? (
                            <img
                                src={URL.createObjectURL(companyLogo)}
                                alt="Company Logo"
                                className="rounded-lg w-full h-full object-cover border-4 border-indigo-200 dark:border-indigo-400"
                            />
                        ) : (
                            <div className="bg-gray-200 dark:bg-gray-600 rounded-lg w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-300 text-sm border-4 border-gray-300 dark:border-gray-500">
                                Company Logo
                            </div>
                        )}
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileChange}
                            className="absolute top-0 left-0 opacity-0 w-full h-full cursor-pointer"
                            title="Upload company logo"
                        />
                        <div className="absolute bottom-0 right-0 bg-indigo-600 dark:bg-indigo-500 text-white rounded-full p-2 cursor-pointer hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                        </div>
                    </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                    Upload your company logo (max 5MB, image files only)
                </p>
            </section>

            {/* Company Information */}
            <section>
                <h3 className="text-xl font-semibold mb-4 text-indigo-600 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-600 pb-2">
                    Company Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="md:col-span-2">
                        <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Company Name *</label>
                        <input
                            name="company_name"
                            value={form.company_name}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                            placeholder="Your company name"
                            required
                        />
                    </div>

                    <div>
                        <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Company Website</label>
                        <input
                            name="company_website"
                            type="url"
                            value={form.company_website}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                            placeholder="https://yourcompany.com"
                        />
                    </div>

                    <div>
                        <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Company Size</label>
                        <select
                            name="company_size"
                            value={form.company_size}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                        >
                            <option value="">Select company size</option>
                            <option value="1-10">1-10 employees</option>
                            <option value="11-50">11-50 employees</option>
                            <option value="51-200">51-200 employees</option>
                            <option value="201-500">201-500 employees</option>
                            <option value="501-1000">501-1000 employees</option>
                            <option value="1001-5000">1001-5000 employees</option>
                            <option value="5000+">5000+ employees</option>
                        </select>
                    </div>

                    <div>
                        <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Industry *</label>
                        <select
                            name="industry"
                            value={form.industry}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                            required
                        >
                            <option value="">Select industry</option>
                            <option value="Technology">Technology</option>
                            <option value="Healthcare">Healthcare</option>
                            <option value="Finance">Finance</option>
                            <option value="Education">Education</option>
                            <option value="Manufacturing">Manufacturing</option>
                            <option value="Retail">Retail</option>
                            <option value="Consulting">Consulting</option>
                            <option value="Media & Entertainment">Media & Entertainment</option>
                            <option value="Real Estate">Real Estate</option>
                            <option value="Transportation">Transportation</option>
                            <option value="Energy">Energy</option>
                            <option value="Government">Government</option>
                            <option value="Non-profit">Non-profit</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>

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

                    <div className="md:col-span-2">
                        <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">Company Description *</label>
                        <textarea
                            name="company_description"
                            value={form.company_description}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
                            rows={4}
                            placeholder="Describe your company, its mission, values, and what makes it unique..."
                            required
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

export default RecruiterProfileForm;