import React from 'react';

export interface StatItem {
  id?: string;
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
}

interface StatRailProps {
  stats: StatItem[];
  className?: string;
}

export const StatRail: React.FC<StatRailProps> = ({ stats, className = '' }) => {
  return (
    <div
      className={`border-y border-[#cecece] bg-[#ffffff] divide-y md:divide-y-0 md:divide-x divide-[#cecece] grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 ${className}`}
    >
      {stats.map((stat, idx) => (
        <div
          key={stat.id || idx}
          className="px-6 py-6 flex flex-col justify-between hover:bg-[#fafafa] transition-colors"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
              SPEC // 0{idx + 1}
            </span>
            <span className="text-[12px] tracking-wide uppercase text-[#6d6d6d] font-medium text-right truncate">
              {stat.label}
            </span>
          </div>

          <div className="flex items-baseline gap-1.5 mt-1">
            <span className="text-[44px] md:text-[52px] font-bold tracking-tight text-[#0c0c0c] font-tech leading-none">
              {stat.value}
            </span>
            {stat.unit && (
              <span className="text-[14px] text-[#6d6d6d] font-tech tracking-normal">
                {stat.unit}
              </span>
            )}
          </div>

          {stat.subtext && (
            <p className="mt-2 text-[12px] text-[#6d6d6d] tracking-tight">
              {stat.subtext}
            </p>
          )}
        </div>
      ))}
    </div>
  );
};
