import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const location = useLocation()
  const isActive = (path: string) => location.pathname === path

  return (
    <nav
      className="sticky top-0 z-50 flex items-center justify-between px-8 py-4"
      style={{ background: '#E8143A' }}
    >
      {/* Brand */}
      <Link to="/" className="flex items-center gap-1.5">
        <span className="font-display font-black text-xl italic text-white" style={{ letterSpacing: '-0.02em' }}>
          Critic
        </span>
        <span className="font-display font-black text-xl text-white/60" style={{ letterSpacing: '-0.02em' }}>
          AI
        </span>
      </Link>

      {/* Links */}
      <div className="flex items-center gap-1">
        {[
          { to: '/', label: 'Evaluate' },
          { to: '/history', label: 'History' },
        ].map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            className="px-4 py-2 rounded-full text-sm font-medium transition-all duration-200"
            style={{
              background: isActive(to) ? 'rgba(255,255,255,0.2)' : 'transparent',
              color: isActive(to) ? '#FFFFFF' : 'rgba(255,255,255,0.6)',
            }}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
