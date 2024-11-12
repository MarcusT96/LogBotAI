'use client'

import { useState, useRef, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send } from "lucide-react"
import ReactMarkdown, { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Header from '@/components/header';

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
  const [messageIdCounter, setMessageIdCounter] = useState(2)
  const [sessionId, setSessionId] = useState<string>("")

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

  const renderText = (text: string) => {
    return <span>{text}</span>;
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading || !sessionId) return

    const userMessage = {
      id: messageIdCounter,
      text: inputValue.trim(),
      sender: 'user' as const
    }

    setMessageIdCounter(prev => prev + 1)
    setMessages(prev => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: userMessage.text,
          session_id: sessionId 
        }),
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const assistantMessage: Message = {
        id: messageIdCounter + 1,
        text: '',
        sender: 'ai'
      }
      setMessageIdCounter(prev => prev + 1)
      setMessages(prev => [...prev, assistantMessage])

      const reader = response.body?.getReader()

      if (reader) {
        const textDecoder = new TextDecoder()
        let buffer = ''
        let isFirstChunk = true
        
        const updateMessageWithDelay = async (text: string) => {
          if (isFirstChunk) {
            setIsLoading(false)
            isFirstChunk = false
          }
          
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            newMessages[newMessages.length - 1] = {
              ...lastMessage,
              text: text
            };
            return newMessages;
          });
          
          await new Promise(resolve => setTimeout(resolve, 50));
        };
        
        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            await updateMessageWithDelay(buffer)
            break
          }

          const chunk = textDecoder.decode(value, { stream: true })
          buffer += chunk
          await updateMessageWithDelay(buffer)
        }
        
        const finalChunk = textDecoder.decode()
        if (finalChunk) {
          buffer += finalChunk
          await updateMessageWithDelay(buffer)
        }
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        id: messageIdCounter + 1,
        text: 'Sorry, there was an error processing your request.',
        sender: 'ai'
      }])
      setMessageIdCounter(prev => prev + 1)
    } finally {
      setIsLoading(false)
    }
  }

  // Effect to load session ID from localStorage
  useEffect(() => {
    const savedSessionId = localStorage.getItem('chatSessionId');
    console.log('Retrieved session ID:', savedSessionId);
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  // If no session ID, show warning with the header
  if (!sessionId) {
    return (
      <>
        <Header showBackButton={true} />
        <div className="h-[calc(100vh-4rem)] flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
          <div className="text-center p-8 bg-white rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Inga dokument uppladdade</h2>
            <p>Vänligen ladda upp dokument först för att starta en chatt.</p>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Header showBackButton={true} />
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
                        components={{
                          ...markdownComponents,
                          p: ({ children }) => (
                            <p className="whitespace-pre-wrap">
                              {typeof children === 'string' && message.text === children ? (
                                renderText(children)
                              ) : children}
                            </p>
                          ),
                        }}
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
    </>
  )
}