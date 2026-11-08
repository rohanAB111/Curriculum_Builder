"use client";

import React from "react";

export interface ArticulationCellItem {
  co_id: string;
  target_id: string;
  correlation_level: number; // 0, 1, 2, 3
  rationale?: string;
}

interface ArticulationMatrixViewProps {
  cos: string[];
  matrix: ArticulationCellItem[];
  onChangeCell?: (coId: string, targetId: string, level: number) => void;
  readOnly?: boolean;
}

const PO_LIST = ["PO1", "PO2", "PO3", "PO4", "PO5", "PO6", "PO7", "PO8", "PO9", "PO10", "PO11", "PO12"];
const PSO_LIST = ["PSO1", "PSO2", "PSO3"];
const ALL_TARGETS = [...PO_LIST, ...PSO_LIST];

export const ArticulationMatrixView: React.FC<ArticulationMatrixViewProps> = ({
  cos,
  matrix,
  onChangeCell,
  readOnly = false,
}) => {
  const getCell = (coId: string, targetId: string): number => {
    const item = matrix.find((m) => m.co_id === coId && m.target_id === targetId);
    return item ? item.correlation_level : 0;
  };

  const getAverage = (targetId: string): string => {
    const vals = cos
      .map((co) => getCell(co, targetId))
      .filter((v) => v > 0);
    if (!vals.length) return "-";
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
    return avg.toFixed(1);
  };

  const handleCellClick = (coId: string, targetId: string) => {
    if (readOnly || !onChangeCell) return;
    const current = getCell(coId, targetId);
    const nextLevel = (current + 1) % 4; // Cycles: 0 -> 1 -> 2 -> 3 -> 0
    onChangeCell(coId, targetId, nextLevel);
  };

  const getColorClass = (level: number) => {
    switch (level) {
      case 3:
        return "bg-blue-600 text-white font-bold";
      case 2:
        return "bg-blue-100 text-blue-900 font-semibold";
      case 1:
        return "bg-slate-100 text-slate-800";
      default:
        return "bg-transparent text-slate-300";
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4 overflow-x-auto">
      <div className="border-b border-slate-100 pb-3 flex justify-between items-center">
        <div>
          <h3 className="text-base font-bold text-nba-navy">
            CO-PO & CO-PSO Articulation Matrix (Course Articulation)
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Correlation levels: <span className="font-semibold text-blue-800">3: Substantial (High)</span>,{" "}
            <span className="font-semibold text-blue-600">2: Moderate (Medium)</span>,{" "}
            <span className="font-semibold text-slate-600">1: Slight (Low)</span>,{" "}
            <span className="text-slate-400">-: No correlation</span>.
          </p>
        </div>
        {!readOnly && (
          <span className="text-[11px] bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md border border-slate-200">
            Click any cell to toggle weight (0→1→2→3)
          </span>
        )}
      </div>

      <div className="min-w-[700px]">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-slate-100 text-slate-700">
              <th className="border border-slate-300 p-2 text-left font-bold w-16">CO ID</th>
              {PO_LIST.map((po) => (
                <th key={po} className="border border-slate-300 p-1.5 text-center font-bold">
                  {po}
                </th>
              ))}
              {PSO_LIST.map((pso) => (
                <th
                  key={pso}
                  className="border border-slate-300 p-1.5 text-center font-bold bg-amber-50 text-amber-900"
                >
                  {pso}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cos.map((coId) => (
              <tr key={coId} className="hover:bg-slate-50 transition-colors">
                <td className="border border-slate-300 p-2 font-bold text-nba-navy text-center">
                  {coId}
                </td>
                {ALL_TARGETS.map((targetId) => {
                  const level = getCell(coId, targetId);
                  return (
                    <td
                      key={targetId}
                      onClick={() => handleCellClick(coId, targetId)}
                      className={`border border-slate-300 p-1.5 text-center transition-all ${
                        !readOnly ? "cursor-pointer hover:opacity-80" : ""
                      } ${getColorClass(level)}`}
                    >
                      {level > 0 ? level : "-"}
                    </td>
                  );
                })}
              </tr>
            ))}
            {/* Averages Row */}
            <tr className="bg-slate-100 font-bold border-t-2 border-slate-400">
              <td className="border border-slate-300 p-2 text-center text-nba-navy">Average</td>
              {ALL_TARGETS.map((targetId) => (
                <td key={targetId} className="border border-slate-300 p-1.5 text-center text-nba-navy">
                  {getAverage(targetId)}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
