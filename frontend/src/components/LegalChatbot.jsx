import React, { useState, useRef, useEffect } from 'react'
import { MessageSquare, X, Send, Sparkles, Trash2, Scale, RefreshCw, ChevronRight, BookOpen } from 'lucide-react'

export default function LegalChatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: "Hello Officer! I am your **Legal AI Assistant**.\n\nAsk me anything about **BNS 2023**, **IPC**, **IT Act**, **POCSO**, FIR drafting procedures, or case details.",
      citations: [],
      suggested_questions: [
        "What is the section for murder under BNS 2023?",
        "Is theft bailable under IPC 379?",
        "How to draft an e-FIR for cyber financial fraud?"
      ],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ])

  const chatEndRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) {
      scrollToBottom()
    }
  }, [messages, isOpen, loading])

  const handleSend = async (textToSend) => {
    const query = textToSend || input
    if (!query.trim() || loading) return

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages((prev) => [...prev, userMsg])
    if (!textToSend) setInput('')
    setLoading(true)

    try {
      // Format chat history for backend context
      const historyPayload = messages.map((m) => ({
        sender: m.sender,
        text: m.text
      }))

      const API_URL = window.location.hostname === 'localhost' ? 'http://localhost:5000/api/chat' : '/api/chat'
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query.trim(),
          history: historyPayload
        })
      })

      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`)
      }

      const data = await res.json()

      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: data.reply || "I couldn't retrieve an answer at this moment.",
        citations: data.citations || [],
        suggested_questions: data.suggested_questions || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }

      setMessages((prev) => [...prev, botMsg])
    } catch (err) {
      console.error('LegalChat error:', err)
      const errorMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: "⚠️ **Connection Error**: Could not reach backend server. Please ensure the backend service is running on port 5000.",
        citations: [],
        suggested_questions: ["What is BNS 103?", "Is theft bailable?"],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = () => {
    setMessages([
      {
        id: Date.now(),
        sender: 'bot',
        text: "Chat history cleared. How can I assist you with legal questions or case details?",
        citations: [],
        suggested_questions: [
          "What is the section for murder under BNS 2023?",
          "Is theft bailable under IPC 379?",
          "How to draft an e-FIR for cyber financial fraud?"
        ],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ])
  }

  // Format simple markdown (bolding, linebreaks, bullet points)
  const renderFormattedText = (content) => {
    if (!content) return null
    const lines = content.split('\n')
    return lines.map((line, idx) => {
      // Parse bold tags **text**
      const parts = line.split(/(\*\*.*?\*\*)/g)
      const renderedLine = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx}>{part.slice(2, -2)}</strong>
        }
        return part
      })

      if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
        return (
          <div key={idx} style={{ marginLeft: '12px', marginBottom: '4px', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
            <span style={{ color: 'var(--gold)', fontWeight: 'bold' }}>•</span>
            <span>{renderedLine}</span>
          </div>
        )
      }

      return (
        <React.Fragment key={idx}>
          {renderedLine}
          {idx < lines.length - 1 && <br />}
        </React.Fragment>
      )
    })
  }

  return (
    <div className="legal-chatbot-wrapper">
      {/* Floating Action Button (Fixed Bottom-Right) */}
      <button
        className={`chatbot-fab ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Legal AI Chatbot Assistant"
        aria-label="Toggle Legal Chatbot"
      >
        {isOpen ? (
          <X size={26} className="fab-icon" />
        ) : (
          <div className="fab-inner">
            <Scale size={24} className="fab-icon" />
            <span className="fab-pulse"></span>
          </div>
        )}
      </button>

      {/* Chatbot Popup Window */}
      {isOpen && (
        <div className="chatbot-window">
          {/* Header */}
          <div className="chatbot-header">
            <div className="header-brand">
              <div className="bot-avatar">
                <Scale size={18} color="#0f172a" />
              </div>
              <div>
                <h3 className="header-title">
                  Legal AI Assistant <Sparkles size={14} style={{ color: 'var(--gold)', marginLeft: '4px', verticalAlign: 'middle' }} />
                </h3>
                <div className="header-subtitle">
                  <span className="status-dot"></span> Online · BNS/IPC Legal RAG Engine
                </div>
              </div>
            </div>
            <div className="header-actions">
              <button onClick={clearChat} className="icon-btn-sm" title="Clear Chat History">
                <Trash2 size={16} />
              </button>
              <button onClick={() => setIsOpen(false)} className="icon-btn-sm" title="Close Chatbot">
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Messages Body */}
          <div className="chatbot-body">
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-bubble-row ${msg.sender}`}>
                {msg.sender === 'bot' && (
                  <div className="msg-avatar">
                    <Scale size={14} color="#0f172a" />
                  </div>
                )}
                <div className={`chat-bubble ${msg.sender}`}>
                  <div className="bubble-content">{renderFormattedText(msg.text)}</div>

                  {/* Suggested follow-up questions */}
                  {msg.sender === 'bot' && msg.suggested_questions && msg.suggested_questions.length > 0 && (
                    <div className="suggested-questions">
                      {msg.suggested_questions.map((q, qIdx) => (
                        <button
                          key={qIdx}
                          className="chip-btn"
                          onClick={() => handleSend(q)}
                          disabled={loading}
                        >
                          <ChevronRight size={12} /> {q}
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="bubble-timestamp">{msg.timestamp}</div>
                </div>
              </div>
            ))}

            {/* Loading / Typing Indicator */}
            {loading && (
              <div className="chat-bubble-row bot">
                <div className="msg-avatar">
                  <Scale size={14} color="#0f172a" />
                </div>
                <div className="chat-bubble bot loading-bubble">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="loading-text">Analyzing legal databases & statutes...</span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Footer Input Bar */}
          <div className="chatbot-footer">
            <textarea
              className="chat-input"
              placeholder="Ask a legal question (e.g. BNS sections, FIR rules)..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button
              className="chat-send-btn"
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              title="Send Message"
            >
              {loading ? <RefreshCw size={18} className="spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
