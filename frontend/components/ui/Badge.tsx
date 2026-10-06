import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'outline' | 'dark' | 'success' | 'warning' | 'alert';
  size?: 'sm' | 'md';
  className?: string;
  onClick?: () => void;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'sm',
  className = '',
  onClick
}) => {
  const sizeStyles = {
    sm: 'text-[11px] px-2.5 py-0.5 tracking-wider',
    md: 'text-[12px] px-3.5 py-1 tracking-wider'
  }[size];

  const variantStyles = {
    default: 'bg-[#f4f4f4] text-[#0c0c0c] border border-[#cecece]',
    outline: 'bg-transparent text-[#0c0c0c] border border-[#0c0c0c]',
    dark: 'bg-[#0c0c0c] text-[#ffffff] border border-[#0c0c0c]',
    success: 'bg-[#eaf7ee] text-[#137333] border border-[#b7e1cd]',
    warning: 'bg-[#fef7e0] text-[#b06000] border border-[#fdd663]',
    alert: 'bg-[#fce8e6] text-[#c5221f] border border-[#f5b4af]'
  }[variant];

  return (
    <span
      onClick={onClick}
      className={`inline-flex items-center font-tech uppercase font-medium rounded-full ${sizeStyles} ${variantStyles} ${
        onClick ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''
      } ${className}`}
    >
      {children}
    </span>
  );
};
