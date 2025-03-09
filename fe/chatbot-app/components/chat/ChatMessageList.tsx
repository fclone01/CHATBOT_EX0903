// components/chat/ChatMessageList.tsx
import React from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Message } from '@/types/chat';

interface ChatMessageListProps {
  messages: Message[];
}

const ChatMessageList: React.FC<ChatMessageListProps> = ({ messages }) => {
  // Format message timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <ScrollArea className="flex-1 rounded bg-gray-50 mb-2 p-2 overflow-scroll">
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
  );
};

export default ChatMessageList;