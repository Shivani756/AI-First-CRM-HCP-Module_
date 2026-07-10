import React from 'react';
import { Provider } from 'react-redux';
import { store } from './store';
import LogInteractionForm from './components/LogInteractionForm';
import AIAssistantChat from './components/AIAssistantChat';
import './App.css';

export default function App() {
  return (
    <Provider store={store}>
      <div className="app-shell">
        {/* Top navigation bar */}
        <header className="topbar">
          <div className="topbar-brand">
            <span className="brand-icon">⚕</span>
            <span className="brand-name">PharmaCRM</span>
          </div>
          <nav className="topbar-nav">
            <a href="#" className="nav-link">Dashboard</a>
            <a href="#" className="nav-link active">HCP Management</a>
            <a href="#" className="nav-link">Reports</a>
          </nav>
          <div className="topbar-user">
            <div className="user-avatar">JD</div>
            <span className="user-name">Jane Doe</span>
          </div>
        </header>

        {/* Page content */}
        <main className="page-content">
          <div className="page-heading">
            <h1 className="page-title">Log HCP Interaction</h1>
            <p className="page-subtitle">
              Record your field interactions using the structured form or the AI chat assistant.
            </p>
          </div>

          <div className="layout-grid">
            <section className="panel form-panel">
              <LogInteractionForm />
            </section>
            <aside className="panel chat-panel">
              <AIAssistantChat />
            </aside>
          </div>
        </main>
      </div>
    </Provider>
  );
}
