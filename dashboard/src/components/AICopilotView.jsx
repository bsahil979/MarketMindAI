import React from 'react';

export default function AICopilotView({
  copilotMessages,
  copilotInput,
  setCopilotInput,
  handleSendCopilotMessage,
}) {
  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '560px', overflow: 'hidden' }}>
      <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {copilotMessages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              justifyContent: msg.sender === 'ai' ? 'flex-start' : 'flex-end',
            }}
          >
            <div
              className="glass-panel"
              style={{
                maxWidth: '75%',
                padding: '12px 18px',
                background: msg.sender === 'ai' ? 'var(--glass-bg)' : 'linear-gradient(135deg, rgba(168,85,247,0.1) 0%, rgba(59,130,246,0.1) 100%)',
                borderColor: msg.sender === 'ai' ? 'var(--glass-border)' : 'rgba(59,130,246,0.2)',
                borderRadius: msg.sender === 'ai' ? '16px 16px 16px 4px' : '16px 16px 4px 16px',
                fontSize: '13.5px',
                lineHeight: '1.5'
              }}
            >
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSendCopilotMessage} style={{ padding: '16px 24px', borderTop: '1px solid var(--glass-border)', display: 'flex', gap: '12px' }}>
        <input
          type="text"
          className="input-field"
          placeholder="Ask about forecast prices, beta risk, or database sentiments..."
          value={copilotInput}
          onChange={(e) => setCopilotInput(e.target.value)}
        />
        <button type="submit" className="btn btn-primary">
          Send
        </button>
      </form>
    </div>
  );
}
