import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, AlertCircle, LayoutGrid } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Marketplace from './Marketplace';
import Settings from './Settings';

const BACKEND_URL = "ws://localhost:8001/ws/chat";

export default function Chat({ sessionId, title, initialMessages, onMessagesUpdate, showMarketplace, setShowMarketplace, showSettings, setShowSettings }) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState(initialMessages || []);

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

  const handleSubmit = async (e, directMessage = null) => {
    if (e) e.preventDefault();
    
    const messageToSend = directMessage || input.trim();
    if (!messageToSend || isLoading) return;

    if (!directMessage) {
        setInput('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }

    // Add user message
    const msgsWithUser = [...messages, { role: 'user', content: messageToSend }];
    updateMessages(msgsWithUser);
    setIsLoading(true);

    try {
      // abort any previous streaming
      streamControllerRef.current.abort = true;
      streamControllerRef.current = { abort: false };

      const ws = new WebSocket(BACKEND_URL);
      
      ws.onopen = () => {
        ws.send(JSON.stringify({
          query: messageToSend,
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

  if (showSettings) {
    return <Settings onBack={() => setShowSettings(false)} />;
  }

  if (showMarketplace) {
    return <Marketplace onClose={() => setShowMarketplace(false)} />;
  }

  return (
    <div className="flex flex-1 bg-white flex-col overflow-hidden relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-hide py-4">
        <div className="flex flex-col max-w-4xl mx-auto p-4 sm:p-8 space-y-10 pb-10">
          {(!messages || messages.length === 0) ? (
                <div className="flex flex-col items-center justify-center h-[55vh] animate-fade-in text-center">
                  <div className="relative mb-10">
                    <div className="absolute inset-0 bg-indigo-500 blur-3xl opacity-20 animate-pulse"></div>
                    <div className="relative w-24 h-24 bg-white rounded-[2.5rem] flex items-center justify-center shadow-2xl shadow-indigo-100 border border-slate-100 ring-1 ring-slate-100/50">
                      <Bot className="w-12 h-12 text-indigo-600" />
                    </div>
                  </div>
                  <h2 className="text-3xl font-bold text-slate-900 mb-3 tracking-tight">How can I assist your leadership today?</h2>
                  <p className="text-slate-500 text-base max-w-md mx-auto leading-relaxed font-medium">
                    I'm your AI-powered Intelligence Suite. I can manage your <span className="text-indigo-600">calendar</span>, draft <span className="text-indigo-600">professional emails</span>, and analyze <span className="text-indigo-600">company documents</span>.
                  </p>
                  <div className="grid grid-cols-2 gap-3 mt-10 w-full max-w-lg">
                    {[
                      'Kiểm tra lịch của tôi ngày hôm nay', 
                      'Tóm tắt các email hôm nay', 
                      'Chỉ số bụi mịn ở Hà Nội ngày hôm nay', 
                      'Tóm tắt các tài liệu mới nhất'
                    ].map((hint) => (
                      <button 
                        key={hint}
                        onClick={() => handleSubmit(null, hint)}
                        className="p-4 text-left text-sm font-semibold text-slate-600 bg-slate-50 hover:bg-white hover:shadow-md hover:border-indigo-200 border border-slate-100 rounded-2xl transition-all active:scale-95"
                      >
                        {hint}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
              messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex w-full animate-fade-in ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div className={`flex max-w-[92%] sm:max-w-[85%] ${
                msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              } gap-4 sm:gap-5`}>
                {/* Avatar */}
                <div className="flex-shrink-0 mt-0.5">
                  {msg.role === 'assistant' ? (
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center shadow-lg shadow-indigo-100 border border-indigo-400/20 ring-4 ring-white">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-2xl bg-white border border-slate-200 flex items-center justify-center shadow-sm ring-4 ring-slate-50">
                      <User className="w-5 h-5 text-slate-500" />
                    </div>
                  )}
                </div>

                {/* Message Content */}
                <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} space-y-1.5`}>
                  <div className={`px-6 py-4 rounded-[1.5rem] shadow-md ${
                      msg.role === 'user' 
                      ? 'bg-indigo-600 text-white rounded-tr-none' 
                      : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none'
                  }`}>
                    {msg.content ? (
                        msg.role === 'user' ? (
                          <div className="whitespace-pre-wrap text-[15px] font-semibold tracking-tight leading-relaxed text-white">
                            {msg.content}
                          </div>
                        ) : (
                          <div className="prose max-w-none prose-slate prose-p:leading-relaxed prose-pre:bg-slate-900 prose-pre:rounded-2xl">
                            {msg.complete ? (
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {msg.content}
                              </ReactMarkdown>
                            ) : (
                              <div className="whitespace-pre-wrap font-medium leading-relaxed opacity-90">{msg.content}</div>
                            )}
                          </div>
                        )
                    ) : (
                      <div className="flex items-center gap-3 text-indigo-600 py-2">
                        <div className="flex gap-1.5">
                          <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce [animation-delay:-0.3s]" />
                          <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce [animation-delay:-0.15s]" />
                          <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" />
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-[0.2em] ml-1">Processing Analysis</span>
                      </div>
                    )}
                  </div>
                  {msg.role === 'assistant' && msg.complete && (
                    <div className="mt-1 flex items-center gap-5 px-3">
                      <button className="text-[9px] font-bold text-slate-300 hover:text-indigo-600 uppercase tracking-widest transition-colors flex items-center gap-1.5">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>
                        Copy
                      </button>
                      <button className="text-[9px] font-bold text-slate-300 hover:text-indigo-600 uppercase tracking-widest transition-colors flex items-center gap-1.5">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                        Regenerate
                      </button>
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
      <div className="w-full bg-white p-6 sm:p-8 relative z-20">
        <div className="max-w-4xl mx-auto relative">
          <div className="relative flex items-end w-full p-2.5 bg-slate-50 rounded-[2rem] border border-slate-200/80 focus-within:border-indigo-400 focus-within:ring-[6px] focus-within:ring-indigo-500/5 focus-within:bg-white transition-all group shadow-sm">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Deep search or ask a leadership question..."
              className="w-full max-h-[300px] py-4 pl-6 pr-16 bg-transparent border-0 focus:ring-0 ring-0 outline-none appearance-none resize-none text-base text-slate-900 placeholder:text-slate-400 font-semibold leading-relaxed"
              rows={1}
              style={{ minHeight: '56px' }}
            />
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading}
              className={`absolute right-3.5 bottom-3.5 p-3.5 rounded-2xl transition-all duration-300 ${
                input.trim() && !isLoading
                  ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-200 hover:bg-indigo-700 hover:-translate-y-1 active:translate-y-0 scale-100'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed scale-95 opacity-50'
              }`}
            >
              {isLoading ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <Send className="w-6 h-6" />
              )}
            </button>
          </div>
          <div className="flex items-center justify-center gap-6 mt-4 opacity-70">
            <p className="text-[11px] font-medium text-slate-500 text-center">
              Leadership Assistant can make mistakes. Consider checking important information.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
