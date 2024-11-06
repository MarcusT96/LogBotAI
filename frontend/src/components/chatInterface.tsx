'use client'

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send } from "lucide-react"
import ReactMarkdown, { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
}

interface MarkdownProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export default function Component() {
  const [inputValue, setInputValue] = useState("")
  const [messages, setMessages] = useState<Message[]>([
    { 
      id: 1, 
      text: "Hur kan jag hjälpa dig med dina mötesanteckningar idag?", 
      sender: 'ai' 
    }
  ])
  const [isLoading, setIsLoading] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const markdownComponents: Partial<Components> = {
    code: ({ node, inline, className, children, ...props }: MarkdownProps) => {
      return (
        <code
          className={`${inline ? 'bg-gray-100 rounded px-1' : 'block bg-gray-100 p-2 rounded-lg'} ${className || ''}`}
          {...props}
        >
          {children}
        </code>
      )
    },
    a: ({ node, className, children, ...props }: MarkdownProps) => {
      return (
        <a
          className="text-blue-500 hover:underline"
          target="_blank"
          rel="noopener noreferrer"
          {...props}
        >
          {children}
        </a>
      )
    },
    ul: ({ node, className, children, ...props }: MarkdownProps) => {
      return (
        <ul className="list-disc pl-4 space-y-1" {...props}>
          {children}
        </ul>
      )
    },
    ol: ({ node, className, children, ...props }: MarkdownProps) => {
      return (
        <ol className="list-decimal pl-4 space-y-1" {...props}>
          {children}
        </ol>
      )
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return

    // Add user message immediately
    const userMessage: Message = {
      id: Date.now(),
      text: inputValue,
      sender: 'user'
    }
    setMessages(prev => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: inputValue }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()
      setMessages(prev => [...prev, data])
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: "Ett fel uppstod. Försök igen senare.",
        sender: 'ai'
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-3xl">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.sender === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-gray-800'
                  }`}
                >
                  {message.sender === 'ai' ? (
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      className="prose prose-slate max-w-none
                        prose-headings:text-gray-800 
                        prose-p:text-gray-800 
                        prose-strong:text-gray-800
                        prose-ul:text-gray-800
                        prose-ol:text-gray-800
                        prose-pre:bg-gray-50
                        prose-pre:text-gray-800
                        prose-code:text-gray-800
                        prose-blockquote:text-gray-800
                        prose-li:marker:text-gray-800"
                      components={markdownComponents}
                    >
                      {message.text}
                    </ReactMarkdown>
                  ) : (
                    message.text
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-white text-gray-800 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="border-t bg-white p-4">
          <div className="mx-auto max-w-3xl">
            <form onSubmit={handleSendMessage} className="flex items-center gap-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ställ en fråga om dina mötesanteckningar..."
                className="rounded-full border-gray-300"
                disabled={isLoading}
              />
              <Button 
                type="submit"
                className="rounded-full px-6 bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg transition-all" 
                disabled={!inputValue.trim() || isLoading}
              >
                Skicka <Send className="ml-2 h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}