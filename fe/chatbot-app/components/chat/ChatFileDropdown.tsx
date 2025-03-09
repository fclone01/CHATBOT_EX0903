// components/chat/ChatFileDropdown.tsx
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { File } from '@/types/chat';
import { FileIcon, ChevronDown, UploadIcon, Trash2 } from "lucide-react";

interface ChatFileDropdownProps {
  files: File[];
  onUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onDelete: (fileId: string) => void;
}

const ChatFileDropdown: React.FC<ChatFileDropdownProps> = ({
  files,
  onUpload,
  onDelete
}) => {
  const [showDropdown, setShowDropdown] = useState(false);

  return (
    <div className="relative">
      <Button 
        variant="outline" 
        size="sm" 
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center gap-1"
      >
        <FileIcon size={14} />
        Files ({files.length})
        <ChevronDown size={14} className={`transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
      </Button>
      
      {showDropdown && (
        <div className="absolute right-0 top-full mt-1 bg-white border rounded-md shadow-lg z-10 w-64">
          <div className="p-2">
            <label className="flex items-center gap-1 text-sm cursor-pointer hover:bg-gray-50 p-1 rounded">
              <UploadIcon size={14} className="text-blue-500" />
              Upload File
              <input 
                type="file" 
                onChange={onUpload} 
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
                      onDelete(file.id);
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
  );
};

export default ChatFileDropdown;