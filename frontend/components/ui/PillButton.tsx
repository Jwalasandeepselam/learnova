import React from 'react';

interface PillButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'subtle';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export const PillButton: React.FC<PillButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium tracking-tight transition-all duration-150 select-none cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed';

  // 24px radius = rounded-full
  const sizeStyles = {
    sm: 'text-[13px] px-4 py-1.5 rounded-full gap-1.5',
    md: 'text-[14px] px-7 py-2.5 rounded-full gap-2',
    lg: 'text-[15px] px-8 py-3.5 rounded-full gap-2.5'
  }[size];

  const variantStyles = {
    primary:
      'bg-[#0c0c0c] text-[#ffffff] hover:bg-[#262626] active:bg-[#000000] border border-[#0c0c0c] hover:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#0c0c0c] focus-visible:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#0c0c0c] hover:-translate-y-0.5',
    secondary:
      'bg-transparent text-[#0c0c0c] border border-[#cecece] hover:border-[#0c0c0c] hover:bg-[#f9f9f9] hover:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#0c0c0c] focus-visible:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#0c0c0c] hover:-translate-y-0.5',
    outline:
      'bg-transparent text-[#0c0c0c] border border-[#0c0c0c] hover:bg-[#0c0c0c] hover:text-[#ffffff] hover:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#0c0c0c] focus-visible:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#0c0c0c] hover:-translate-y-0.5',
    subtle:
      'bg-[#f4f4f4] text-[#6d6d6d] hover:text-[#0c0c0c] hover:bg-[#eaeaea] border border-transparent hover:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#6d6d6d] focus-visible:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#6d6d6d]'
  }[variant];

  return (
    <button
      className={`${baseStyles} ${sizeStyles} ${variantStyles} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span>{children}</span>
    </button>
  );
};
