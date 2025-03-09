// app/chat/new/page.tsx
"use client";

import { useEffect, useState } from "react";
import { Chat, Message, File } from "@/types/chat";
import { useChatService } from "@/services/chatService";
import ChatSidebar from "@/components/chat/ChatSidebar";
import ChatMain from "@/components/chat/ChatMain";

export default function NewChatPage() {
  // State management
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const { 
    fetchChats, 
    selectChat, 
    createChat, 
    uploadFile, 
    deleteFile, 
    sendMessage 
  } = useChatService({
    setChats,
    setSelectedChat,
    setMessages,
    setFiles,
    setIsLoading
  });

  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  const handleUploadFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedChat || !e.target.files || e.target.files.length === 0) return;
    uploadFile(e.target.files[0] as unknown as File, selectedChat.id);
  };

  const handleDeleteFile = (fileId: string) => {
    if (!selectedChat) return;
    deleteFile(fileId, selectedChat.id);
  };

  const handleSendMessage = (content: string) => {
    if (!selectedChat) return;
    sendMessage(content, selectedChat.id);
  };

  return (
    <>
      <ChatSidebar 
        chats={chats}
        selectedChat={selectedChat}
        isLoading={isLoading}
        onSelectChat={selectChat}
        onCreateChat={createChat}
      />
      <div className="w-3/4 md:w-[70%] flex flex-col p-2">
        <ChatMain 
          selectedChat={selectedChat}
          messages={messages}
          files={files}
          onSendMessage={handleSendMessage}
          onUploadFile={handleUploadFile}
          onDeleteFile={handleDeleteFile}
        />
      </div>
    </>
  );
}