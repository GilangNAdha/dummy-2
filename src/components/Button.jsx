// Button — props + default value

const variantStyles = {
  primary: { backgroundColor: '#0F172A', color: '#fff', border: 'none' },
  outline: { backgroundColor: 'transparent', color: '#334155', border: '1px solid #E2E8F0' },
  danger:  { backgroundColor: 'transparent', color: '#DC2626', border: '1px solid #FECACA' },
  ghost:   { backgroundColor: 'transparent', color: '#64748B', border: 'none' },
};

export default function Button({
  children,
  onClick,
  variant = 'primary',   // default value
  type = 'button',       // default value
  disabled = false,      // default value
  fullWidth = false,     // default value
  className = '',
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80 disabled:opacity-50 ${fullWidth ? 'w-full' : ''} ${className}`}
      style={variantStyles[variant] ?? variantStyles.primary}
    >
      {children}
    </button>
  );
}
