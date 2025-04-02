import { useState, useRef, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Bot, User, SendIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useMCPChat, MCPToolResponse } from "./services/mcpService";

// QueryClient setup
const queryClient = new QueryClient();

// Types
type MessageType = {
  id: string;
  content: string;
  isUser: boolean;
  isTool?: boolean;
  isError?: boolean;
};

// Message Component
const Message = ({ content, isUser, isTool, isError }: { 
  content: string, 
  isUser: boolean,
  isTool?: boolean,
  isError?: boolean
}) => {
  return (
    <div className="flex w-full mb-6">
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mr-3",
        isUser ? "bg-primary text-primary-foreground" : 
        isError ? "bg-destructive text-destructive-foreground" :
        isTool ? "bg-secondary text-secondary-foreground" : "bg-muted"
      )}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>
      <div className="flex-grow">
        <div className="font-semibold text-sm mb-1">
          {isUser ? "You" : isTool ? "Tool Result" : isError ? "Error" : "AI Assistant"}
        </div>
        <div className={cn(
          "text-sm",
          isUser ? "" : 
          isTool ? "bg-muted p-3 rounded-md font-mono text-xs" : 
          isError ? "text-destructive" : "prose prose-sm max-w-none"
        )}>
          <p className="whitespace-pre-wrap break-words">{content}</p>
        </div>
      </div>
    </div>
  );
};

// Loading Dots Component
const LoadingDots = () => {
  return (
    <div className="flex w-full mb-6">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center mr-3">
        <Bot className="w-4 h-4" />
      </div>
      <div className="flex-grow">
        <div className="font-semibold text-sm mb-1">
          AI Assistant
        </div>
        <div className="flex items-center space-x-1">
          <div className="h-2 w-2 bg-primary/40 rounded-full animate-pulse" style={{ animationDelay: "0ms" }}></div>
          <div className="h-2 w-2 bg-primary/40 rounded-full animate-pulse" style={{ animationDelay: "300ms" }}></div>
          <div className="h-2 w-2 bg-primary/40 rounded-full animate-pulse" style={{ animationDelay: "600ms" }}></div>
        </div>
      </div>
    </div>
  );
};

// Chat Input Component
const ChatInput = ({ onSendMessage, disabled }: { onSendMessage: (message: string) => void, disabled?: boolean }) => {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() === "" || disabled) return;
    
    onSendMessage(message);
    setMessage("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question..."
          className="min-h-[60px] resize-none pr-14 rounded-xl"
          disabled={disabled}
        />
        <Button 
          type="submit" 
          size="icon" 
          disabled={message.trim() === "" || disabled}
          className="absolute right-2 bottom-2 h-8 w-8 rounded-lg"
        >
          <SendIcon className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
};

// Chat Component
const Chat = () => {
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: "welcome",
      content: "I'm an AI assistant for Modern Clinical Practice. How can I help with your veterinary patients today?",
      isUser: false
    }
  ]);
  const { sendMessage, isLoading } = useMCPChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: MessageType = {
      id: Date.now().toString(),
      content,
      isUser: true
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Get AI response from MCP service
      const responses = await sendMessage(content);
      
      // Process each response
      responses.forEach(response => {
        if (response.type === 'text') {
          const aiMessage: MessageType = {
            id: (Date.now() + Math.random()).toString(),
            content: response.content,
            isUser: false
          };
          setMessages(prev => [...prev, aiMessage]);
        } 
        else if (response.type === 'tool') {
          // Add tool result as a special message
          const toolContent = `Tool: ${response.name}\nArgs: ${JSON.stringify(response.args)}\nResult: ${response.result}`;
          const toolMessage: MessageType = {
            id: (Date.now() + Math.random()).toString(),
            content: toolContent,
            isUser: false,
            isTool: true
          };
          setMessages(prev => [...prev, toolMessage]);
        }
        else if (response.type === 'error') {
          const errorMessage: MessageType = {
            id: (Date.now() + Math.random()).toString(),
            content: `Error: ${response.content}`,
            isUser: false,
            isError: true
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      });
    } catch (error) {
      console.error("Failed to get response:", error);
      const errorMessage: MessageType = {
        id: (Date.now() + Math.random()).toString(),
        content: "Sorry, I encountered an error processing your request.",
        isUser: false,
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto py-6 px-4 scrollbar-thin">
        {messages.map(message => (
          <Message
            key={message.id}
            content={message.content}
            isUser={message.isUser}
            isTool={message.isTool}
            isError={message.isError}
          />
        ))}
        {isLoading && <LoadingDots />}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t p-4">
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
};

// Index Page Component
const Index = () => {
  return (
    <div className="flex flex-col h-screen bg-background">
      <header className="border-b p-4">
        <h1 className="text-xl font-bold text-center">Modern Clinical Practice</h1>
        <p className="text-center text-muted-foreground text-sm">Smart pet records for modern practitioners</p>
      </header>
      <main className="flex-1 container mx-auto max-w-4xl overflow-hidden flex flex-col">
        <Chat />
      </main>
    </div>
  );
};

// NotFound Page Component
const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-4xl font-bold mb-4">404</h1>
      <p className="text-xl mb-6">Page not found</p>
      <a href="/" className="text-blue-500 hover:underline">
        Go back home
      </a>
    </div>
  );
};

// Main App Component
const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
