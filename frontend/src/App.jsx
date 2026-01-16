import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import { MessageSquare, Plus, Trash2, Menu, PanelLeftClose, PanelLeftOpen, MoreHorizontal, Search, LayoutGrid, Bot } from 'lucide-react';

function App() {
  const [sessions, setSessions] = useState(() => {
    try {
      const saved = localStorage.getItem('chat_sessions');
      const parsed = saved ? JSON.parse(saved) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.error('Failed to load sessions', e);
      return [];
    }
  });
  
  const [activeSessionId, setActiveSessionId] = useState(() => {
    return localStorage.getItem('active_session_id') || null;
  });

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [openMenuSessionId, setOpenMenuSessionId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [draftSession, setDraftSession] = useState(null);
  const [showMarketplace, setShowMarketplace] = useState(false);
  const commitLockRef = React.useRef(new Set());

  // Initialization: ensure we have an active session
  useEffect(() => {
    if (!activeSessionId || (activeSessionId && !sessions.some(s => s.id === activeSessionId))) {
      createNewSession(true);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('chat_sessions', JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    if (activeSessionId) {
      localStorage.setItem('active_session_id', activeSessionId);
    }
  }, [activeSessionId]);

  // Debug logging to help trace session lifecycle
  useEffect(() => {
    console.debug('[App] sessions changed', sessions);
  }, [sessions]);

  useEffect(() => {
    console.debug('[App] draftSession changed', draftSession);
  }, [draftSession]);
  // createNewSession(asDraft = true) - when asDraft is true we only create a transient draft
  // that won't appear in the sidebar until the user sends a message.
  const createNewSession = (asDraft = true) => {
    // If a draft session already exists and is empty, reuse it instead of creating another
    if (draftSession && (!draftSession.messages || draftSession.messages.length === 0)) {
      setActiveSessionId(draftSession.id);
      if (window.innerWidth < 768) setIsSidebarOpen(false);
      return;
    }
    // (previous guard removed) allow creating a new draft even if an empty 'New Chat' exists

    const newId = 'session-' + Math.random().toString(36).substr(2, 9);
    const newSessionObj = {
      id: newId,
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      pinned: false
    };

    if (asDraft) {
      setDraftSession(newSessionObj);
      setActiveSessionId(newId);
    } else {
      setSessions(prev => [newSessionObj, ...prev]);
      setActiveSessionId(newId);
    }

    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  const deleteSession = (e, sessionId) => {
    e.stopPropagation();
    const newSessions = sessions.filter(s => s.id !== sessionId);
    setSessions(newSessions);
    if (openMenuSessionId === sessionId) setOpenMenuSessionId(null);
    
    if (activeSessionId === sessionId) {
      if (newSessions.length > 0) {
        setActiveSessionId(newSessions[0].id);
      } else {
        setActiveSessionId(null);
        // Create new session immediately if all deleted
        setTimeout(() => createNewSession(), 0);
      }
    }
  };

  const togglePinSession = (e, sessionId) => {
    e.stopPropagation();
    setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, pinned: !s.pinned } : s));
    setOpenMenuSessionId(null);
  };

  const renameSession = (e, sessionId) => {
    e.stopPropagation();
    const session = sessions.find(s => s.id === sessionId);
    const newTitle = prompt("Rename chat", session?.title);
    if (newTitle) {
        setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s));
    }
    setOpenMenuSessionId(null);
  };

  const updateSessionMessages = (sessionId, newMessages) => {
    // If this update is for a draft session, update the draft and commit when user sends a message
    if (draftSession && draftSession.id === sessionId) {
      setDraftSession(prev => ({ ...prev, messages: newMessages }));

      // If the user has sent at least one user message, commit draft into sessions
      const hasUserMsg = newMessages.some(m => m.role === 'user');
      if (hasUserMsg) {
        // Prevent committing the same draft multiple times when updates happen rapidly
        if (commitLockRef.current.has(draftSession.id)) return;
        commitLockRef.current.add(draftSession.id);

        // generate title from first user message
        const firstUserMsg = newMessages.find(m => m.role === 'user');
        const title = firstUserMsg ? (firstUserMsg.content.slice(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '')) : 'New Chat';

        const committed = { ...draftSession, messages: newMessages, title };
        setSessions(prev => [committed, ...prev]);
        setDraftSession(null);
        setActiveSessionId(committed.id);
      }

      return;
    }

    // Otherwise update an existing session
    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        // Generate a title from the first user message if it's still "New Chat"
        let title = session.title;
        if (session.title === 'New Chat' && newMessages.length > 0) {
          const firstUserMsg = newMessages.find(m => m.role === 'user');
          if (firstUserMsg) {
            title = firstUserMsg.content.slice(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '');
          }
        }
        return { ...session, messages: newMessages, title };
      }
      return session;
    }));
  };

  const activeSession = (draftSession && draftSession.id === activeSessionId) 
    ? draftSession 
    : sessions.find(s => s.id === activeSessionId) || sessions[0] || draftSession;

  useEffect(() => {
    if (activeSession && activeSession.id !== activeSessionId) {
        setActiveSessionId(activeSession.id);
    }
  }, [activeSession, activeSessionId]);

  return (
    <div className="h-screen w-full flex bg-gray-50 overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-20 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed md:static inset-y-0 left-0 z-30
        w-72 bg-[#f8fafc] border-r border-slate-200/60 text-slate-800 flex flex-col transition-all duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden'}
      `}>
        <div className="p-5 flex items-center justify-between">
          <div className="flex items-center gap-3 px-1">
            <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200 ring-1 ring-white/20">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-slate-900 tracking-tight leading-none">Leadership</span>
              <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-widest mt-1">Intelligence</span>
            </div>
          </div>
          <button 
              onClick={() => setIsSidebarOpen(false)}
              className="p-2 hover:bg-slate-200/50 text-slate-400 hover:text-slate-600 rounded-xl transition-all md:hidden"
              title="Close Sidebar"
          >
              <PanelLeftClose className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-2 space-y-8">
          {/* New chat button */}
          <div className="space-y-4">
            <button
              onClick={createNewSession}
              className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-300 text-slate-700 transition-all group active:scale-[0.98]"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-600 group-hover:text-white transition-all duration-300">
                  <Plus className="w-4 h-4" />
                </div>
                <span className="text-sm font-bold tracking-tight">New Conversation</span>
              </div>
              <kbd className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 text-[9px] font-bold text-slate-400 bg-slate-50 border border-slate-100 rounded-lg">
                ⌘ K
              </kbd>
            </button>

            <div className="relative group">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search history..."
                className="w-full pl-11 pr-4 py-3 text-sm rounded-2xl border border-slate-200 bg-white text-slate-700 placeholder:text-slate-400 focus:ring-4 focus:ring-indigo-50 focus:border-indigo-400 transition-all outline-none"
              />
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                <Search className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Chat History */}
          <div className="space-y-2">
            <div className="flex items-center justify-between px-2 mb-3">
              <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em]">Recent Sessions</h3>
              <span className="text-[10px] font-bold text-slate-300 bg-slate-100 px-2 py-0.5 rounded-full">{Array.isArray(sessions) ? sessions.length : 0}</span>
            </div>
            
            <div className="space-y-1.5 px-0.5">
              {Array.isArray(sessions) && sessions.length > 0 ? (
                sessions
                  .filter(s => (s.title || 'New Chat').toLowerCase().includes((searchQuery || '').toLowerCase()))
                  .map(session => (
                <div
                  key={session.id}
                  onClick={() => {
                    setActiveSessionId(session.id);
                    if (window.innerWidth < 768) setIsSidebarOpen(false);
                  }}
                  className={`
                    group flex items-center gap-3 p-3.5 rounded-2xl cursor-pointer transition-all relative
                    ${activeSessionId === session.id 
                      ? 'bg-white shadow-[0_2px_12px_-3px_rgba(0,0,0,0.06)] border border-slate-200/80 text-indigo-600' 
                      : 'text-slate-600 hover:bg-white hover:shadow-sm hover:border-slate-200/50 border border-transparent'}
                  `}
                >
                  <div className={`p-2 rounded-xl transition-all duration-300 ${activeSessionId === session.id ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-500'}`}>
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <div className="flex-1 truncate text-sm font-semibold tracking-tight">
                    {session.title}
                  </div>
                  
                  {session.pinned && (
                    <div className="absolute -left-1 top-1/2 -translate-y-1/2 w-1 h-4 bg-indigo-500 rounded-full shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
                  )}

                  <div className="relative flex items-center">
                    <button 
                        onClick={(e) => {
                            e.stopPropagation();
                            setOpenMenuSessionId(openMenuSessionId === session.id ? null : session.id);
                        }}
                        className={`p-1.5 rounded-lg hover:bg-slate-100 transition-all ${openMenuSessionId === session.id ? 'opacity-100 bg-slate-100' : 'opacity-0 group-hover:opacity-100'}`}
                    >
                        <MoreHorizontal className="w-4 h-4" />
                    </button>
                    
                    {openMenuSessionId === session.id && (
                        <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-slate-100 rounded-2xl shadow-xl z-50 py-2 border border-slate-100 animate-fade-in ring-1 ring-black/5">
                            <button 
                                onClick={(e) => togglePinSession(e, session.id)} 
                                className="w-full text-left px-4 py-2.5 text-xs font-bold uppercase tracking-wider hover:bg-slate-50 flex items-center gap-3 transition-colors"
                            >
                                <span className="opacity-60">{session.pinned ? '📍' : '📌'}</span>
                                {session.pinned ? 'Unpin Chat' : 'Pin Chat'}
                            </button>
                            <button 
                                onClick={(e) => renameSession(e, session.id)} 
                                className="w-full text-left px-4 py-2.5 text-xs font-bold uppercase tracking-wider hover:bg-slate-50 flex items-center gap-3 transition-colors text-slate-600"
                            >
                                <span className="opacity-60">✏️</span>
                                Rename
                            </button>
                            <div className="h-px bg-slate-100 my-1.5 mx-2" />
                            <button 
                                onClick={(e) => deleteSession(e, session.id)} 
                                className="w-full text-left px-4 py-2.5 text-xs font-bold uppercase tracking-wider hover:bg-red-50 text-red-500 flex items-center gap-3 transition-colors"
                            >
                                <span className="opacity-60">🗑️</span>
                                Delete session
                            </button>
                        </div>
                    )}
                  </div>
                </div>
              ))
              ) : (
                <div className="text-center py-6 px-4">
                  <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center mx-auto mb-3 opacity-50">
                    <MessageSquare className="w-5 h-5 text-slate-400" />
                  </div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">No history yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* User Profile */}
        <div className="p-4 border-t border-slate-100 bg-[#f8fafc]">
           <div className="flex items-center justify-between p-3 rounded-2xl hover:bg-white hover:shadow-sm border border-transparent hover:border-slate-200 transition-all cursor-pointer group">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-sm font-bold text-white shadow-lg shadow-indigo-100 ring-1 ring-white/20">
                  NM
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-bold text-slate-900 leading-tight">Ngo Minh Quan</span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_4px_rgba(99,102,241,0.5)]"></span>
                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest leading-none">Pro Plan</span>
                  </div>
                </div>
              </div>
              <MoreHorizontal className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition-colors" />
           </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full relative w-full bg-white overflow-hidden">
        {/* Top header */}
        <div className="w-full border-b border-slate-100 bg-white/70 backdrop-blur-xl p-4 flex items-center justify-between sticky top-0 z-40 transition-all">
          <div className="flex items-center gap-4">
            {!isSidebarOpen && (
              <button 
                  onClick={() => setIsSidebarOpen(true)}
                  className="p-2.5 hover:bg-slate-100 rounded-xl text-slate-400 hover:text-indigo-600 transition-all active:scale-95"
                  title="Open Sidebar"
              >
                  <PanelLeftOpen className="w-5 h-5" />
              </button>
            )}
            <div className="flex flex-col">
              <h1 className="text-sm font-bold text-slate-900 tracking-tight">
                {activeSession?.title || 'Leadership Assistant'}
              </h1>
              {activeSession && <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">Conversation ID: {activeSession.id.slice(-6)}</span>}
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button
                onClick={() => setShowMarketplace(!showMarketplace)}
                className="flex items-center gap-2 px-3 py-1.5 text-[10px] font-bold text-indigo-600 bg-indigo-50 hover:bg-indigo-600 hover:text-white rounded-xl transition-all uppercase tracking-wider border border-indigo-100"
            >
                <LayoutGrid className="w-3.5 h-3.5" />
                {showMarketplace ? 'Back to Chat' : 'Marketplace'}
            </button>
            <div className="px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100/50 flex items-center gap-2 shadow-sm shadow-emerald-50">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[9px] font-bold text-emerald-700 uppercase tracking-[0.1em]">Cloud Sync Active</span>
            </div>
          </div>
        </div>

        {activeSession ? (
          <Chat 
            key={activeSession.id} // Force remount on session change
            sessionId={activeSession.id}
            title={activeSession.title}
            initialMessages={activeSession.messages}
            onMessagesUpdate={(msgs) => updateSessionMessages(activeSession.id, msgs)}
            showMarketplace={showMarketplace}
            setShowMarketplace={setShowMarketplace}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center bg-white">
            <p className="text-gray-500">Select or create a chat to start.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
