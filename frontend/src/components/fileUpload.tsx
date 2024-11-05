'use client';

import { useState, useRef } from 'react';
import { Upload, X, FileText } from 'lucide-react';
import { Button } from "@/components/ui/button";

interface FileUploadProps {
  onUploadComplete: () => void;
  isProcessing: boolean;
}

export default function FileUpload({ onUploadComplete, isProcessing }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.name.endsWith('.docx')
    );
    
    if (droppedFiles.length > 0) {
      setFiles(prev => [...prev, ...droppedFiles]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (fileToRemove: File) => {
    setFiles(files.filter(file => file !== fileToRemove));
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-primary">LogBotAI</h1>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="max-w-3xl w-full space-y-8">
          {/* Upload area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragging ? 'border-primary bg-primary/5' : 'border-gray-300'}
              ${isProcessing ? 'pointer-events-none opacity-50' : 'hover:border-primary'}`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx"
              onChange={handleFileSelect}
              className="hidden"
              multiple
            />
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              Dra och släpp dina .docx filer här eller
            </p>
            <Button 
              variant="outline" 
              className="mt-2" 
              disabled={isProcessing}
              onClick={handleButtonClick}
            >
              Välj filer
            </Button>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="space-y-4">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm"
                >
                  <div className="flex items-center space-x-3">
                    <FileText className="h-6 w-6 text-primary" />
                    <span className="text-sm font-medium">{file.name}</span>
                  </div>
                  <button
                    onClick={() => removeFile(file)}
                    className="text-gray-400 hover:text-gray-500"
                    disabled={isProcessing}
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ))}

              <Button
                className="w-full"
                onClick={onUploadComplete}
                disabled={isProcessing}
              >
                Ladda upp
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
} 