"use client";

import React from "react";

export interface CourseMetaState {
  course_name: string;
  course_code: string;
  academic_year: string;
  semester: string;
  department: string;
  scheme: string;
  credits_l: number;
  credits_t: number;
  credits_p: number;
  credits_c: number;
  total_contact_hours: number;
  theory_hours: number;
  lab_hours: number;
  self_study_hours: number;
}

interface CourseMetaFormProps {
  meta: CourseMetaState;
  onChange: (field: keyof CourseMetaState, value: any) => void;
}

export const CourseMetaForm: React.FC<CourseMetaFormProps> = ({ meta, onChange }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      <div className="border-b border-slate-100 pb-4">
        <h3 className="text-base font-bold text-nba-navy">1. Course Metadata & Academic Scheme</h3>
        <p className="text-xs text-slate-500 mt-1">
          Define institutional regulation, course code, credit breakdown (L-T-P-C), and total hours.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Course / Subject Name *
          </label>
          <input
            type="text"
            value={meta.course_name}
            onChange={(e) => onChange("course_name", e.target.value)}
            placeholder="e.g. Advanced Distributed Systems & Cloud Architecture"
            className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-nba-navy focus:border-nba-navy"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Course Code *
          </label>
          <input
            type="text"
            value={meta.course_code}
            onChange={(e) => onChange("course_code", e.target.value)}
            placeholder="e.g. 22CS501"
            className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg font-mono focus:ring-2 focus:ring-nba-navy focus:border-nba-navy"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Department / Branch
          </label>
          <input
            type="text"
            value={meta.department}
            onChange={(e) => onChange("department", e.target.value)}
            placeholder="Computer Science & Engineering"
            className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-nba-navy"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Curriculum Scheme / Regulation
          </label>
          <select
            value={meta.scheme}
            onChange={(e) => onChange("scheme", e.target.value)}
            className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-nba-navy bg-white"
          >
            <option value="NEP 2020 / AICTE Model Curriculum">NEP 2020 / AICTE Model Curriculum</option>
            <option value="Choice Based Credit System (CBCS)">Choice Based Credit System (CBCS)</option>
            <option value="Autonomous Autonomous 2025 Regulations">Autonomous 2025 Regulations</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Academic Year & Semester
          </label>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="text"
              value={meta.academic_year}
              onChange={(e) => onChange("academic_year", e.target.value)}
              placeholder="2025-26"
              className="text-sm px-3 py-2 border border-slate-300 rounded-lg"
            />
            <select
              value={meta.semester}
              onChange={(e) => onChange("semester", e.target.value)}
              className="text-sm px-3 py-2 border border-slate-300 rounded-lg bg-white"
            >
              {["I", "II", "III", "IV", "V", "VI", "VII", "VIII"].map((s) => (
                <option key={s} value={s}>
                  Sem {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Credit & Hours Breakdown */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
        <h4 className="text-xs font-bold text-nba-navy uppercase tracking-wider mb-3">
          Credits (L-T-P-C) & Contact Hours Calculation
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-[11px] font-medium text-slate-600 mb-1">
              Lectures (L) / week
            </label>
            <input
              type="number"
              min="0"
              max="6"
              value={meta.credits_l}
              onChange={(e) => onChange("credits_l", parseInt(e.target.value) || 0)}
              className="w-full text-sm px-3 py-1.5 border border-slate-300 rounded-md bg-white"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-600 mb-1">
              Tutorials (T) / week
            </label>
            <input
              type="number"
              min="0"
              max="4"
              value={meta.credits_t}
              onChange={(e) => onChange("credits_t", parseInt(e.target.value) || 0)}
              className="w-full text-sm px-3 py-1.5 border border-slate-300 rounded-md bg-white"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-600 mb-1">
              Practicals (P) / week
            </label>
            <input
              type="number"
              min="0"
              max="6"
              value={meta.credits_p}
              onChange={(e) => onChange("credits_p", parseInt(e.target.value) || 0)}
              className="w-full text-sm px-3 py-1.5 border border-slate-300 rounded-md bg-white"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-nba-navy mb-1">
              Total Credits (C)
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={meta.credits_c}
              onChange={(e) => onChange("credits_c", parseInt(e.target.value) || 1)}
              className="w-full text-sm px-3 py-1.5 border border-nba-navy rounded-md bg-white font-bold text-nba-navy"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t border-slate-200 text-xs">
          <div>
            <span className="text-slate-500">Total Contact Hours:</span>
            <input
              type="number"
              value={meta.total_contact_hours}
              onChange={(e) => onChange("total_contact_hours", parseInt(e.target.value) || 45)}
              className="mt-1 w-full text-sm px-2 py-1 border border-slate-300 rounded bg-white font-semibold"
            />
          </div>
          <div>
            <span className="text-slate-500">Theory Hours:</span>
            <input
              type="number"
              value={meta.theory_hours}
              onChange={(e) => onChange("theory_hours", parseInt(e.target.value) || 45)}
              className="mt-1 w-full text-sm px-2 py-1 border border-slate-300 rounded bg-white"
            />
          </div>
          <div>
            <span className="text-slate-500">Lab / Hands-on Hours:</span>
            <input
              type="number"
              value={meta.lab_hours}
              onChange={(e) => onChange("lab_hours", parseInt(e.target.value) || 0)}
              className="mt-1 w-full text-sm px-2 py-1 border border-slate-300 rounded bg-white"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
