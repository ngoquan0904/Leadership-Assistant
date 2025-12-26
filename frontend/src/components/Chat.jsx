import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, AlertCircle, LayoutGrid } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Marketplace from './Marketplace';

const BACKEND_URL = "ws://localhost:8001/ws/chat";

export default function Chat({ sessionId, title, initialMessages, onMessagesUpdate }) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState(initialMessages || []);
  const [showMarketplace, setShowMarketplace] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const streamControllerRef = useRef({ abort: false });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const updateMessages = (newMessages) => {
    setMessages(newMessages);
    onMessagesUpdate(newMessages);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    // Add user message
    const msgsWithUser = [...messages, { role: 'user', content: userMessage }];
    updateMessages(msgsWithUser);
    setIsLoading(true);

    try {
      // abort any previous streaming
      streamControllerRef.current.abort = true;
      streamControllerRef.current = { abort: false };

      const ws = new WebSocket(BACKEND_URL);
      
      ws.onopen = () => {
        ws.send(JSON.stringify({
          query: userMessage,
          session_id: sessionId
        }));
      };

      // Add placeholder for assistant message (streaming)
      const msgsWithAssistant = [...msgsWithUser, { role: 'assistant', content: '', complete: false }];
      updateMessages(msgsWithAssistant);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.is_task_complete) {
          // Stream the final text token-by-token into the last assistant message
          streamTextToLastMessage(data.content, streamControllerRef.current)
            .then(() => {
              ws.close();
            })
            .catch(() => {
              ws.close();
            });
        } else {
          if (data.updates) {
            // Optionally handle intermediate update messages from backend
          }
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // update last assistant message to error and mark complete
        setMessages(prev => {
            const newMsgs = [...prev];
            if (newMsgs.length > 0) {
                newMsgs[newMsgs.length - 1] = { role: 'assistant', content: "Sorry, I encountered an error connecting to the server.", complete: true };
            } else {
                newMsgs.push({ role: 'assistant', content: "Sorry, I encountered an error connecting to the server.", complete: true });
            }
            onMessagesUpdate(newMsgs);
            return newMsgs;
        });
        // cancel streaming
        streamControllerRef.current.abort = true;
        setIsLoading(false);
      };

      ws.onclose = () => {
        // ensure any active streaming is stopped
        streamControllerRef.current.abort = true;
        if (isLoading) setIsLoading(false);
      };

    } catch (error) {
      console.error('Error:', error);
      setIsLoading(false);
    }
  };

    // Streams text token-by-token into the last assistant message.
    // controller should be an object with { abort: boolean } to cancel.
    const streamTextToLastMessage = async (text, controller) => {
      if (!text) {
        setIsLoading(false);
        return;
      }

      // Tokenize roughly by words while preserving whitespace
      const tokens = text.match(/\S+\s*/g) || [text];

      for (let i = 0; i < tokens.length; i++) {
        if (controller && controller.abort) break;

        const token = tokens[i];

        // Append token to last assistant message
        setMessages(prev => {
            const newMsgs = [...prev];
            const last = newMsgs[newMsgs.length - 1] || { role: 'assistant', content: '' };
            newMsgs[newMsgs.length - 1] = { role: 'assistant', content: (last.content || '') + token, complete: false };
            // We don't call onMessagesUpdate here to avoid excessive re-renders in parent
            return newMsgs;
        });

        const delay = 30;
        await new Promise(res => setTimeout(res, delay));
      }

      // If not aborted, mark final message as complete and render full Markdown
      if (!(controller && controller.abort)) {
        setMessages(prev => {
            const newMsgs = [...prev];
            newMsgs[newMsgs.length - 1] = { role: 'assistant', content: text, complete: true };
            onMessagesUpdate(newMsgs); // Sync with parent at the end
            return newMsgs;
        });
      }

      setIsLoading(false);
    };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (showMarketplace) {
    return <Marketplace onClose={() => setShowMarketplace(false)} />;
  }

  return (
    <div className="flex h-full bg-white flex-col">
      {/* Header */}
      <header className="p-4 border-b border-gray-200 bg-white/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-3xl mx-auto flex justify-end">
          <button
            onClick={() => setShowMarketplace(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LayoutGrid className="w-4 h-4" />
            Explore Marketplace
          </button>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col pb-32 max-w-3xl mx-auto p-4">
          {(!messages || messages.length === 0) ? (
                <div className="flex flex-col items-center justify-center h-[50vh] text-gray-500">
                  <Bot className="w-16 h-16 mb-4 opacity-50 text-blue-500" />
                  <p className="text-lg font-medium">How can I help you today?</p>
                </div>
              ) : (
              messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex w-full mb-6 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div className={`flex max-w-[85%] ${
                msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 flex flex-col relative ${
                    msg.role === 'user' ? 'ml-3' : 'mr-3'
                }`}>
                  {msg.role === 'assistant' ? (
                    <div className="w-8 h-8 rounded-full bg-teal-500 flex items-center justify-center shadow-sm">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shadow-sm">
                      <User className="w-5 h-5 text-gray-600" />
                    </div>
                  )}
                </div>
                {/* Message Content */}
                <div className={`relative overflow-hidden ${
                    msg.role === 'user' 
                    ? 'bg-gray-100 rounded-2xl px-5 py-3 text-gray-800' 
                    : 'bg-transparent text-gray-800 px-0 py-1'
                }`}>
                  {msg.content ? (
                    <div className={`prose max-w-none leading-7 text-gray-800 ${
                        msg.role === 'user' ? 'prose-p:my-0' : ''
                    }`}>
                      {msg.role === 'assistant' ? (
                        // If assistant message is complete, render full Markdown; otherwise render plain text while streaming
                        msg.complete ? (
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        ) : (
                          <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                        )
                      ) : (
                        // user messages render Markdown
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      )}

                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-gray-500 animate-pulse">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Thinking...</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6">
        <div className="max-w-3xl mx-auto px-4">
          <div className="relative flex items-center w-full p-3 bg-white rounded-xl border border-gray-200 shadow-xl focus-within:border-blue-400 ring-offset-2 focus-within:ring-2 ring-blue-100 transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Send a message..."
              className="w-full max-h-[200px] py-2 pl-3 pr-12 bg-transparent border-0 focus:ring-0 ring-0 outline-none focus:outline-none appearance-none resize-none text-gray-900 placeholder-gray-400 scrollbar-hide"
              rows={1}
              style={{ minHeight: '44px' }}
            />
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading}
              className={`absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-md transition-colors ${
                input.trim() && !isLoading
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-md'
                  : 'bg-transparent text-gray-300 cursor-not-allowed'
              }`}
              style={{ transform: 'translateY(-50%)' }}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
          <p className="text-xs text-center text-gray-400 mt-2">
            Leadership Assistant can make mistakes. Consider checking important information.
          </p>
        </div>
      </div>
    </div>
  );
}
