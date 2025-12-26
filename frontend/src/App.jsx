import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import { MessageSquare, Plus, Trash2, Menu, PanelLeftClose, PanelLeftOpen, MoreHorizontal, Search } from 'lucide-react';

function App() {
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('chat_sessions');
    return saved ? JSON.parse(saved) : [];
  });
  
  const [activeSessionId, setActiveSessionId] = useState(null);

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [openMenuSessionId, setOpenMenuSessionId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [draftSession, setDraftSession] = useState(null);
  const commitLockRef = React.useRef(new Set());

  useEffect(() => {
    localStorage.setItem('chat_sessions', JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    if (activeSessionId) {
      localStorage.setItem('active_session_id', activeSessionId);
    }
  }, [activeSessionId]);

  // Always start with a new draft session
  useEffect(() => {
    createNewSession(true);
  }, []);

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

  const activeSession = (draftSession && draftSession.id === activeSessionId) ? draftSession : sessions.find(s => s.id === activeSessionId);

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
        w-64 bg-white border-r border-gray-200 text-gray-800 flex flex-col transition-all duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden'}
      `}>
        <div className="p-4 border-b border-gray-100 flex items-center justify-center relative">
          <h2 className="font-bold text-lg text-blue-600 hidden">Leadership Assistant</h2>
          <div className="flex items-center gap-1 absolute right-2">
            <button 
                onClick={createNewSession}
                className="p-2 hover:bg-blue-50 text-gray-600 hover:text-blue-600 rounded-full transition-colors"
                title="New Chat"
            >
                <Plus className="w-5 h-5" />
            </button>
            <button 
                onClick={() => setIsSidebarOpen(false)}
                className="p-2 hover:bg-blue-50 text-gray-600 hover:text-blue-600 rounded-full transition-colors md:hidden"
            >
                <PanelLeftClose className="w-5 h-5" />
            </button>
             <button 
                onClick={() => setIsSidebarOpen(false)}
                className="p-2 hover:bg-blue-50 text-gray-600 hover:text-blue-600 rounded-full transition-colors hidden md:block"
                title="Close Sidebar"
            >
                <PanelLeftClose className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {/* New chat button and search */}
          <div className="px-1">
            <button
              onClick={createNewSession}
              className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 text-gray-700"
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm font-medium">New chat</span>
            </button>

            <div className="mt-2 relative">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search chats"
                className="w-full pl-3 pr-9 py-2 text-sm rounded-md border border-gray-100 bg-gray-50 text-gray-700"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400">
                <Search className="w-4 h-4" />
              </div>
            </div>
          </div>

          {sessions
            .filter(s => s.title.toLowerCase().includes(searchQuery.toLowerCase()))
            .map(session => (
            <div
              key={session.id}
              onClick={() => {
                setActiveSessionId(session.id);
                if (window.innerWidth < 768) setIsSidebarOpen(false);
              }}
              className={`
                group flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors border border-transparent relative
                ${activeSessionId === session.id ? 'bg-blue-50 text-blue-700 border-blue-100' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
              `}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
              <div className="flex-1 truncate text-sm font-medium">
                {session.title} {session.pinned && '📌'}
              </div>
              
              <div className="relative">
                <button 
                    onClick={(e) => {
                        e.stopPropagation();
                        setOpenMenuSessionId(openMenuSessionId === session.id ? null : session.id);
                    }}
                    className={`p-1 rounded hover:bg-gray-200 transition-opacity ${openMenuSessionId === session.id ? 'opacity-100 bg-gray-200' : 'opacity-0 group-hover:opacity-100'}`}
                >
                    <MoreHorizontal className="w-4 h-4" />
                </button>
                
                {openMenuSessionId === session.id && (
                    <div className="absolute right-0 top-full mt-1 w-32 bg-white border rounded shadow-lg z-50 py-1">
                        <button 
                            onClick={(e) => togglePinSession(e, session.id)} 
                            className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100"
                        >
                            {session.pinned ? 'Unpin Chat' : 'Pin Chat'}
                        </button>
                        <button 
                            onClick={(e) => renameSession(e, session.id)} 
                            className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100"
                        >
                            Rename Chat
                        </button>
                        <button 
                            onClick={(e) => deleteSession(e, session.id)} 
                            className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 text-red-600"
                        >
                            Remove Chat
                        </button>
                    </div>
                )}
              </div>
            </div>
          ))}
        </div>
        
        {/* User Profile / Footer */}
        <div className="p-4 border-t border-gray-100 bg-gray-50/50">
           <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-sm font-medium text-white shadow-sm">
                LA
              </div>
              <div className="text-sm font-medium text-gray-700 truncate">User</div>
           </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full relative w-full bg-white">
        {/* Top full-width header with centered title */}
        <div className="w-full border-b bg-white p-4 flex items-center justify-center sticky top-0 z-40">
          <h1 className="text-lg font-bold text-gray-800">Leadership Assistant</h1>
        </div>
        {/* Toggle Button when sidebar is closed */}
        {!isSidebarOpen && (
            <div className="absolute top-4 left-4 z-50">
                <button 
                    onClick={() => setIsSidebarOpen(true)}
                    className="p-2 bg-white hover:bg-gray-50 rounded-md shadow-md border border-gray-200 text-gray-600 hover:text-blue-600 transition-all"
                    title="Open Sidebar"
                >
                    <PanelLeftOpen className="w-5 h-5" />
                </button>
            </div>
        )}

        {activeSession ? (
          <Chat 
            key={activeSession.id} // Force remount on session change
            sessionId={activeSession.id}
            title={activeSession.title}
            initialMessages={activeSession.messages}
            onMessagesUpdate={(msgs) => updateSessionMessages(activeSession.id, msgs)}
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
