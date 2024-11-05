'use client'

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, FileText } from "lucide-react"

export default function Component() {
  const [isHistoryVisible, setIsHistoryVisible] = useState(true)
  const [inputValue, setInputValue] = useState("")

  return (
    <div className="h-[calc(100vh-4rem)] flex bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Sidebar */}
      {isHistoryVisible && (
        <div className="w-64 border-r bg-white shadow-sm overflow-y-auto">
          <div className="p-4">
            <div className="mb-4 text-lg font-semibold">Chatthistorik</div>
            <div className="space-y-2">
              {["Tidigare möte 1", "Tidigare möte 2", "Tidigare möte 3"].map((chat, index) => (
                <button
                  key={index}
                  className="w-full rounded-lg p-2 text-left hover:bg-gray-100"
                >
                  {chat}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Simplified header */}
        <div className="flex items-center justify-start border-b bg-white p-4 shadow-sm">
          <button
            onClick={() => setIsHistoryVisible(!isHistoryVisible)}
            className="text-gray-500 hover:text-gray-700"
          >
            ☰
          </button>
        </div>

        {/* Chat Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-3xl">
            {/* Welcome Message */}
            <div className="mb-8 text-center">
              <h1 className="mb-2 text-3xl font-bold text-gray-800">
                Välkommen till LogBotAI
              </h1>
              <p className="text-gray-600">
                Hur kan jag hjälpa dig med dina mötesanteckningar idag?
              </p>
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t bg-white p-4">
          <div className="mx-auto max-w-3xl">
            <div className="flex items-center gap-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ställ en fråga om dina mötesanteckningar..."
                className="rounded-full border-gray-300"
              />
              <Button 
                className="rounded-full px-6 bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg transition-all" 
                disabled={!inputValue}
              >
                Skicka <Send className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}