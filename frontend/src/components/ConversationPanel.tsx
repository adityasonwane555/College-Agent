import React, { useRef, useEffect, useState } from 'react';
import type { ChatMessage } from '../types';
import { BookOpen, User, Bot, ChevronDown, ChevronUp, Trash2 } from 'lucide-react';

interface ConversationPanelProps {
  messages: ChatMessage[];
  onClearSession: () => void;
}

export const ConversationPanel: React.FC<ConversationPanelProps> = ({ messages, onClearSession }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const toggleCitations = (msgId: string) => {
    setExpandedCitations(prev => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  return (
    <div className="glass-panel" style={{
      width: '100%',
      maxWidth: '720px',
      height: '240px',
      borderRadius: '20px',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      margin: '0 auto',
      position: 'relative'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 18px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        background: 'rgba(10, 16, 30, 0.5)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            fontSize: '13px',
            fontWeight: 600,
            color: '#94a3b8',
            letterSpacing: '0.05em',
            textTransform: 'uppercase'
          }}>
            Live Dialogue
          </span>
          <span style={{
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '10px',
            background: 'rgba(56, 189, 248, 0.1)',
            color: '#38bdf8'
          }}>
            {messages.length} messages
          </span>
        </div>

        {messages.length > 0 && (
          <button
            onClick={onClearSession}
            style={{
              background: 'none',
              border: 'none',
              color: '#64748b',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '12px',
              padding: '4px 8px',
              borderRadius: '6px',
              transition: 'color 0.2s'
            }}
            title="Reset Conversation"
          >
            <Trash2 size={13} />
            Clear
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '14px 18px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}
      >
        {messages.length === 0 ? (
          <div style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#475569',
            fontSize: '14px',
            fontStyle: 'italic'
          }}>
            Conversation is empty. Ask Buddy a question or click a suggestion below!
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                width: '100%'
              }}
            >
              {/* Message Bubble */}
              <div style={{
                maxWidth: '85%',
                padding: '10px 14px',
                borderRadius: msg.sender === 'user' ? '16px 16px 2px 16px' : '16px 16px 16px 2px',
                background: msg.sender === 'user'
                  ? 'linear-gradient(135deg, #0369a1 0%, #0284c7 100%)'
                  : 'rgba(30, 41, 59, 0.85)',
                border: msg.sender === 'user'
                  ? '1px solid rgba(56, 189, 248, 0.3)'
                  : '1px solid rgba(255, 255, 255, 0.08)',
                color: '#f8fafc',
                fontSize: '14px',
                lineHeight: 1.5,
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
                whiteSpace: 'pre-line'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  marginBottom: '4px',
                  fontSize: '11px',
                  color: msg.sender === 'user' ? '#bae6fd' : '#38bdf8',
                  fontWeight: 600
                }}>
                  {msg.sender === 'user' ? <User size={12} /> : <Bot size={12} />}
                  <span>{msg.sender === 'user' ? 'You' : 'Buddy'}</span>
                  <span style={{ color: 'rgba(255,255,255,0.4)', fontWeight: 400, marginLeft: 'auto' }}>
                    {msg.timestamp}
                  </span>
                </div>

                <div>{msg.text}</div>

                {/* Citations Section */}
                {msg.citations && msg.citations.length > 0 && (
                  <div style={{ marginTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '8px' }}>
                    <button
                      onClick={() => toggleCitations(msg.id)}
                      style={{
                        background: 'rgba(0, 240, 255, 0.1)',
                        border: '1px solid rgba(0, 240, 255, 0.25)',
                        borderRadius: '6px',
                        padding: '3px 8px',
                        color: '#38bdf8',
                        fontSize: '11px',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontWeight: 600
                      }}
                    >
                      <BookOpen size={12} />
                      {(() => {
                        const isWeb = msg.citations.some(c => c.source && (c.source.startsWith('http://') || c.source.startsWith('https://')));
                        const label = isWeb ? 'Web Source' : 'Institutional Source';
                        return `${msg.citations.length} ${label}${msg.citations.length > 1 ? 's' : ''}`;
                      })()}
                      {expandedCitations[msg.id] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>

                    {expandedCitations[msg.id] && (
                      <div style={{
                        marginTop: '8px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px',
                        fontSize: '12px'
                      }}>
                        {msg.citations.map((cite, idx) => {
                          const isUrl = cite.source && (cite.source.startsWith('http://') || cite.source.startsWith('https://'));
                          return (
                            <div
                              key={idx}
                              style={{
                                padding: '6px 10px',
                                borderRadius: '8px',
                                background: 'rgba(15, 23, 42, 0.75)',
                                borderLeft: '3px solid #00f0ff'
                              }}
                            >
                              <div style={{ color: '#00f0ff', fontWeight: 600, fontSize: '11px' }}>
                                {isUrl ? (
                                  <>
                                    🌐 <a
                                      href={cite.source}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      style={{ color: '#38bdf8', textDecoration: 'underline' }}
                                    >
                                      {cite.section || cite.source}
                                    </a>
                                  </>
                                ) : (
                                  <>
                                    📄 {cite.source} {cite.page ? `• Page ${cite.page}` : ''} {cite.section ? `• ${cite.section}` : ''}
                                  </>
                                )}
                              </div>
                              {cite.snippet && (
                                <div style={{ color: '#94a3b8', fontStyle: 'italic', marginTop: '2px', fontSize: '11px' }}>
                                  "{cite.snippet}"
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
