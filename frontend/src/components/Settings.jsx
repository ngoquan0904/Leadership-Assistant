import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, FileText, ArrowLeft, Upload, Loader2, CheckCircle, AlertCircle, RefreshCw, File } from 'lucide-react';

export default function Settings({ onBack }) {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // 'idle', 'uploading', 'success', 'error'
  const [statusMessage, setStatusMessage] = useState('');
  
  const [files, setFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  const agents = [
    {
      id: 'document_agent',
      name: 'Document Agent',
      icon: <FileText className="w-6 h-6" />,
      description: 'Manage document extraction and vector database search configuration.'
    },
    // Add more agents here as needed
  ];

  useEffect(() => {
    if (selectedAgent?.id === 'document_agent') {
      fetchFiles();
    }
  }, [selectedAgent]);

  const fetchFiles = async () => {
    setLoadingFiles(true);
    try {
      const response = await fetch('http://localhost:5080/list-files');
      if (response.ok) {
        const data = await response.json();
        setFiles(data);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadStatus('idle');
      setStatusMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setUploadStatus('uploading');
    setStatusMessage('Uploading and processing document...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Calling the /upload-file API
      const response = await fetch('http://localhost:5080/upload-file', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status: ${response.status}`);
      }

      const result = await response.json();
      setUploadStatus('success');
      setStatusMessage(`Successfully uploaded and processed: ${result.filename}`);
      setFile(null); // Clear file input
      
      // Refresh list after successful upload
      setTimeout(fetchFiles, 2000); 
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      setStatusMessage(`Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-slate-100 rounded-xl text-slate-500 transition-all hover:text-indigo-600"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
              <SettingsIcon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 tracking-tight">Agent Settings</h2>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">Configure your AI workforce</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {!selectedAgent ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  className="group bg-white p-6 rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all duration-300 cursor-pointer relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                    {React.cloneElement(agent.icon, { className: "w-24 h-24" })}
                  </div>
                  <div className="relative z-10">
                    <div className="p-3 bg-slate-50 text-slate-500 rounded-2xl w-fit group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors duration-300 mb-4">
                      {agent.icon}
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mb-2 group-hover:text-indigo-600 transition-colors">{agent.name}</h3>
                    <p className="text-sm text-slate-500 leading-relaxed font-medium">
                      {agent.description}
                    </p>
                    <div className="mt-4 flex items-center text-xs font-bold text-indigo-500 uppercase tracking-widest gap-2">
                      Open Settings
                      <span className="group-hover:translate-x-1 transition-transform inline-block">→</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-6">
              <button
                onClick={() => setSelectedAgent(null)}
                className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest hover:text-slate-600 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back to all agents
              </button>

              <div className="bg-white rounded-3xl border border-slate-100 shadow-xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300">
                <div className="bg-slate-900 px-8 py-6 flex items-center gap-4">
                  <div className="p-3 bg-white/10 text-white rounded-2xl backdrop-blur-md">
                    {selectedAgent.icon}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white tracking-tight">{selectedAgent.name}</h3>
                    <p className="text-xs font-medium text-slate-400 mt-1">Configuration options for document processing</p>
                  </div>
                </div>

                <div className="p-8 space-y-8">
                  {selectedAgent.id === 'document_agent' && (
                    <div className="space-y-6">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2">Upload New Document</h4>
                        <p className="text-xs text-slate-500 font-medium leading-relaxed">
                          Files uploaded here will be processed, chunked, and stored in the vector database for RAG (Retrieval Augmented Generation).
                        </p>
                      </div>

                      <div className="group relative border-2 border-dashed border-slate-200 rounded-2xl p-8 transition-all hover:border-indigo-400 hover:bg-indigo-50/30">
                        <input
                          type="file"
                          onChange={handleFileChange}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        />
                        <div className="flex flex-col items-center justify-center text-center space-y-3">
                          <div className={`p-4 rounded-2xl transition-colors duration-300 ${file ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-400 group-hover:bg-indigo-100 group-hover:text-indigo-600'}`}>
                            <Upload className="w-8 h-8" />
                          </div>
                          <div>
                            <p className="text-sm font-bold text-slate-700">
                              {file ? file.name : 'Click or drag file to upload'}
                            </p>
                            <p className="text-xs font-semibold text-slate-400 mt-1 uppercase tracking-wider">
                              PDF, DOCX, etc.
                            </p>
                          </div>
                        </div>
                      </div>

                      {file && (
                        <button
                          onClick={handleUpload}
                          disabled={uploading}
                          className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-2xl font-bold text-sm transition-all shadow-lg shadow-indigo-100 flex items-center justify-center gap-2"
                        >
                          {uploading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Upload className="w-4 h-4" />
                          )}
                          {uploading ? 'Processing...' : 'Start Upload & Process'}
                        </button>
                      )}

                      {uploadStatus !== 'idle' && (
                        <div className={`p-4 rounded-2xl border flex gap-3 ${
                          uploadStatus === 'uploading' ? 'bg-blue-50 border-blue-100 text-blue-700' :
                          uploadStatus === 'success' ? 'bg-emerald-50 border-emerald-100 text-emerald-700' :
                          'bg-red-50 border-red-100 text-red-700'
                        }`}>
                          {uploadStatus === 'uploading' && <Loader2 className="w-5 h-5 animate-spin" />}
                          {uploadStatus === 'success' && <CheckCircle className="w-5 h-5" />}
                          {uploadStatus === 'error' && <AlertCircle className="w-5 h-5" />}
                          <p className="text-xs font-bold uppercase tracking-wider mt-0.5">{statusMessage}</p>
                        </div>
                      )}

                      <div className="pt-8 border-t border-slate-100">
                        <div className="flex items-center justify-between mb-4">
                          <div>
                            <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Storage Explorer</h4>
                            <p className="text-xs text-slate-500 font-medium">Existing documents in MinIO</p>
                          </div>
                          <button 
                            onClick={fetchFiles}
                            disabled={loadingFiles}
                            className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
                          >
                            <RefreshCw className={`w-4 h-4 ${loadingFiles ? 'animate-spin' : ''}`} />
                          </button>
                        </div>

                        {loadingFiles ? (
                          <div className="flex items-center justify-center py-10">
                            <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
                          </div>
                        ) : files.length > 0 ? (
                          <div className="bg-slate-50 rounded-2xl border border-slate-100 overflow-hidden">
                            <div className="overflow-x-auto">
                              <table className="w-full text-left text-xs border-collapse">
                                <thead>
                                  <tr className="bg-slate-100/50 border-b border-slate-100">
                                    <th className="px-4 py-3 font-bold text-slate-500 uppercase tracking-wider">File Name</th>
                                    <th className="px-4 py-3 font-bold text-slate-500 uppercase tracking-wider">Size</th>
                                    <th className="px-4 py-3 font-bold text-slate-500 uppercase tracking-wider text-right">Last Modified</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {files.map((f, i) => (
                                    <tr key={i} className="border-b border-slate-100 hover:bg-white transition-colors group">
                                      <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                          <File className="w-3.5 h-3.5 text-indigo-400" />
                                          <span className="font-bold text-slate-700 truncate max-w-[200px]" title={f.name}>
                                            {f.name}
                                          </span>
                                        </div>
                                      </td>
                                      <td className="px-4 py-3 text-slate-500 font-medium">
                                        {(f.size / 1024 / 1024).toFixed(2)} MB
                                      </td>
                                      <td className="px-4 py-3 text-slate-400 font-medium text-right">
                                        {new Date(f.last_modified).toLocaleDateString()}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ) : (
                          <div className="text-center py-10 bg-slate-50 rounded-2xl border border-slate-100 border-dashed">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">No documents found</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Placeholder for other settings sections */}
                  <div className="pt-6 border-t border-slate-100">
                     <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] text-center">Settings Version 1.0.0</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
