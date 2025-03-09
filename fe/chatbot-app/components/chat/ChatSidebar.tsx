// components/chat/ChatSidebar.tsx
import React, { useState } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Plus } from "lucide-react";
import { Chat } from '@/types/chat';

interface ChatSidebarProps {
  chats: Chat[];
  selectedChat: Chat | null;
  isLoading: boolean;
  onSelectChat: (chat: Chat) => void;
  onCreateChat: (name: string) => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  chats,
  selectedChat,
  isLoading,
  onSelectChat,
  onCreateChat
}) => {
  const [newChatName, setNewChatName] = useState("");

  const handleCreateChat = () => {
    if (newChatName.trim()) {
      onCreateChat(newChatName);
      setNewChatName("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCreateChat();
    }
  };

  return (
    <div className="w-1/4 md:w-[30%] border-r bg-gray-50 p-2 flex flex-col">
      {/* Create New Chat */}
      <div className="flex space-x-2 mb-3 p-2">
        <Input
          placeholder="New chat name"
          value={newChatName}
          onChange={(e) => setNewChatName(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <Button onClick={handleCreateChat} size="sm">
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
        <ScrollArea className="flex-1 overflow-y-auto">
          {chats.length > 0 ? (
            chats.map((chat) => (
              <Card
                key={chat.id}
                onClick={() => onSelectChat(chat)}
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
  );
};

export default ChatSidebar;