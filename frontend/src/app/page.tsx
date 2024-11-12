'use client';

import FileUpload from '@/components/fileUpload';
import Header from '@/components/header';

export default function Home() {
  const handleUploadComplete = () => {
    // This function can be empty now, as the redirection is handled in the FileUpload component
  };

  return (
    <div className="min-h-screen">
      <Header />
      <FileUpload onUploadComplete={handleUploadComplete} />
    </div>
  );
}
