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
                  NBA / AICTE Ready
                </span>
              </h1>
              <p className="text-xs text-slate-500">
                Outcome-Based Engineering Syllabus & LaTeX Compiler
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

          {/* User Role Switcher & Model Settings */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-md text-xs">
              <User className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-slate-500">Role:</span>
              <select
                value={userRole}
                onChange={(e) => setUserRole(e.target.value)}
                className="bg-transparent font-semibold text-nba-navy focus:outline-none cursor-pointer"
              >
                <option value="Faculty">Faculty</option>
                <option value="HOD">HOD / Reviewer</option>
                <option value="Admin">Administrator</option>
              </select>
            </div>

            <button
              onClick={onOpenModelConfig}
              className="p-2 text-slate-600 hover:text-nba-navy hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
              title="Configure LLM & Ollama"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
