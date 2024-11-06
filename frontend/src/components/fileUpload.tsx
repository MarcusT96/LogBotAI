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

  const handleUpload = async () => {
    if (files.length > 0) {
      try {
        const formData = new FormData();
        files.forEach(file => {
          formData.append('files', file);
        });

        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        onUploadComplete();
      } catch (error) {
        console.error('Upload error:', error);
      }
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      <main className="flex-1 flex flex-col items-center p-4 overflow-y-auto">
        <div className="max-w-4xl w-full space-y-8 pt-8">
          {/* Hero Section */}
          <div className="text-center p-8">
            <div className="inline-block text-indigo-600 mb-2 px-6 py-2 rounded-full bg-indigo-50 text-sm font-medium shadow-sm">
              Mötesanteckningar på dina villkor
            </div>
            <h2 className="text-5xl font-bold mb-4 leading-tight">
              Personlig analys med en{' '}
              <span className="hero-gradient">AI assistent</span>
            </h2>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto mb-6">
              Lås upp potentialen i dina mötesanteckningar med vår innovativa AI. Vår plattform hjälper dig att 
              analysera innehållet i din takt, med fokus på det som är viktigt för dig.
            </p>
          </div>

          {/* Upload area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`card-gradient border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all shadow-lg
              ${isDragging ? 'border-indigo-500 bg-indigo-50/50' : 'border-indigo-200'}
              ${isProcessing ? 'pointer-events-none opacity-50' : 'hover:border-indigo-500 hover:shadow-xl'}`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx"
              onChange={handleFileSelect}
              className="hidden"
              multiple
            />
            <Upload className="mx-auto h-12 w-12 text-indigo-500" />
            <p className="mt-2 text-sm text-gray-600">
              Dra och släpp dina .docx filer här eller
            </p>
            <Button 
              variant="outline" 
              className="mt-2 border-indigo-200 hover:border-indigo-500 hover:bg-indigo-50" 
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
                  className="card-gradient flex items-center justify-between p-4 rounded-xl shadow-md transition-all hover:shadow-lg"
                >
                  <div className="flex items-center space-x-3">
                    <FileText className="h-6 w-6 text-indigo-500" />
                    <span className="text-sm font-medium text-gray-700">{file.name}</span>
                  </div>
                  <button
                    onClick={() => removeFile(file)}
                    className="text-gray-400 hover:text-indigo-500 transition-colors"
                    disabled={isProcessing}
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ))}

              <Button
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg transition-all"
                onClick={handleUpload}
                disabled={isProcessing || files.length === 0}
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