// services/chatService.ts
import { useCallback } from 'react';
import axios from 'axios';
import { Chat, Message, File } from '@/types/chat';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

type ChatServiceProps = {
  setChats: React.Dispatch<React.SetStateAction<Chat[]>>;
  setSelectedChat: React.Dispatch<React.SetStateAction<Chat | null>>;
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  setFiles: React.Dispatch<React.SetStateAction<File[]>>;
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>;
};

export const useChatService = ({
  setChats,
  setSelectedChat,
  setMessages,
  setFiles,
  setIsLoading
}: ChatServiceProps) => {
  const router = useRouter();

  const fetchChats = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await axios.get(`${API_URL}/api/chats`);
      setChats(res.data);
      if (res.data.length > 0) {
        // Don't automatically select a chat - let URL param decide
      }
    } catch (error) {
      console.error("Failed to fetch chats:", error);
    } finally {
      setIsLoading(false);
    }
  }, [setChats, setIsLoading]);

  const selectChat = useCallback(async (chat: Chat) => {
    try {
      setSelectedChat(chat);
      const res = await axios.get(`${API_URL}/api/chats/${chat.id}`);
      setMessages(res.data.messages);
      setFiles(res.data.files);
      
      // Update URL with chat ID
      router.push(`/chat/${chat.id}`);
    } catch (error) {
      console.error(`Failed to fetch chat ${chat.id}:`, error);
    }
  }, [setSelectedChat, setMessages, setFiles, router]);

  const fetchChatById = useCallback(async (chatId: string) => {
    try {
      setIsLoading(true);
      const chatRes = await axios.get(`${API_URL}/api/chats`);
      const chats = chatRes.data;
      setChats(chats);

      const chat = chats.find((c: Chat) => c.id === chatId);
      if (chat) {
        const res = await axios.get(`${API_URL}/api/chats/${chatId}`);
        setSelectedChat(chat);
        setMessages(res.data.messages);
        setFiles(res.data.files);
      }
    } catch (error) {
      console.error(`Failed to fetch chat ${chatId}:`, error);
    } finally {
      setIsLoading(false);
    }
  }, [setChats, setSelectedChat, setMessages, setFiles, setIsLoading]);

  const createChat = useCallback(async (newChatName: string) => {
    if (!newChatName.trim()) return;
    
    try {
      const res = await axios.post(`${API_URL}/api/chats`, { name: newChatName });
      fetchChats();
      
      // Select the newly created chat
      if (res.data && res.data.id) {
        selectChat(res.data);
      }
    } catch (error) {
      console.error("Failed to create chat:", error);
    }
  }, [fetchChats, selectChat]);

  const uploadFile = useCallback(async (file: File, chatId: string) => {
    if (!file || !chatId) return;

    try {
      const formData = new FormData();
      formData.append("file", file as unknown as Blob);
      formData.append("chat_id", chatId);

      await axios.post(`${API_URL}/api/upload`, formData);
      
      // Refresh the chat to show the new file
    //   const chat = { id: chatId } as Chat;
      const res = await axios.get(`${API_URL}/api/chats/${chatId}`);
      setFiles(res.data.files);
    } catch (error) {
      console.error("Failed to upload file:", error);
    }
  }, [setFiles]);

  const deleteFile = useCallback(async (fileId: string, chatId: string) => {
    try {
      await axios.delete(`${API_URL}/api/files/${fileId}`);
      
      // Refresh files list
      const res = await axios.get(`${API_URL}/api/chats/${chatId}`);
      setFiles(res.data.files);
    } catch (error) {
      console.error(`Failed to delete file ${fileId}:`, error);
    }
  }, [setFiles]);

  const sendMessage = useCallback(async (content: string, chatId: string) => {
    if (!content.trim() || !chatId) return;

    try {
      await axios.post(`${API_URL}/api/messages`, {
        content: content,
        chat_id: chatId,
      });

      // Refresh messages
      const res = await axios.get(`${API_URL}/api/chats/${chatId}`);
      setMessages(res.data.messages);
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  }, [setMessages]);

  return {
    fetchChats,
    selectChat,
    fetchChatById,
    createChat,
    uploadFile,
    deleteFile,
    sendMessage
  };
};