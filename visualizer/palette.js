// Palette parsing + interpolation. Exposed as window.Palette.
(function () {
  function hexToRgb(h) {
    h = String(h || '#000').replace('#', '');
    if (h.length === 3) h = h.split('').map((c) => c + c).join('');
    const n = parseInt(h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function lerpRgb(a, b, k) {
    k = Math.max(0, Math.min(1, k));
    return [
      Math.round(a[0] + (b[0] - a[0]) * k),
      Math.round(a[1] + (b[1] - a[1]) * k),
      Math.round(a[2] + (b[2] - a[2]) * k),
    ];
  }

  function rgba(rgb, a) {
    return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`;
  }

  const DEFAULT = {
    bg: '#0b0d12',
    fg: '#c9d2e3',
    accent: ['#7aa2f7', '#9ece6a', '#e0af68'],
    transition_sec: 12,
  };

  function normalize(p) {
    p = p || {};
    return {
      bg: hexToRgb(p.bg || DEFAULT.bg),
      fg: hexToRgb(p.fg || DEFAULT.fg),
      accent: (p.accent && p.accent.length ? p.accent : DEFAULT.accent).map(hexToRgb),
      transition_sec: typeof p.transition_sec === 'number' ? p.transition_sec : DEFAULT.transition_sec,
    };
  }

  window.Palette = { hexToRgb, lerpRgb, rgba, normalize, DEFAULT };
})();
