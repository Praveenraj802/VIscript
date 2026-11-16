import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Upload, MessageSquare, Bell, LogOut, ChevronRight, Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useQuery } from '@tanstack/react-query';
import { getCameras } from '../api/client';
import { supabase } from '../supabaseClient';
import { Session } from '@supabase/supabase-js';
import Logo from './Logo';
import ProfileModal from './ProfileModal';
import { useState } from 'react';

interface SidebarProps {
  session: Session | null;
  isOpen?: boolean;
  onClose?: () => void;
}

const Sidebar = ({ session, isOpen, onClose }: SidebarProps) => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const user = session?.user;
  const email = user?.email || 'User';
  const initials = email.substring(0, 2).toUpperCase();
  
  // Fetch cameras for dropdown
  const { data: cameras } = useQuery({
    queryKey: ['cameras'],
    queryFn: async () => {
        try { return await getCameras(); } catch { return []; }
    },
    staleTime: 60000
  });

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/login');
  };

  const navClass = ({ isActive }: { isActive: boolean }) => 
    `flex items-center gap-4 px-4 py-3 mx-2 rounded-xl transition-all duration-300 group relative ${
      isActive 
        ? 'bg-gradient-to-r from-teal-600 to-teal-500 text-white shadow-lg shadow-teal-500/20' 
        : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/40 hover:text-slate-900 dark:hover:text-white'
    }`;

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-slate-900/40 dark:bg-black/60 backdrop-blur-sm z-30 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar Drawer */}
      <div className={`h-screen w-72 bg-white dark:bg-[#0B1120] text-slate-900 dark:text-white flex flex-col fixed left-0 top-0 z-40 border-r border-slate-200/60 dark:border-slate-800/50 transition-transform duration-300 ease-in-out shadow-2xl lg:shadow-xl lg:shadow-slate-200/20 lg:dark:shadow-none ${
        isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}>
        <div className="pt-10 pb-10 px-8 flex items-center justify-between">
          <Logo size={34} withText variant={theme === 'dark' ? 'white' : 'gradient'} className="scale-110 origin-left transition-transform duration-300 hover:scale-[1.12]" />
        </div>

      <div className="px-6 mb-10">
        <div className="bg-slate-50/80 dark:bg-slate-900/40 p-5 rounded-2xl border border-slate-200/50 dark:border-slate-800/50 backdrop-blur-md transition-all duration-300 hover:border-teal-500/30">
          <label className="text-[10px] text-slate-400 dark:text-slate-500 uppercase font-bold tracking-[0.15em] mb-3.5 block flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
            System Interface
          </label>
          <select className="w-full bg-white dark:bg-slate-950 border border-slate-200/60 dark:border-slate-700 rounded-xl p-3 text-sm text-slate-600 dark:text-slate-300 outline-none focus:border-teal-500/50 focus:ring-4 focus:ring-teal-500/5 transition-all appearance-none cursor-pointer">
            <option value="all">Global Monitoring</option>
            {cameras?.map((cam: any) => (
              <option key={cam.id} value={cam.id}>{cam.name}</option>
            ))}
            {!cameras && <option>Connecting...</option>}
          </select>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        <div className="px-4 py-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Menu</p>
        </div>
        
        <NavLink to="/" className={navClass}>
          <LayoutDashboard size={20} className="stroke-[1.5]" />
          <span className="font-medium">Dashboard</span>
          <ChevronRight size={16} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
        </NavLink>
        
        <NavLink to="/upload" className={navClass}>
          <Upload size={20} className="stroke-[1.5]" />
          <span className="font-medium">Upload Video</span>
          <ChevronRight size={16} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
        </NavLink>
        
        <NavLink to="/query" className={navClass}>
          <MessageSquare size={20} className="stroke-[1.5]" />
          <span className="font-medium">AI Assistant</span>
          <ChevronRight size={16} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
        </NavLink>
        
        <NavLink to="/alerts" className={navClass}>
            <div className="flex w-full justify-between items-center">
                <div className="flex items-center gap-3">
                    <Bell size={20} className="stroke-[1.5]" /> 
                    <span className="font-medium">Alerts</span>
                </div>
            </div>
            <ChevronRight size={16} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
        </NavLink>
      </nav>

      <div className="p-6 border-t border-slate-100 dark:border-slate-800/50 bg-slate-50/50 dark:bg-[#0B1120] transition-colors duration-300">
        <div className="flex items-center justify-between mb-5">
            <div 
                onClick={() => setIsProfileModalOpen(true)}
                className="flex items-center gap-3.5 p-2 rounded-xl transition-colors hover:bg-slate-100 dark:hover:bg-slate-800/50 group cursor-pointer flex-1 mr-2"
                title="View Profile & Billing"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-teal-500/20 group-hover:scale-105 transition-transform">
                {initials}
              </div>
              <div className="overflow-hidden">
                <p className="text-sm font-semibold text-slate-800 dark:text-white truncate transition-colors group-hover:text-teal-600 dark:group-hover:text-teal-400">
                  {email.split('@')[0]}
                </p>
                <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate font-medium tracking-wide">{email}</p>
              </div>
            </div>

            <button 
              onClick={toggleTheme}
              className="p-2.5 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/80 hover:border-teal-500/30 dark:hover:border-teal-500/50 transition-all duration-300 text-slate-500 dark:text-slate-400 hover:text-teal-600 dark:hover:text-teal-400 shadow-sm group flex-shrink-0"
              title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
            >
              {theme === 'light' ? <Moon size={18} className="group-hover:-rotate-12 transition-transform" /> : <Sun size={18} className="group-hover:rotate-45 transition-transform" />}
            </button>
        </div>

        <button 
          onClick={handleLogout}
          className="flex items-center justify-center gap-2 text-slate-500 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 border border-slate-200 dark:border-slate-800/80 hover:border-rose-200 dark:hover:border-rose-900/30 hover:bg-rose-50 dark:hover:bg-rose-900/10 px-4 py-2.5 rounded-xl text-xs font-semibold w-full transition-all duration-300"
        >
          <LogOut size={14} /> 
          Terminate Session
        </button>
      </div>
    </div>

    {/* Profile Modal Rendered Outside Sidebar Context */}
    <ProfileModal 
      isOpen={isProfileModalOpen} 
      onClose={() => setIsProfileModalOpen(false)} 
      session={session} 
    />
    </>
  );
};

export default Sidebar;
