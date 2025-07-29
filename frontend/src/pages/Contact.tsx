import React, { useState } from 'react';
import Footer from '../components/layout/Footer';

interface FormState {
  name: string;
  email: string;
  message: string;
  attachment: File | null;
  agree: boolean;
}

const Contact: React.FC = () => {
  const [form, setForm] = useState<FormState>({ name: '', email: '', message: '', attachment: null, agree: false });
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type, checked, files } = e.target as HTMLInputElement;
    if (type === 'checkbox') {
      setForm({ ...form, [name]: checked });
    } else if (type === 'file') {
      setForm({ ...form, attachment: files && files[0] ? files[0] : null });
    } else {
      setForm({ ...form, [name]: value });
    }
  };

  const validate = () => {
    const newErrors: { [key: string]: string } = {};
    if (!form.name.trim()) newErrors.name = 'Name is required.';
    if (!form.email.trim()) newErrors.email = 'Email is required.';
    else if (!/^\S+@\S+\.\S+$/.test(form.email)) newErrors.email = 'Enter a valid email.';
    if (!form.message.trim()) newErrors.message = 'Message is required.';
    if (!form.agree) newErrors.agree = 'You must agree to share your details.';
    return newErrors;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length === 0) {
      setSubmitted(true);
      // Here you would typically send the form data to your backend
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 flex flex-col items-center justify-center">
      <div className="max-w-2xl w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
        <h1 className="text-4xl font-bold text-indigo-700 dark:text-indigo-400 mb-6 text-center">Contact Us</h1>
        <p className="text-lg text-gray-700 dark:text-gray-300 mb-6 text-center">
          We'd love to hear from you! Fill out the form below and our team will get back to you as soon as possible.
        </p>
        {submitted ? (
          <div className="text-green-600 dark:text-green-400 text-center font-semibold py-8">
            Thank you for reaching out! We'll get back to you soon.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
              <input
                type="text"
                name="name"
                id="name"
                value={form.name}
                onChange={handleChange}
                className={`mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-14 text-base ${errors.name ? 'border-red-500' : ''}`}
              />
              {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
              <input
                type="email"
                name="email"
                id="email"
                value={form.email}
                onChange={handleChange}
                className={`mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-14 text-base ${errors.email ? 'border-red-500' : ''}`}
              />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
            </div>
            <div>
              <label htmlFor="message" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Message</label>
              <textarea
                name="message"
                id="message"
                rows={5}
                value={form.message}
                onChange={handleChange}
                className={`mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-28 text-base ${errors.message ? 'border-red-500' : ''}`}
              />
              {errors.message && <p className="text-red-500 text-xs mt-1">{errors.message}</p>}
            </div>
            <div>
              <label htmlFor="attachment" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Attachment (optional)</label>
              <input
                type="file"
                name="attachment"
                id="attachment"
                accept="image/*,application/pdf,.doc,.docx,.txt"
                onChange={handleChange}
                className="mt-1 block w-full text-gray-700 dark:text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
              {form.attachment && <p className="text-xs text-gray-500 mt-1">Selected: {form.attachment.name}</p>}
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                name="agree"
                id="agree"
                checked={form.agree}
                onChange={handleChange}
                className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="agree" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                I agree to sharing my details with HireWise.
              </label>
            </div>
            {errors.agree && <p className="text-red-500 text-xs mt-1">{errors.agree}</p>}
            <button
              type="submit"
              className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md shadow focus:outline-none focus:ring-2 focus:ring-indigo-500 text-lg"
            >
              Send Message
            </button>
          </form>
        )}
      </div>
      <div className="w-full mt-8">
        <Footer />
      </div>
    </div>
  );
};

export default Contact;
