def generate_double_diamond_svg():
    svg = '''<svg viewBox="0 0 1000 340" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: auto; max-height: 280px; display: block; margin: 0 auto;">
  <defs>
    <!-- Gradients -->
    <linearGradient id="d1Grad" x1="60" y1="170" x2="480" y2="170" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.15" />
      <stop offset="50%" stop-color="#60a5fa" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.1" />
    </linearGradient>
    <linearGradient id="d2Grad" x1="480" y1="170" x2="900" y2="170" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#ef4444" stop-opacity="0.12" />
      <stop offset="50%" stop-color="#f87171" stop-opacity="0.28" />
      <stop offset="100%" stop-color="#ef4444" stop-opacity="0.12" />
    </linearGradient>
    <linearGradient id="lineGrad" x1="60" y1="170" x2="900" y2="170" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#60a5fa" />
      <stop offset="48%" stop-color="#93c5fd" />
      <stop offset="52%" stop-color="#fca5a5" />
      <stop offset="100%" stop-color="#ef4444" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Diamond 1 Background Fill -->
  <polygon points="70,170 270,35 470,170 270,305" fill="url(#d1Grad)" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="4 4" stroke-opacity="0.4" />
  
  <!-- Diamond 2 Background Fill -->
  <polygon points="490,170 690,35 890,170 690,305" fill="url(#d2Grad)" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 4" stroke-opacity="0.4" />

  <!-- Center Horizontal Baseline -->
  <line x1="50" y1="170" x2="910" y2="170" stroke="url(#lineGrad)" stroke-width="2" stroke-opacity="0.5" stroke-dasharray="2 4" />

  <!-- Diamond 1 Solid Edges (Active journey) -->
  <polyline points="70,170 270,35 470,170" stroke="#60a5fa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
  <polyline points="70,170 270,305 470,170" stroke="#60a5fa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />

  <!-- Diamond 2 Solid Edges (Active journey) -->
  <polyline points="490,170 690,35 890,170" stroke="#f87171" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
  <polyline points="490,170 690,305 890,170" stroke="#f87171" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />

  <!-- Diamond Headers / Stages -->
  <g font-family="Inter, -apple-system, sans-serif" font-size="11" font-weight="700" letter-spacing="0.1em" text-anchor="middle">
    <rect x="200" y="8" width="140" height="20" rx="10" fill="#1e293b" stroke="#3b82f6" stroke-width="1" stroke-opacity="0.4" />
    <text x="270" y="22" fill="#93c5fd">1. DISCOVER &amp; DEFINE</text>
    
    <rect x="620" y="8" width="140" height="20" rx="10" fill="#2d1517" stroke="#ef4444" stroke-width="1" stroke-opacity="0.4" />
    <text x="690" y="22" fill="#fca5a5">2. DEVELOP &amp; DELIVER</text>
  </g>

  <!-- Widening / Convergence Markers -->
  <g font-family="Inter, -apple-system, sans-serif" font-size="9" font-weight="600" letter-spacing="0.05em">
    <text x="170" y="160" fill="#64748b" text-anchor="middle">WIDENING ↗</text>
    <text x="370" y="160" fill="#64748b" text-anchor="middle">CONVERGING ↘</text>
    <text x="590" y="160" fill="#64748b" text-anchor="middle">WIDENING ↗</text>
    <text x="790" y="160" fill="#64748b" text-anchor="middle">CONVERGING ↘</text>
  </g>

  <!-- PHASE 1: Sense intent -->
  <g transform="translate(95, 120)">
    <circle cx="0" cy="0" r="14" fill="#1e293b" stroke="#60a5fa" stroke-width="2" />
    <text x="0" y="4" font-family="Inter, sans-serif" font-size="10" font-weight="700" fill="#fff" text-anchor="middle">01</text>
    <text x="0" y="-22" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#f8fafc" text-anchor="middle">Sense intent</text>
    <text x="0" y="28" font-family="Inter, sans-serif" font-size="9.5" fill="#94a3b8" text-anchor="middle">Deconstruct prompt</text>
  </g>

  <!-- PHASE 2: Know context -->
  <g transform="translate(230, 80)">
    <circle cx="0" cy="0" r="14" fill="#1e293b" stroke="#60a5fa" stroke-width="2" />
    <text x="0" y="4" font-family="Inter, sans-serif" font-size="10" font-weight="700" fill="#fff" text-anchor="middle">02</text>
    <text x="0" y="-20" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#f8fafc" text-anchor="middle">Know context</text>
    <text x="0" y="28" font-family="Inter, sans-serif" font-size="9.5" fill="#94a3b8" text-anchor="middle">Hero chaos &amp; distress</text>
  </g>

  <!-- PHASE 3: Know people -->
  <g transform="translate(250, 240)">
    <circle cx="0" cy="0" r="14" fill="#1e293b" stroke="#60a5fa" stroke-width="2" />
    <text x="0" y="4" font-family="Inter, sans-serif" font-size="10" font-weight="700" fill="#fff" text-anchor="middle">03</text>
    <text x="0" y="28" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#f8fafc" text-anchor="middle">Know people</text>
    <text x="0" y="-20" font-family="Inter, sans-serif" font-size="9.5" fill="#94a3b8" text-anchor="middle">Panicked civilians</text>
  </g>

  <!-- PHASE 4: Frame insights (Converge point) -->
  <g transform="translate(480, 170)">
    <circle cx="0" cy="0" r="18" fill="#0f172a" stroke="#a855f7" stroke-width="3" filter="url(#glow)" />
    <text x="0" y="4" font-family="Inter, sans-serif" font-size="11" font-weight="800" fill="#c084fc" text-anchor="middle">04</text>
    <rect x="-65" y="-55" width="130" height="24" rx="12" fill="#1e1b4b" stroke="#a855f7" stroke-width="1.2" />
    <text x="0" y="-39" font-family="Inter, sans-serif" font-size="11" font-weight="800" fill="#e9d5ff" text-anchor="middle">Frame insights</text>
    <text x="0" y="38" font-family="Inter, sans-serif" font-size="9.5" font-weight="600" fill="#c084fc" text-anchor="middle">Panic-first pivot</text>
  </g>

  <!-- PHASE 5: Explore concepts -->
  <g transform="translate(630, 80)">
    <circle cx="0" cy="0" r="14" fill="#2d1517" stroke="#f87171" stroke-width="2" />
    <text x="0" y="4" font-family="Inter, sans-serif" font-size="10" font-weight="700" fill="#fff" text-anchor="middle">05</text>
    <text x="0" y="-20" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#f8fafc" text-anchor="middle">Explore concepts</text>
    <text x="0" y="28" font-family="Inter, sans-serif" font-size="9.5" fill="#94a3b8" text-anchor="middle">1-tap vs category triage</text>
  </g>

  <!-- PHASE 6: Frame solution -->
  <g transform="translate(710, 240)">
    <circle cx="0" cy="0" r="14" fill="#2d1517" stroke="#f87171" stroke-width="2" />
    <text x="0" y="4" font-family="Inter, sans-serif" font-size="10" font-weight="700" fill="#fff" text-anchor="middle">06</text>
    <text x="0" y="28" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#f8fafc" text-anchor="middle">Frame solution</text>
    <text x="0" y="-20" font-family="Inter, sans-serif" font-size="9.5" fill="#94a3b8" text-anchor="middle">Immediate dispatch + updates</text>
  </g>

  <!-- PHASE 7: Realise offer (Final convergent delivery) -->
  <g transform="translate(865, 170)">
    <circle cx="0" cy="0" r="16" fill="#14532d" stroke="#22c55e" stroke-width="2.5" filter="url(#glow)" />
    <text x="0" y="4" font-family="Inter, sans-serif" font-size="11" font-weight="800" fill="#fff" text-anchor="middle">07</text>
    <rect x="-55" y="-52" width="110" height="24" rx="12" fill="#052e16" stroke="#22c55e" stroke-width="1.2" />
    <text x="0" y="-36" font-family="Inter, sans-serif" font-size="11" font-weight="800" fill="#86efac" text-anchor="middle">Realise offer</text>
    <text x="0" y="36" font-family="Inter, sans-serif" font-size="9.5" font-weight="600" fill="#4ade80" text-anchor="middle">Harbor Prototype</text>
  </g>
</svg>'''
    return svg

if __name__ == "__main__":
    with open("double_diamond.svg", "w", encoding="utf-8") as f:
        f.write(generate_double_diamond_svg())
    print("Generated double_diamond.svg")
