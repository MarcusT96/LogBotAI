'use client';

import ChatInterface from '@/components/chatInterface';
import Header from '@/components/header';

export default function ChatPage() {
  return (
    <div className="min-h-screen">
      <Header />
      <div className="pt-16">
        <ChatInterface />
      </div>
    </div>
  );
} 