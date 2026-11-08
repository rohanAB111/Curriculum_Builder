"use client";

import React from "react";
import { BookOpen, ShieldCheck, Cpu, FileText, Settings, User } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  userRole: string;
  setUserRole: (role: string) => void;
  onOpenModelConfig: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  userRole,
  setUserRole,
  onOpenModelConfig,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      {/* Official SAKEC Institutional Top Header Banner */}
      <div className="bg-gradient-to-r from-[#0f2547] via-[#163669] to-[#1e4682] text-white py-2.5 px-4 sm:px-6 lg:px-8 border-b-2 border-amber-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-amber-300 font-bold">
              Mahavir Education Trust&apos;s
            </div>
            <div className="text-lg font-extrabold tracking-tight text-white">
              SHAH &amp; ANCHOR KUTCHHI ENGINEERING COLLEGE (SAKEC)
            </div>
            <div className="text-[11px] text-sky-100">
              An Autonomous Institute Affiliated to University of Mumbai &bull; NAAC &apos;A&apos; Grade (3.16 CGPA) &bull; NBA Accredited (Comp, IT, EXTC) &bull; DTE Code: 3148
            </div>
            <div className="text-[11px] text-slate-200">
              Mahavir Education Trust&apos;s Chowk, W. T. Patil Marg, Chembur, Mumbai – 400 088 &bull; Tel: 022-25580854 &bull;{" "}
              <a href="https://www.sakec.ac.in/" target="_blank" rel="noreferrer" className="text-amber-300 underline font-semibold">
                www.sakec.ac.in
              </a>
            </div>
          </div>
          <div className="bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-right">
            <div className="text-[11px] text-amber-200 font-semibold">Principal: Dr. Bhavesh Patel</div>
            <div className="text-xs font-extrabold text-yellow-200">
              👨‍💻 Developed by Dr. Rohan Borgalli
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center space-x-3">
            <div className="bg-nba-navy text-white p-2 rounded-lg shadow-sm">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-nba-navy tracking-tight flex items-center gap-2">
                CurriculumAI Studio
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                  SAKEC OBE V3.0 Ready
                </span>
              </h1>
              <p className="text-xs text-slate-500">
                NBA / AICTE Curriculum, Multi-Domain COs &amp; MS Teams Rubric Exporter
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 bg-slate-100 p-1 rounded-lg">
            {[
              { id: "wizard", label: "Curriculum Wizard", icon: FileText },
              { id: "rag", label: "Context RAG Store", icon: Cpu },
              { id: "editor", label: "Live LaTeX Editor", icon: BookOpen },
              { id: "export", label: "Export & Review", icon: ShieldCheck },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                    isActive
                      ? "bg-white text-nba-navy shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Hierarchical User Role Switcher (Faculty, HOD, Principal, Admin) */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-md text-xs">
              <User className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-slate-500">Role:</span>
              <select
                value={userRole}
                onChange={(e) => setUserRole(e.target.value)}
                className="bg-transparent font-semibold text-nba-navy focus:outline-none cursor-pointer"
              >
                <option value="Faculty">Faculty (Dr. Rohan Borgalli)</option>
                <option value="HOD">HOD (Inherits All Faculty + BoS)</option>
                <option value="Principal">Principal (Dr. Bhavesh Patel - All Access)</option>
                <option value="Admin">Administrator (Full System Access)</option>
              </select>
            </div>

            <button
              onClick={onOpenModelConfig}
              className="p-2 text-slate-600 hover:text-nba-navy hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
              title="Configure LLM & PARAM Shavak Qwen"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
