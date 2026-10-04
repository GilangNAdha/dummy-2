// Card — komponen reusable dengan props + default value

export default function Card({
  children,
  className = '',
  padding = 'p-6',
  onClick = null,
}) {
  return (
    <div
      className={`bg-white rounded-2xl ${padding} ${className} ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
      style={{ boxShadow: 'rgba(0,0,0,0.06) 0px 4px 20px -4px' }}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
