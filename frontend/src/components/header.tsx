import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { Button } from "@/components/ui/button";

interface HeaderProps {
  showBackButton?: boolean;
}

export default function Header({ showBackButton = false }: HeaderProps) {
  return (
    <header className="bg-white/80 backdrop-blur-sm shadow-sm fixed top-0 w-full z-50 h-16">
      <div className="h-full px-6 flex items-center justify-between">
        {showBackButton ? (
          <Link href="/">
            <Button
              variant="ghost"
              className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
        ) : (
          <div className="w-10"></div>
        )}
        
        <Link href="/" className="absolute left-1/2 -translate-x-1/2">
          <h1 className="text-2xl font-bold text-indigo-600">
            LogBotAI
          </h1>
        </Link>
        
        <div className="w-10"></div>
      </div>
    </header>
  );
} 