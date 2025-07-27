import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { apiService } from '../services/api';
import { 
  Send, 
  Search, 
  MoreVertical, 
  Phone, 
  Video, 
  Paperclip, 
  Smile, 
  Check, 
  CheckCheck,
  Circle,
  User,
  Bot,
  Briefcase,
  Calendar,
  FileText
} from 'lucide-react';

interface Message {
  id: string;
  sender: string;
  content: string;
  timestamp: string;
  is_read: boolean;
  message_type: 'text' | 'file' | 'system';
  file_url?: string;
  file_name?: string;
}

interface Conversation {
  id: string;
  participant: {
    id: string;
    name: string;
    avatar: string;
    title: string;
    is_online: boolean;
    last_seen?: string;
  };
  last_message: Message;
  unread_count: number;
  conversation_type: 'direct' | 'interview' | 'support';
}

export const Messages: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mock data - replace with actual API calls
  const mockConversations: Conversation[] = [
    {
      id: '1',
      participant: {
        id: '1',
        name: 'Sarah Chen',
        avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150',
        title: 'Senior Recruiter at TechCorp',
        is_online: true,
      },
      last_message: {
        id: '1',
        sender: '1',
        content: 'Thanks for your application! I\'d like to schedule an interview.',
        timestamp: '2024-01-15T10:30:00Z',
        is_read: false,
        message_type: 'text',
      },
      unread_count: 2,
      conversation_type: 'direct',
    },
    {
      id: '2',
      participant: {
        id: '2',
        name: 'AI Interview Assistant',
        avatar: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=150',
        title: 'AI Assistant',
        is_online: true,
      },
      last_message: {
        id: '2',
        sender: '2',
        content: 'Your interview session is ready. Click here to start.',
        timestamp: '2024-01-15T09:15:00Z',
        is_read: true,
        message_type: 'text',
      },
      unread_count: 0,
      conversation_type: 'interview',
    },
    {
      id: '3',
      participant: {
        id: '3',
        name: 'Mike Rodriguez',
        avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
        title: 'Hiring Manager at StartupXYZ',
        is_online: false,
        last_seen: '2024-01-15T08:45:00Z',
      },
      last_message: {
        id: '3',
        sender: 'me',
        content: 'Thank you for the opportunity. I look forward to hearing from you.',
        timestamp: '2024-01-14T16:20:00Z',
        is_read: true,
        message_type: 'text',
      },
      unread_count: 0,
      conversation_type: 'direct',
    },
  ];

  const mockMessages: Message[] = [
    {
      id: '1',
      sender: '1',
      content: 'Hi! I reviewed your application for the Senior Frontend Developer position.',
      timestamp: '2024-01-15T10:00:00Z',
      is_read: true,
      message_type: 'text',
    },
    {
      id: '2',
      sender: 'me',
      content: 'Thank you for reaching out! I\'m very interested in the position.',
      timestamp: '2024-01-15T10:05:00Z',
      is_read: true,
      message_type: 'text',
    },
    {
      id: '3',
      sender: '1',
      content: 'Great! Your experience with React and TypeScript looks impressive. I\'d like to schedule a technical interview.',
      timestamp: '2024-01-15T10:10:00Z',
      is_read: true,
      message_type: 'text',
    },
    {
      id: '4',
      sender: 'me',
      content: 'That sounds perfect. I\'m available this week for an interview.',
      timestamp: '2024-01-15T10:15:00Z',
      is_read: true,
      message_type: 'text',
    },
    {
      id: '5',
      sender: '1',
      content: 'Thanks for your application! I\'d like to schedule an interview.',
      timestamp: '2024-01-15T10:30:00Z',
      is_read: false,
      message_type: 'text',
    },
  ];

  useEffect(() => {
    // Load conversations
    setConversations(mockConversations);
    setActiveConversation(mockConversations[0]);
    setMessages(mockMessages);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || isSending) return;

    setIsSending(true);
    const messageContent = newMessage.trim();
    setNewMessage('');

    // Add message optimistically
    const tempMessage: Message = {
      id: Date.now().toString(),
      sender: 'me',
      content: messageContent,
      timestamp: new Date().toISOString(),
      is_read: false,
      message_type: 'text',
    };

    setMessages(prev => [...prev, tempMessage]);

    try {
      // TODO: Send message via API
      // await apiService.sendMessage(activeConversation?.id, messageContent);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update message status
      setMessages(prev => 
        prev.map(msg => 
          msg.id === tempMessage.id 
            ? { ...msg, is_read: true }
            : msg
        )
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove failed message
      setMessages(prev => prev.filter(msg => msg.id !== tempMessage.id));
    } finally {
      setIsSending(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      // TODO: Upload file and send message
      // const response = await apiService.uploadFile(file, 'message_attachment');
      console.log('File upload:', file.name);
    } catch (error) {
      console.error('File upload failed:', error);
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getConversationIcon = (type: string) => {
    switch (type) {
      case 'interview':
        return <Bot className="w-4 h-4 text-violet-600" />;
      case 'support':
        return <FileText className="w-4 h-4 text-blue-600" />;
      default:
        return <Briefcase className="w-4 h-4 text-gray-600" />;
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.participant.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading messages...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-8rem)]">
          
          {/* Conversations List */}
          <div className="lg:col-span-4 xl:col-span-3">
            <Card className="h-full flex flex-col">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Messages</h2>
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-0">
                <div className="space-y-1">
                  {filteredConversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                        activeConversation?.id === conversation.id
                          ? 'bg-indigo-50 dark:bg-indigo-900/20 border-r-2 border-indigo-500'
                          : ''
                      }`}
                      onClick={() => setActiveConversation(conversation)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="relative">
                          <img
                            src={conversation.participant.avatar}
                            alt={conversation.participant.name}
                            className="w-12 h-12 rounded-full"
                          />
                          {conversation.participant.is_online && (
                            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full"></div>
                          )}
                          <div className="absolute -top-1 -left-1">
                            {getConversationIcon(conversation.conversation_type)}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {conversation.participant.name}
                            </h3>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {formatTime(conversation.last_message.timestamp)}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-400 truncate mb-1">
                            {conversation.participant.title}
                          </p>
                          <div className="flex items-center justify-between">
                            <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                              {conversation.last_message.sender === 'me' && (
                                <span className="mr-1">
                                  {conversation.last_message.is_read ? (
                                    <CheckCheck className="w-3 h-3 inline text-blue-500" />
                                  ) : (
                                    <Check className="w-3 h-3 inline text-gray-400" />
                                  )}
                                </span>
                              )}
                              {conversation.last_message.content}
                            </p>
                            {conversation.unread_count > 0 && (
                              <div className="w-5 h-5 bg-indigo-600 text-white text-xs rounded-full flex items-center justify-center">
                                {conversation.unread_count}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-8 xl:col-span-9">
            {activeConversation ? (
              <Card className="h-full flex flex-col">
                {/* Chat Header */}
                <CardHeader className="border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="relative">
                        <img
                          src={activeConversation.participant.avatar}
                          alt={activeConversation.participant.name}
                          className="w-10 h-10 rounded-full"
                        />
                        {activeConversation.participant.is_online && (
                          <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full"></div>
                        )}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {activeConversation.participant.name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {activeConversation.participant.is_online ? (
                            'Online'
                          ) : (
                            `Last seen ${formatTime(activeConversation.participant.last_seen || '')}`
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm">
                        <Phone className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Video className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                {/* Messages */}
                <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.sender === 'me' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.sender === 'me'
                            ? 'bg-indigo-600 text-white'
                            : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <div className="flex items-center justify-between mt-1">
                          <span className={`text-xs ${
                            message.sender === 'me' ? 'text-indigo-200' : 'text-gray-500 dark:text-gray-400'
                          }`}>
                            {formatTime(message.timestamp)}
                          </span>
                          {message.sender === 'me' && (
                            <span className="ml-2">
                              {message.is_read ? (
                                <CheckCheck className="w-3 h-3 text-indigo-200" />
                              ) : (
                                <Check className="w-3 h-3 text-indigo-300" />
                              )}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </CardContent>

                {/* Message Input */}
                <div className="border-t border-gray-200 dark:border-gray-700 p-4">
                  <div className="flex items-center space-x-2">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                      className="hidden"
                      accept="image/*,.pdf,.doc,.docx"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Paperclip className="w-4 h-4" />
                    </Button>
                    <div className="flex-1 relative">
                      <Input
                        placeholder="Type a message..."
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        className="pr-10"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 transform -translate-y-1/2"
                      >
                        <Smile className="w-4 h-4" />
                      </Button>
                    </div>
                    <Button
                      onClick={handleSendMessage}
                      disabled={!newMessage.trim() || isSending}
                      size="sm"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ) : (
              <Card className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Send className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Select a conversation
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Choose a conversation from the list to start messaging
                  </p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};