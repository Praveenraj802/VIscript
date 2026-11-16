import React from 'react';
import { Shield } from 'lucide-react';

interface LogoProps {
  size?: number;
  withText?: boolean;
  variant?: string;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 28, withText = false, className = '' }) => {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <div
        style={{ width: size, height: size }}
        className="rounded-xl bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center text-white shadow-md flex-shrink-0"
      >
        <Shield size={size * 0.6} />
      </div>
      {withText && (
        <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
          Vi<span className="text-teal-500">Script</span>
        </span>
      )}
    </div>
  );
};

export default Logo;
