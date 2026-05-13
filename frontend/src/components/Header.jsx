export default function Header() {
  return (
    <header className="header">
      <div className="header-logo">
        <svg viewBox="0 0 32 32" fill="none">
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="32" y2="32">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>
          </defs>
          <circle cx="16" cy="16" r="14" stroke="url(#grad)" strokeWidth="2.5" fill="none" />
          <path d="M10 16 L14 20 L22 12" stroke="url(#grad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </svg>
        <h1>NeuroTrace</h1>
      </div>
      <span className="header-badge">Neural Debugger v0.6.0</span>
    </header>
  );
}
