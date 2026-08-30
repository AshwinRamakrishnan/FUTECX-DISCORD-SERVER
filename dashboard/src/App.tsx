import React, { useState, useEffect } from 'react';
import { Users, CheckSquare, Award, FolderGit2, Shield, Activity } from 'lucide-react';

function App() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [selectedUser, setSelectedUser] = useState<any>(null);

  const inspectUser = (futecx_id: string) => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/users/${futecx_id}`)
      .then(res => res.json())
      .then(data => setSelectedUser(data))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/leaderboard`)
      .then(res => res.json())
      .then(data => {
        if(data.leaderboard) setLeaderboard(data.leaderboard);
      })
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="min-h-screen bg-background text-text p-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            FUTECX Admin
          </h1>
          <p className="text-gray-400 mt-2">Platform Overview & Management</p>
        </div>
        <div className="flex gap-4">
          <button className="px-4 py-2 glass-panel hover:bg-surface/90 transition-colors">Settings</button>
          <button className="px-4 py-2 bg-primary text-white rounded-xl hover:bg-blue-600 transition-colors">Export Report</button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[
          { label: "Active Members", value: "0", icon: <Users size={24} className="text-blue-400"/> },
          { label: "Tasks Completed", value: "0", icon: <CheckSquare size={24} className="text-green-400"/> },
          { label: "Projects Active", value: "0", icon: <FolderGit2 size={24} className="text-purple-400"/> },
          { label: "Certificates Issued", value: "0", icon: <Award size={24} className="text-yellow-400"/> }
        ].map((stat, i) => (
          <div key={i} className="glass-panel p-6 flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 font-medium">{stat.label}</span>
              {stat.icon}
            </div>
            <span className="text-3xl font-bold">{stat.value}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 glass-panel p-6 min-h-[400px]">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Activity size={20} className="text-primary"/> Activity Feed
          </h2>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No recent activity
          </div>
        </div>
        
        <div className="glass-panel p-6 min-h-[400px]">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Shield size={20} className="text-primary"/> Leaderboard
          </h2>
          <div className="flex flex-col gap-4">
            {leaderboard.length > 0 ? leaderboard.map((user: any) => (
              <div key={user.rank} className="flex justify-between items-center p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10" onClick={() => inspectUser(user.futecx_id)}>
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 font-mono">#{user.rank}</span>
                  <span className="font-medium">{user.username}</span>
                </div>
                <div className="text-right">
                  <div className="text-primary font-bold">{user.xp} XP</div>
                  <div className="text-xs text-gray-400">Level {user.level}</div>
                </div>
              </div>
            )) : (
              <div className="text-gray-500 text-center py-8">No leaderboard data</div>
            )}
          </div>
        </div>
      </div>
      {selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedUser(null)}>
          <div className="bg-surface border border-white/10 p-8 rounded-xl max-w-md w-full shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">FUTECX OFFICIAL ID</h3>
              <button onClick={() => setSelectedUser(null)} className="text-gray-500 hover:text-white">✕</button>
            </div>
            
            <div className="space-y-4 font-mono">
              <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                <div className="text-xs text-gray-500 mb-1">MEMBER NAME</div>
                <div className="text-lg font-bold">{selectedUser.username}</div>
              </div>
              
              <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                <div className="text-xs text-gray-500 mb-1">FUTECX ID</div>
                <div className="text-lg font-bold text-primary">{selectedUser.futecx_id}</div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                  <div className="text-xs text-gray-500 mb-1">STATUS</div>
                  <div className="text-green-400 font-bold">✅ {selectedUser.verification_status}</div>
                </div>
                <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                  <div className="text-xs text-gray-500 mb-1">ROLE</div>
                  <div className="font-bold text-gray-300">{selectedUser.official_role}</div>
                </div>
                <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                  <div className="text-xs text-gray-500 mb-1">LEVEL</div>
                  <div className="font-bold">{selectedUser.level}</div>
                </div>
                <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                  <div className="text-xs text-gray-500 mb-1">XP</div>
                  <div className="font-bold text-primary">{selectedUser.xp}</div>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-white/10 text-center flex flex-col items-center">
                <div className="text-xs text-gray-500 mb-4">QR VERIFICATION LINK</div>
                <div className="w-32 h-32 bg-white flex items-center justify-center p-2 rounded">
                   {/* In a real app we'd use a QR component here. We just show the raw link for the mockup */}
                   <span className="text-black text-[10px] break-all">{selectedUser.qr_verification_url}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App;
