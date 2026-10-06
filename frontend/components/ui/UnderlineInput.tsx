import React from 'react';

interface UnderlineInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  endAdornment?: React.ReactNode;
}

export const UnderlineInput = React.forwardRef<HTMLInputElement, UnderlineInputProps>(
  ({ label, error, endAdornment, className = '', ...props }, ref) => {
    return (
      <div className="w-full flex flex-col">
        {label && (
          <label className="text-[12px] uppercase tracking-wider text-[#6d6d6d] mb-1 font-tech">
            {label}
          </label>
        )}
        <div className="relative flex items-center border-b border-[#0c0c0c] focus-within:border-[#000000] focus-within:border-b-2 transition-all">
          <input
            ref={ref}
            className={`w-full bg-transparent py-2.5 px-0 text-[16px] text-[#0c0c0c] placeholder-[#6d6d6d] outline-none rounded-none tracking-tight font-sans ${className}`}
            {...props}
          />
          {endAdornment && <div className="ml-2 flex-shrink-0">{endAdornment}</div>}
        </div>
        {error && <span className="text-[12px] text-red-600 mt-1">{error}</span>}
      </div>
    );
  }
);

UnderlineInput.displayName = 'UnderlineInput';
