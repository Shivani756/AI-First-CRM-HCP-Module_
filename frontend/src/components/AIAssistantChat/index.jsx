import React, { useRef, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendMessage, clearChat } from '../../store/agentSlice';
import { patchForm, setAISuggestedFollowups, setCurrentInteractionId } from '../../store/interactionSlice';
import './AIAssistantChat.css';

const QUICK_PROMPTS = [
  'Log interaction with Dr. Sharma today',
  'Get follow-up suggestions',
  'Analyze sentiment from last notes',
  'Show Dr. Mehta profile',
];

export default function AIAssistantChat() {
  const dispatch = useDispatch();
  const { messages, loading, sessionId, lastExtractedFields, lastInteractionId } = useSelector(
    (s) => s.agent
  );
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Sync extracted fields to the form
  useEffect(() => {
    if (lastExtractedFields && Object.keys(lastExtractedFields).length > 0) {
      dispatch(patchForm(lastExtractedFields));
      if (lastExtractedFields.ai_suggested_followups?.length > 0) {
        dispatch(setAISuggestedFollowups(lastExtractedFields.ai_suggested_followups));
      }
    }
    if (lastInteractionId) {
      dispatch(setCurrentInteractionId(lastInteractionId));
    }
  }, [lastExtractedFields, lastInteractionId, dispatch]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || loading) return;
    dispatch(sendMessage({ message: text, sessionId }));
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickPrompt = (prompt) => {
    dispatch(sendMessage({ message: prompt, sessionId }));
  };

  return (
    <div className="chat-shell">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-bot-icon">✦</div>
          <div>
            <div className="chat-title">AI Assistant</div>
            <div className="chat-subtitle">Log interaction via chat</div>
          </div>
        </div>
        <button
          className="chat-clear-btn"
          onClick={() => dispatch(clearChat())}
          title="Clear conversation"
        >
          ↺
        </button>
      </div>

      {/* Quick prompts */}
      <div className="chat-quick-prompts">
        {QUICK_PROMPTS.map((p) => (
          <button
            key={p}
            className="quick-prompt-chip"
            onClick={() => handleQuickPrompt(p)}
            disabled={loading}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            {msg.role === 'assistant' && (
              <div className="msg-avatar bot">✦</div>
            )}
            <div className={`msg-bubble ${msg.role}`}>{msg.content}</div>
            {msg.role === 'user' && (
              <div className="msg-avatar user">You</div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-msg assistant">
            <div className="msg-avatar bot">✦</div>
            <div className="msg-bubble assistant typing">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="chat-input-area">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe interaction..."
          className="chat-input"
          rows={2}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="chat-send-btn"
        >
          {loading ? '…' : '⬆ Log'}
        </button>
      </div>
    </div>
  );
}
