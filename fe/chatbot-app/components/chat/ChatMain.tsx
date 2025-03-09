// components/chat/ChatMain.tsx
import React from 'react';
import { Separator } from "@/components/ui/separator";
import ChatFileDropdown from './ChatFileDropdown';
import ChatMessageList from './ChatMessageList';
import ChatMessageInput from './ChatMessageInput';
import { Chat, Message, File } from '@/types/chat';

interface ChatMainProps {
  selectedChat: Chat | null;
  messages: Message[];
  files: File[];
  onSendMessage: (message: string) => void;
  onUploadFile: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDeleteFile: (fileId: string) => void;
}

const ChatMain: React.FC<ChatMainProps> = ({
  selectedChat,
  messages,
  files,
  onSendMessage,
  onUploadFile,
  onDeleteFile
}) => {
  if (!selectedChat) {
    return (
      <div className="flex-1 flex justify-center items-center text-gray-500">
        Select a chat or create a new one to start
      </div>
    );
  }

  return (
    <>
      {/* Chat Header with Files Dropdown */}
      <div className="mb-2 flex justify-between items-center">
        <h3 className="font-bold">{selectedChat.name}</h3>
        <ChatFileDropdown 
          files={files}
          onUpload={onUploadFile}
          onDelete={onDeleteFile}
        />
      </div>

      <Separator className="mb-2" />

      {/* Messages */}
      <ChatMessageList messages={messages} />

      {/* Message Input */}
      <ChatMessageInput onSendMessage={onSendMessage} />
    </>
  );
};

export default ChatMain;