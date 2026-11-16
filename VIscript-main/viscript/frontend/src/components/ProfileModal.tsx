import React from 'react';
import { Session } from '@supabase/supabase-js';
import { X, User } from 'lucide-react';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  session: Session | null;
}

const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose, session }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <User size={18} className="text-teal-500" /> User Profile
          </h3>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
          <div>
            <span className="font-semibold text-slate-400 block text-xs">Email</span>
            {session?.user?.email || 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileModal;
