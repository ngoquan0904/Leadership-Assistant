import React, { useState } from 'react';
import { Mail, Calendar, ArrowLeft, X, CheckCircle, ExternalLink, Users, FileText, Layout, Database, Search } from 'lucide-react';

export default function Marketplace({ onClose }) {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [installMode, setInstallMode] = useState(false);
  const [uploadedSecret, setUploadedSecret] = useState(null);
  const [secretFileObj, setSecretFileObj] = useState(null);
  const [senderEmailInput, setSenderEmailInput] = useState('');
  const [appPasswordInput, setAppPasswordInput] = useState('');
  const [installing, setInstalling] = useState(false);
  const [installResult, setInstallResult] = useState(null);

  const commonSetupSteps = [
    {
      title: "PHẦN 1 — TẠO CLIENT SECRET FILE (credentials.json)",
      items: [
        {
          subtitle: "1️⃣ Tạo / chọn Project trên Google Cloud",
          content: [
            { type: 'link', text: "Truy cập: https://console.cloud.google.com", url: "https://console.cloud.google.com" },
            { type: 'text', text: "Chọn Select a project → New Project" },
            { type: 'text', text: "Đặt tên project → Create" }
          ]
        },
        {
          subtitle: "2️⃣ Enable Gmail & Calendar API",
          content: [
            { type: 'text', text: "Vào APIs & Services → Library" },
            { type: 'text', text: "Tìm và Enable:" },
            { type: 'list', items: ["Gmail API", "Google Calendar API (nếu project dùng lịch)"] }
          ]
        },
        {
          subtitle: "3️⃣ Cấu hình OAuth Consent Screen",
          content: [
            { type: 'text', text: "Vào APIs & Services → OAuth consent screen" },
            { type: 'text', text: "Chọn User Type: External" },
            { type: 'text', text: "Click Create" },
            { type: 'text', text: "Điền thông tin cơ bản:" },
            { type: 'list', items: ["App name: ví dụ Gmail Agent", "User support email: Gmail của bạn", "Developer contact email: Gmail của bạn"] },
            { type: 'text', text: "→ Save and Continue" },
            { type: 'text', text: "Scopes: Có thể bỏ qua → Save and Continue" },
            { type: 'text', text: "Test Users (BẮT BUỘC):" },
            { type: 'list', items: ["Vào tab Audience", "Tại Test users → Add users", "Thêm chính Gmail của bạn", "Save"] },
            { type: 'note', text: "📌 Vì app đang ở chế độ Testing, chỉ Test users mới dùng được OAuth" }
          ]
        },
        {
          subtitle: "4️⃣ Tạo OAuth Credentials (Client Secret)",
          content: [
            { type: 'text', text: "Vào APIs & Services → Credentials" },
            { type: 'text', text: "Click Create Credentials" },
            { type: 'text', text: "Chọn OAuth client ID" },
            { type: 'text', text: "Application type: Desktop app" },
            { type: 'text', text: "Name: ví dụ Gmail Desktop Client" },
            { type: 'text', text: "Click Create" },
            { type: 'text', text: "➡️ Tải file JSON về" }
          ]
        }
      ]
    }
  ];

  const gmailExtraSetupSteps = [
    {
      title: "PHẦN 2 — TẠO SENDER PASSWORD (GMAIL APP PASSWORD)",
      description: "Dùng cho smtplib (SMTP Gmail)",
      items: [
        {
          subtitle: "6️⃣ Bật xác minh 2 bước (2FA)",
          content: [
            { type: 'link', text: "Truy cập: https://myaccount.google.com/security", url: "https://myaccount.google.com/security" },
            { type: 'text', text: "Bật 2-Step Verification" },
            { type: 'warning', text: "⚠️ Bắt buộc để tạo App Password" }
          ]
        },
        {
          subtitle: "7️⃣ Tạo App Password",
          content: [
            { type: 'link', text: "Truy cập: 👉 https://myaccount.google.com/apppasswords", url: "https://myaccount.google.com/apppasswords" },
            { type: 'text', text: "Đăng nhập Gmail" },
            { type: 'text', text: "Chọn:" },
            { type: 'list', items: ["App: Mail", "Device: Other", "Name: Python SMTP / Gmail Agent"] },
            { type: 'text', text: "Click Generate" }
          ]
        },
        {
          subtitle: "8️⃣ Lấy App Password",
          content: [
            { type: 'text', text: "Google sẽ cung cấp mật khẩu 16 ký tự, ví dụ: abcd efgh ijkl mnop" },
            { type: 'warning', text: "⚠️ Chỉ hiện 1 lần duy nhất → copy ngay" }
          ]
        }
      ]
    }
  ];

  const agents = [
    {
      id: 'gmail-agent',
      name: 'Gmail Agent',
      description: 'An agent that helps users manage and query their Gmail account.',
      icon: <Mail className="w-8 h-8 text-red-500" />,
      tags: ['Productivity', 'Communication'],
      author: 'Google',
      installs: '10k+',
      features: [
        "Create Email Content: Generate formatted email content with a signature.",
        "Create Email Draft: Create a draft email in the user's Gmail account.",
        "Send Email: Send an email from the user's Gmail account.",
        "Search Emails: Search for messages in Gmail.",
        "Get Thread: Retrieve an email thread.",
        "Get Message: Retrieve a specific email message."
      ],
      setupSteps: [...commonSetupSteps, ...gmailExtraSetupSteps]
    },
    {
      id: 'calendar-agent',
      name: 'Calendar Agent',
      description: 'An agent that helps users manage and query their Google Calendar.',
      icon: <Calendar className="w-8 h-8 text-blue-500" />,
      tags: ['Productivity', 'Scheduling'],
      author: 'Google',
      installs: '8k+',
      features: [
        "Search Events: Search for events in the user's calendar based on time, date, or keywords.",
        "Create Event: Create a new event in the user's calendar.",
        "Update Event: Update details of an existing event in the user's calendar.",
        "Delete Event: Delete an event from the calendar.",
        "Move Event: Move an event to a different time or date."
      ],
      setupSteps: commonSetupSteps
    },
    {
      id: 'hr-agent',
      name: 'HR Agent',
      description: 'An agent that helps users manage human resources, employee records, leave requests, and recruitment processes.',
      icon: <Users className="w-8 h-8 text-green-500" />,
      tags: ['HR', 'Management'],
      author: 'Cyberdyne Systems',
      installs: '5k+',
      features: [
        "Search Employees: Find employee information in the organization.",
        "Get Employee Information: Retrieve detailed employee profiles.",
        "Manage Leave Requests: Handle employee leave and vacation requests.",
        "Update Employee Record: Keep employee information up to date.",
        "Recruitment Management: Track and manage the hiring process."
      ],
      setupSteps: []
    },
    {
      id: 'document-agent',
      name: 'Document Agent',
      description: 'An agent that helps users retrieve relevant information chunks from the internal business and company documentation repository.',
      icon: <FileText className="w-8 h-8 text-orange-500" />,
      tags: ['Documentation', 'Knowledge Base'],
      author: 'Cyberdyne Systems',
      installs: '12k+',
      features: [
        "Get Relevant Chunks: Semantic search across company documents to find specific information.",
        "Contextual Search: Find policies, regulations, and internal processes."
      ],
      setupSteps: []
    },
    {
      id: 'project-manager-agent',
      name: 'Project Manager Agent',
      description: 'An agent for project management using Notion. It can manage tasks, projects, documentation, and assignments.',
      icon: <Layout className="w-8 h-8 text-purple-500" />,
      tags: ['Project Management', 'Notion'],
      author: 'Cyberdyne Systems',
      installs: '7k+',
      features: [
        "Notion Project Manager: Full integration with Notion for task tracking.",
        "Query Notion Database: Search and filter through project databases.",
        "Search Notion: Find any page or block within your Notion workspace.",
        "Manage Notion Pages: Create and update documentation in Notion."
      ],
      setupSteps: []
    },
    {
      id: 'ek-agent',
      name: 'Enterprise Knowledge Agent',
      description: 'An agent for enterprise knowledge management: supports HR information management, project management, and retrieval of software development business documents.',
      icon: <Database className="w-8 h-8 text-cyan-500" />,
      tags: ['Enterprise', 'Knowledge'],
      author: 'Cyberdyne Systems',
      installs: '15k+',
      features: [
        "Neo4j Integration: Query organizational graphs for complex relationships.",
        "Combined Knowledge: Access HR, Project, and Documentation data in one place.",
        "Advanced Reasoning: Connect dots across different internal systems.",
        "Multi-source Search: Search across Neo4j, Notion, and Vector databases."
      ],
      setupSteps: []
    },
    {
      id: 'search-agent',
      name: 'Search Agent',
      description: 'An agent that helps users search for information on the internet.',
      icon: <Search className="w-8 h-8 text-yellow-500" />,
      tags: ['Search', 'Research'],
      author: 'Tavily',
      installs: '20k+',
      features: [
        "Web Search: Search the web for information using Tavily.",
        "News Search: Get the latest news and updates from various sources."
      ],
      setupSteps: []
    }
  ];

  const renderContentItem = (item, index) => {
    switch (item.type) {
      case 'link':
        return (
          <a key={index} href={item.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline flex items-center gap-1 mb-1">
            {item.text} <ExternalLink className="w-3 h-3" />
          </a>
        );
      case 'list':
        return (
          <ul key={index} className="list-disc list-inside ml-4 mb-2 text-gray-700">
            {item.items.map((li, i) => <li key={i}>{li}</li>)}
          </ul>
        );
      case 'note':
        return (
          <div key={index} className="bg-blue-50 text-blue-800 p-2 rounded-md text-sm mb-2 border border-blue-100">
            {item.text}
          </div>
        );
      case 'warning':
        return (
          <div key={index} className="bg-yellow-50 text-yellow-800 p-2 rounded-md text-sm mb-2 border border-yellow-100">
            {item.text}
          </div>
        );
      default:
        return <p key={index} className="text-gray-700 mb-1">{item.text}</p>;
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#f8fafc] relative animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-5 bg-white/70 backdrop-blur-xl border-b border-slate-100 sticky top-0 z-10 transition-all">
        <div className="flex items-center gap-4">
          <button 
            onClick={onClose}
            className="p-2.5 hover:bg-slate-100 rounded-xl transition-all active:scale-95 group"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400 group-hover:text-indigo-600" />
          </button>
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Intelligence Marketplace</h2>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">Expand your agent capabilities</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-10">
        <div className="max-w-6xl mx-auto mb-12">
          <div className="flex items-center justify-between mb-8 px-2">
            <h3 className="text-lg font-bold text-slate-900 uppercase tracking-widest">Recommended Intelligence</h3>
            <span className="text-xs font-bold text-indigo-600 px-3 py-1 bg-indigo-50 rounded-full ring-1 ring-indigo-100">2 Available</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {agents.map((agent) => (
              <div 
                key={agent.id}
                className="bg-white rounded-[2rem] border border-slate-100 p-8 hover:shadow-2xl hover:shadow-indigo-500/5 hover:-translate-y-1 transition-all duration-300 group relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-8">
                    <span className="px-3 py-1.5 text-[9px] font-bold text-indigo-600 bg-indigo-50 rounded-lg uppercase tracking-widest ring-1 ring-indigo-100">
                      Certified Agent
                    </span>
                </div>
                <div className="flex items-start justify-between mb-6">
                  <div className="p-4 bg-slate-50 rounded-3xl group-hover:bg-indigo-50 transition-colors duration-300 ring-1 ring-slate-100/50">
                    {agent.icon}
                  </div>
                </div>
                
                <h4 className="text-2xl font-bold text-slate-900 mb-3 tracking-tight">{agent.name}</h4>
                <p className="text-slate-500 text-sm mb-8 leading-relaxed font-medium">
                  {agent.description}
                </p>
                
                <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-widest pt-6 border-t border-slate-50">
                  <div className="flex items-center gap-2">
                    <span className="text-indigo-500">{agent.author}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span>{agent.installs} Deployments</span>
                  </div>
                </div>
                
                <div className="flex gap-4 mt-8">
                  <button
                    onClick={() => { setSelectedAgent(agent); setInstallMode(true); }}
                    className="flex-1 py-3.5 px-6 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold uppercase tracking-widest rounded-2xl shadow-lg shadow-indigo-100 transition-all active:scale-[0.98]"
                  >
                    Install Now
                  </button>
                  <button 
                    onClick={() => { setSelectedAgent(agent); setInstallMode(false); }}
                    className="flex-1 py-3.5 px-6 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold uppercase tracking-widest rounded-2xl transition-all"
                  >
                    Specifications
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedAgent && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-gray-50 rounded-lg">
                  {selectedAgent.icon}
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{selectedAgent.name}</h3>
                  <p className="text-sm text-gray-500">{selectedAgent.author}</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedAgent(null)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-6 h-6 text-gray-500" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6">
              {!installMode ? (
                <>
                  {/* Features Section */}
                  <div className="mb-8">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      Key Features
                    </h4>
                    <div className="grid grid-cols-1 gap-3">
                      {selectedAgent.features.map((feature, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 shrink-0" />
                          <span className="text-gray-700 text-sm">{feature}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Setup Instructions Section */}
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Setup Instructions</h4>
                    <div className="space-y-6">
                      {selectedAgent.setupSteps.map((section, idx) => (
                        <div key={idx} className="border border-gray-200 rounded-xl overflow-hidden">
                          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                            <h5 className="font-semibold text-gray-800">{section.title}</h5>
                            {section.description && (
                              <p className="text-sm text-gray-500 mt-1">{section.description}</p>
                            )}
                          </div>
                          <div className="p-4 space-y-6">
                            {section.items.map((item, itemIdx) => (
                              <div key={itemIdx}>
                                <h6 className="font-medium text-gray-900 mb-2">{item.subtitle}</h6>
                                <div className="pl-4 border-l-2 border-gray-100 ml-1">
                                  {item.content.map((content, cIdx) => renderContentItem(content, cIdx))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* Install Form */}
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Install {selectedAgent.name}</h4>
                  <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Upload client secret JSON (credentials.json)</label>
                      <input
                        type="file"
                        accept="application/json"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          setSecretFileObj(f || null);
                          setUploadedSecret(f ? f.name : null);
                        }}
                        className="block w-full text-sm text-gray-700 file:bg-gray-100 file:border file:mr-4 file:py-2 file:px-4 file:rounded-md"
                      />
                      {uploadedSecret && <p className="text-xs text-gray-500 mt-2">Uploaded: {uploadedSecret}</p>}
                    </div>

                    {selectedAgent.id === 'gmail-agent' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Sender email</label>
                          <input
                            type="email"
                            value={senderEmailInput}
                            onChange={(e) => setSenderEmailInput(e.target.value)}
                            placeholder="you@example.com"
                            className="block w-full rounded-md border-gray-200 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">App Password (16 chars)</label>
                          <input
                            type="password"
                            value={appPasswordInput}
                            onChange={(e) => setAppPasswordInput(e.target.value)}
                            placeholder="abcd efgh ijkl mnop"
                            className="block w-full rounded-md border-gray-200 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                          />
                          <p className="text-xs text-yellow-700 mt-2">Lưu ý: App Password là mật khẩu App (16 ký tự) — không phải mật khẩu Gmail gốc.</p>
                        </div>
                      </>
                    )}

                    {selectedAgent.id === 'calendar-agent' && (
                      <p className="text-sm text-gray-600">Chỉ cần upload file client secret JSON theo hướng dẫn ở phần Detail.</p>
                    )}

                    <div className="flex items-center gap-3 pt-2">
                      <button
                        onClick={async () => {
                          if (!secretFileObj) return alert('Please upload client_secret.json');
                          setInstalling(true);
                          setInstallResult(null);
                          const form = new FormData();
                          const profile = selectedAgent.id === 'calendar-agent' ? 'calendar' : 'gmail';
                          const serviceName = selectedAgent.id === 'calendar-agent' ? 'calendar_agent' : 'gmail_agent';
                          const port = selectedAgent.id === 'calendar-agent' ? 10002 : 10003;
                          form.append('profile', profile);
                          form.append('service_name', serviceName);
                          form.append('port', String(port));
                          form.append('file', secretFileObj, secretFileObj.name);
                          if (selectedAgent.id === 'gmail-agent') {
                            if (senderEmailInput) form.append('sender_email', senderEmailInput);
                            if (appPasswordInput) form.append('sender_password', appPasswordInput);
                          }
                          try {
                            const orchestratorOrigin = (window.location.hostname === 'localhost' && window.location.port === '8000')
                              ? 'http://localhost:8001'
                              : '';
                            const apiUrl = orchestratorOrigin + '/install-agent';
                            const res = await fetch(apiUrl, {
                              method: 'POST',
                              body: form,
                            });
                            let json;
                            try {
                              json = await res.json();
                            } catch (e) {
                              const text = await res.text();
                              json = { error: 'non-json response', body: text };
                            }
                            setInstallResult({ ok: res.ok, json });
                            if (!res.ok) alert('Install failed: ' + JSON.stringify(json));
                          } catch (err) {
                            setInstallResult({ ok: false, json: String(err) });
                            alert('Install error: ' + String(err));
                          } finally {
                            setInstalling(false);
                            setInstallMode(false);
                            setSelectedAgent(null);
                            setUploadedSecret(null);
                            setSecretFileObj(null);
                            setSenderEmailInput('');
                            setAppPasswordInput('');
                          }
                        }}
                        disabled={installing}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60"
                      >
                        {installing ? 'Installing...' : 'Submit'}
                      </button>
                      <button
                        onClick={() => setInstallMode(false)}
                        className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </>
              )}
            </div>

            <div className="p-6 border-t border-gray-200 bg-gray-50 rounded-b-xl flex justify-end gap-3">
              <button 
                onClick={() => setSelectedAgent(null)}
                className="px-4 py-2 text-gray-700 font-medium hover:bg-gray-200 rounded-lg transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => setInstallMode(true)}
                className="px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 rounded-lg transition-colors"
              >
                Install Agent
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
