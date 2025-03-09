// app/chat/page.tsx
"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { UploadIcon, Trash2, FileIcon, ChevronDown, Plus } from "lucide-react";
import axios from "axios";

// Types based on the provided API response
type Chat = {
  id: string;
  name: string;
  created_at: string;
};

type Message = {
  id: string;
  chat_id: string;
  content: string;
  role: 'user' | 'ai';
  created_at: string;
};

type File = {
  id: string;
  chat_id: string;
  file_name: string;
  created_at: string;
};

export default function ChatPage() {
  // State management
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [newChatName, setNewChatName] = useState("");
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [showFileDropdown, setShowFileDropdown] = useState(false);

  // Environment variable access
  const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      setIsLoading(true);
      const res = await axios.get(`${API_URL}/api/chats`);
      setChats(res.data);
      if (res.data.length > 0) {
        selectChat(res.data[res.data.length - 1]);
      }
    } catch (error) {
      console.error("Failed to fetch chats:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const selectChat = async (chat: Chat) => {
    try {
      setSelectedChat(chat);
      const res = await axios.get(`${API_URL}/api/chats/${chat.id}`);
      setMessages(res.data.messages);
      setFiles(res.data.files);
      // Close file dropdown when changing chat
      setShowFileDropdown(false);
    } catch (error) {
      console.error(`Failed to fetch chat ${chat.id}:`, error);
    }
  };

  const createChat = async () => {
    if (!newChatName.trim()) return;
    
    try {
      await axios.post(`${API_URL}/api/chats`, { name: newChatName });
      setNewChatName("");
      fetchChats();
    } catch (error) {
      console.error("Failed to create chat:", error);
    }
  };

  const uploadFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedChat) return;

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("chat_id", selectedChat.id);

      await axios.post(`${API_URL}/api/upload`, formData);
      selectChat(selectedChat);
    } catch (error) {
      console.error("Failed to upload file:", error);
    } finally {
      // Reset the file input
      event.target.value = '';
    }
  };

  const deleteFile = async (fileId: string) => {
    try {
      await axios.delete(`${API_URL}/api/files/${fileId}`);
      selectChat(selectedChat!);
    } catch (error) {
      console.error(`Failed to delete file ${fileId}:`, error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedChat) return;

    try {
      await axios.post(`${API_URL}/api/chats/${selectedChat.id}/messages`, {
        content: newMessage,
      });

      setNewMessage("");
      selectChat(selectedChat);
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Format message timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-1/4 md:w-[30%] border-r bg-gray-50 p-2 flex flex-col">
        {/* Create New Chat (Moved to top) */}
        <div className="flex space-x-2 mb-3 p-2">
          <Input
            placeholder="New chat name"
            value={newChatName}
            onChange={(e) => setNewChatName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && createChat()}
          />
          <Button onClick={createChat} size="sm">
            <Plus size={16} />
          </Button>
        </div>
        
        <Separator className="mb-2" />
        
        <h2 className="font-bold text-lg px-2 mb-2">Conversations</h2>

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-gray-500">Loading chats...</p>
          </div>
        ) : (
          <ScrollArea className="flex-1">
            {chats.length > 0 ? (
              chats.map((chat) => (
                <Card
                  key={chat.id}
                  onClick={() => selectChat(chat)}
                  className={`mb-1 cursor-pointer transition-colors ${
                    selectedChat?.id === chat.id ? "bg-primary text-white" : ""
                  }`}
                >
                  <CardContent className="p-2 text-sm">{chat.name}</CardContent>
                </Card>
              ))
            ) : (
              <p className="text-gray-500 text-center p-2 text-sm">No conversations yet</p>
            )}
          </ScrollArea>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="w-3/4 md:w-[70%] flex flex-col p-2">
        {selectedChat ? (
          <>
            {/* Chat Header with Files Dropdown */}
            <div className="mb-2 flex justify-between items-center">
              <h3 className="font-bold">{selectedChat.name}</h3>
              
              <div className="relative">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setShowFileDropdown(!showFileDropdown)}
                  className="flex items-center gap-1"
                >
                  <FileIcon size={14} />
                  Files ({files.length})
                  <ChevronDown size={14} className={`transition-transform ${showFileDropdown ? 'rotate-180' : ''}`} />
                </Button>
                
                {showFileDropdown && (
                  <div className="absolute right-0 top-full mt-1 bg-white border rounded-md shadow-lg z-10 w-64">
                    <div className="p-2">
                      <label className="flex items-center gap-1 text-sm cursor-pointer hover:bg-gray-50 p-1 rounded">
                        <UploadIcon size={14} className="text-blue-500" />
                        Upload File
                        <input 
                          type="file" 
                          onChange={uploadFile} 
                          className="hidden" 
                          accept="application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel"
                        />
                      </label>
                    </div>
                    
                    <Separator />
                    
                    <div className="max-h-48 overflow-y-auto p-1">
                      {files.length > 0 ? (
                        files.map((file) => (
                          <div key={file.id} className="flex items-center justify-between p-1 hover:bg-gray-50 rounded">
                            <div className="flex items-center gap-1 text-sm truncate">
                              <FileIcon size={14} className="text-blue-500 flex-shrink-0" />
                              <span className="truncate">{file.file_name}</span>
                            </div>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteFile(file.id);
                              }}
                              className="h-6 w-6"
                              aria-label="Delete file"
                            >
                              <Trash2 size={14} />
                            </Button>
                          </div>
                        ))
                      ) : (
                        <div className="text-gray-500 text-sm text-center p-2">
                          No files uploaded
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <Separator className="mb-2" />

            {/* Messages */}
            <ScrollArea className="flex-1 rounded bg-gray-50 mb-2 p-2">
              {messages.length > 0 ? (
                messages.map((msg) => (
                  <div 
                    key={msg.id} 
                    className={`mb-2 p-2 rounded-lg ${
                      msg.role === 'user' ? 'bg-blue-50 ml-8' : 'bg-white mr-8 border border-gray-100'
                    }`}
                  >
                    <div className="flex justify-between mb-1">
                      <div className="font-medium text-sm">
                        {msg.role === 'user' ? 'You' : 'Assistant'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatTime(msg.created_at)}
                      </div>
                    </div>
                    <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                  </div>
                ))
              ) : (
                <div className="text-gray-500 text-center p-2 text-sm">
                  No messages yet. Start the conversation!
                </div>
              )}
            </ScrollArea>

            {/* Message Input */}
            <div className="flex space-x-2">
              <Input
                placeholder="Type your message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                className="flex-1"
              />
              <Button onClick={sendMessage} disabled={!newMessage.trim()} size="sm">Send</Button>
            </div>
          </>
        ) : (
          <div className="flex-1 flex justify-center items-center text-gray-500">
            Select a chat or create a new one to start
          </div>
        )}
      </div>
    </div>
  );
}