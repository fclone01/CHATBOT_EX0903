// types/chat.ts
export type Chat = {
    id: string;
    name: string;
    created_at: string;
  };
  
  export type Message = {
    id: string;
    chat_id: string;
    content: string;
    role: 'user' | 'ai';
    created_at: string;
  };
  
  export type File = {
    id: string;
    chat_id: string;
    file_name: string;
    created_at: string;
  };