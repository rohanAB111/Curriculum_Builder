"use client";

import React from "react";
import { Plus, Trash2 } from "lucide-react";

export interface CourseOutcomeItem {
  co_id: string;
  description: string;
  bloom_level: string;
  target_attainment_pct: number;
}

interface CourseOutcomesFormProps {
  outcomes: CourseOutcomeItem[];
  onChange: (outcomes: CourseOutcomeItem[]) => void;
}

const BLOOM_OPTIONS = [
  "L1: Remember",
  "L2: Understand",
  "L3: Apply",
  "L4: Analyze",
  "L5: Evaluate",
  "L6: Create",
];

export const CourseOutcomesForm: React.FC<CourseOutcomesFormProps> = ({
  outcomes,
  onChange,
}) => {
  const handleUpdate = (index: number, field: keyof CourseOutcomeItem, value: any) => {
    const updated = [...outcomes];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const handleAdd = () => {
    if (outcomes.length >= 8) return;
    const nextId = `CO${outcomes.length + 1}`;
    onChange([
      ...outcomes,
      {
        co_id: nextId,
        description: "",
        bloom_level: "L3: Apply",
        target_attainment_pct: 70,
      },
    ]);
  };

  const handleRemove = (index: number) => {
    if (outcomes.length <= 4) return;
    const filtered = outcomes.filter((_, i) => i !== index);
    // Re-index IDs
    const reindexed = filtered.map((item, idx) => ({
      ...item,
      co_id: `CO${idx + 1}`,
    }));
    onChange(reindexed);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-base font-bold text-nba-navy">2. Course Outcomes (COs) & Bloom's Taxonomy</h3>
          <p className="text-xs text-slate-500 mt-1">
            Map specific cognitive action verbs to Revised Bloom's Levels (L1-L6) as required by NBA criterion 3.
          </p>
        </div>
        <button
          onClick={handleAdd}
          disabled={outcomes.length >= 6}
          className="flex items-center space-x-1 text-xs bg-slate-100 hover:bg-slate-200 text-nba-navy font-semibold px-2.5 py-1.5 rounded-lg border border-slate-300 transition-colors disabled:opacity-50"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add CO</span>
        </button>
      </div>

      <div className="space-y-3">
        {outcomes.map((co, index) => (
          <div
            key={co.co_id}
            className="flex items-start space-x-3 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs"
          >
            <span className="font-bold text-nba-navy text-sm w-10 mt-1.5">{co.co_id}</span>
            <div className="flex-1">
              <input
                type="text"
                value={co.description}
                onChange={(e) => handleUpdate(index, "description", e.target.value)}
                placeholder="Course Outcome statement (e.g. Understand foundational consensus protocols...)"
                className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-md bg-white focus:ring-1 focus:ring-nba-navy"
              />
            </div>
            <div className="w-40">
              <select
                value={co.bloom_level}
                onChange={(e) => handleUpdate(index, "bloom_level", e.target.value)}
                className="w-full text-xs px-2 py-1.5 border border-slate-300 rounded-md bg-white font-medium"
              >
                {BLOOM_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-20">
              <input
                type="number"
                min="50"
                max="100"
                value={co.target_attainment_pct}
                onChange={(e) =>
                  handleUpdate(index, "target_attainment_pct", parseFloat(e.target.value) || 70)
                }
                title="Target Attainment %"
                className="w-full text-xs px-2 py-1.5 border border-slate-300 rounded-md bg-white text-center"
              />
            </div>
            <button
              onClick={() => handleRemove(index)}
              disabled={outcomes.length <= 4}
              className="p-1.5 text-slate-400 hover:text-rose-600 disabled:opacity-20"
              title="Delete outcome"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
