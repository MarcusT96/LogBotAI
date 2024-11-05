'use client';

import { useState } from 'react';
import ChatInterface from '../components/chatInterface';
import FileUpload from '../components/fileUpload';

export default function Home() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const handleUploadComplete = () => {
    setIsProcessing(true);
    // Simulate processing time
    setTimeout(() => {
      setIsProcessing(false);
      setIsComplete(true);
    }, 3000);
  };

  return (
    <div className="h-screen w-screen">
      {!isComplete ? (
        <div className={`transition-opacity duration-500 ${isProcessing ? 'opacity-50' : 'opacity-100'}`}>
          <FileUpload onUploadComplete={handleUploadComplete} isProcessing={isProcessing} />
        </div>
      ) : (
        <div className="transition-opacity duration-500 opacity-100">
          <ChatInterface />
        </div>
      )}
      
      {isProcessing && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 transition-opacity duration-500">
          <div className="bg-white p-8 rounded-lg shadow-xl text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-lg">Bearbetar dina filer...</p>
          </div>
        </div>
      )}
    </div>
  );
}
