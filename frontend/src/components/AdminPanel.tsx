import React, { useState } from 'react';
import { api } from '../services/api';
import { X, Lock, ShieldCheck, Plus, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

interface AdminPanelProps {
  onClose: () => void;
  onDataModified?: () => void;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ onClose, onDataModified }) => {
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('buddyadmin2026');
  const [activeTab, setActiveTab] = useState<'faq' | 'department' | 'event' | 'upload'>('faq');
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // FAQ Form State
  const [faqQ, setFaqQ] = useState('');
  const [faqA, setFaqA] = useState('');
  const [faqCat, setFaqCat] = useState('General');

  // Department Form State
  const [deptName, setDeptName] = useState('');
  const [deptCode, setDeptCode] = useState('');
  const [deptBlock, setDeptBlock] = useState('');
  const [deptFloor, setDeptFloor] = useState('');
  const [deptHod, setDeptHod] = useState('');
  const [deptEmail, setDeptEmail] = useState('');
  const [deptDesc, setDeptDesc] = useState('');

  // Event Form State
  const [eventTitle, setEventTitle] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [eventTime, setEventTime] = useState('');
  const [eventVenue, setEventVenue] = useState('');
  const [eventDesc, setEventDesc] = useState('');
  const [eventOrg, setEventOrg] = useState('');

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const authToken = await api.adminLogin(username, password);
      setToken(authToken);
      setStatusMsg({ type: 'success', text: 'Admin authenticated successfully.' });
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Authentication failed' });
    }
  };

  const handleCreateFaq = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      await api.addFaq({ question: faqQ, answer: faqA, category: faqCat }, token);
      setStatusMsg({ type: 'success', text: 'New FAQ added successfully!' });
      setFaqQ('');
      setFaqA('');
      onDataModified?.();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message });
    }
  };

  const handleCreateDept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      await api.addDepartment({
        name: deptName,
        code: deptCode,
        block: deptBlock,
        floor: deptFloor,
        hod: deptHod,
        contact_email: deptEmail,
        description: deptDesc
      }, token);
      setStatusMsg({ type: 'success', text: `Department ${deptName} saved successfully!` });
      setDeptName('');
      setDeptCode('');
      onDataModified?.();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message });
    }
  };

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      await api.addEvent({
        title: eventTitle,
        date: eventDate,
        time: eventTime,
        venue: eventVenue,
        description: eventDesc,
        organizer: eventOrg
      }, token);
      setStatusMsg({ type: 'success', text: `Event ${eventTitle} scheduled successfully!` });
      setEventTitle('');
      onDataModified?.();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message });
    }
  };

  const handleUploadDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedFile) return;
    setIsUploading(true);
    try {
      const res = await api.uploadDocument(selectedFile, token);
      setStatusMsg({
        type: 'success',
        text: `Uploaded & Indexed ${res.metadata.filename} (${res.chunk_count} passages)!`
      });
      setSelectedFile(null);
      onDataModified?.();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content glass-panel" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '680px' }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          paddingBottom: '14px',
          marginBottom: '16px'
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={20} color="#00f0ff" />
            Buddy College Admin Console
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Status Message */}
        {statusMsg && (
          <div style={{
            padding: '10px 14px',
            borderRadius: '10px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            background: statusMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            color: statusMsg.type === 'success' ? '#34d399' : '#f87171',
            border: `1px solid ${statusMsg.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
          }}>
            {statusMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            {statusMsg.text}
          </div>
        )}

        {!token ? (
          /* Login Form */
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>
              Authentication required to modify official college records and upload documents.
            </div>

            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Administrator Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#f8fafc',
                  marginTop: '4px'
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Administrator Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#f8fafc',
                  marginTop: '4px'
                }}
              />
            </div>

            <button type="submit" className="btn-primary" style={{ marginTop: '10px' }}>
              <Lock size={16} />
              Login to Admin Console
            </button>
          </form>
        ) : (
          /* Admin Navigation & Content */
          <div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '10px' }}>
              <button
                onClick={() => setActiveTab('faq')}
                className={activeTab === 'faq' ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                + Add FAQ
              </button>
              <button
                onClick={() => setActiveTab('department')}
                className={activeTab === 'department' ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                + Add Department
              </button>
              <button
                onClick={() => setActiveTab('event')}
                className={activeTab === 'event' ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                + Add Event
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={activeTab === 'upload' ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                Upload Document
              </button>
            </div>

            {/* TAB: Add FAQ */}
            {activeTab === 'faq' && (
              <form onSubmit={handleCreateFaq} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8' }}>Question</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. How to apply for hostel accommodation?"
                    value={faqQ}
                    onChange={(e) => setFaqQ(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8' }}>Official Answer</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Detailed response..."
                    value={faqA}
                    onChange={(e) => setFaqA(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8' }}>Category</label>
                  <input
                    type="text"
                    value={faqCat}
                    onChange={(e) => setFaqCat(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                  />
                </div>
                <button type="submit" className="btn-primary" style={{ alignSelf: 'flex-start', marginTop: '6px' }}>
                  <Plus size={16} /> Save FAQ
                </button>
              </form>
            )}

            {/* TAB: Add Department */}
            {activeTab === 'department' && (
              <form onSubmit={handleCreateDept} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8' }}>Department Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Artificial Intelligence & DS"
                      value={deptName}
                      onChange={(e) => setDeptName(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8' }}>Dept Code</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. AI-DS"
                      value={deptCode}
                      onChange={(e) => setDeptCode(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8' }}>Building / Block</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Tech Block 2"
                      value={deptBlock}
                      onChange={(e) => setDeptBlock(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8' }}>Floor</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 3rd Floor"
                      value={deptFloor}
                      onChange={(e) => setDeptFloor(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8' }}>Head of Department (HOD)</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Dr. Ramesh Kumar"
                      value={deptHod}
                      onChange={(e) => setDeptHod(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8' }}>Email</label>
                    <input
                      type="email"
                      required
                      placeholder="hod.aids@college.edu"
                      value={deptEmail}
                      onChange={(e) => setDeptEmail(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8' }}>Description</label>
                  <textarea
                    rows={2}
                    value={deptDesc}
                    onChange={(e) => setDeptDesc(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                  />
                </div>

                <button type="submit" className="btn-primary" style={{ alignSelf: 'flex-start', marginTop: '6px' }}>
                  <Plus size={16} /> Save Department
                </button>
              </form>
            )}

            {/* TAB: Add Event */}
            {activeTab === 'event' && (
              <form onSubmit={handleCreateEvent} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8' }}>Event Title</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Robotics Exhibition 2026"
                    value={eventTitle}
                    onChange={(e) => setEventTitle(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8' }}>Date</label>
                    <input
                      type="date"
                      required
                      value={eventDate}
                      onChange={(e) => setEventDate(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8' }}>Time</label>
                    <input
                      type="text"
                      placeholder="e.g. 10:00 AM - 4:00 PM"
                      value={eventTime}
                      onChange={(e) => setEventTime(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8' }}>Venue</label>
                  <input
                    type="text"
                    placeholder="e.g. Auditorium-1"
                    value={eventVenue}
                    onChange={(e) => setEventVenue(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8' }}>Organizer</label>
                  <input
                    type="text"
                    placeholder="e.g. Student Council & T&P Cell"
                    value={eventOrg}
                    onChange={(e) => setEventOrg(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8' }}>Description</label>
                  <textarea
                    rows={2}
                    value={eventDesc}
                    onChange={(e) => setEventDesc(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
                  />
                </div>
                <button type="submit" className="btn-primary" style={{ alignSelf: 'flex-start', marginTop: '6px' }}>
                  <Plus size={16} /> Schedule Event
                </button>
              </form>
            )}

            {/* TAB: Upload Document */}
            {activeTab === 'upload' && (
              <form onSubmit={handleUploadDoc} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                  Upload college PDF or TXT documents (prospectus, syllabi, handbooks). Buddy chunks and indexes documents with exact page numbers for factual grounded answers.
                </div>

                <div style={{
                  border: '2px dashed rgba(56, 189, 248, 0.3)',
                  borderRadius: '12px',
                  padding: '24px',
                  textAlign: 'center',
                  background: 'rgba(15, 23, 42, 0.4)'
                }}>
                  <FileText size={36} color="#00f0ff" style={{ margin: '0 auto 8px auto', display: 'block' }} />
                  <input
                    type="file"
                    accept=".pdf,.txt"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    style={{ display: 'block', margin: '0 auto', fontSize: '13px', color: '#cbd5e1' }}
                  />
                  {selectedFile && (
                    <div style={{ marginTop: '8px', fontSize: '12px', color: '#38bdf8' }}>
                      Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={!selectedFile || isUploading}
                  className="btn-primary"
                  style={{ alignSelf: 'flex-start' }}
                >
                  {isUploading ? 'Ingesting & Chunking...' : 'Upload & Index into Buddy Knowledge Base'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
