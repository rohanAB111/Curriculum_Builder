"use client";

import React, { useState } from "react";
import { Code, Play, CheckCircle, AlertTriangle, Copy, Check } from "lucide-react";

interface LatexEditorPreviewProps {
  texSource: string;
  onChangeSource: (source: string) => void;
  onCompile: () => Promise<void>;
  isCompiling: boolean;
  compilationResult: any | null;
}

export const LatexEditorPreview: React.FC<LatexEditorPreviewProps> = ({
  texSource,
  onChangeSource,
  onCompile,
  isCompiling,
  compilationResult,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(texSource);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[750px]">
      {/* Editor Toolbar */}
      <div className="bg-slate-900 text-white px-4 py-3 flex justify-between items-center border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Code className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-mono font-bold tracking-wide">
            curriculum_nba_aicte.tex (Standard TeX Template)
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1.5 rounded transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied" : "Copy TeX"}</span>
          </button>

          <button
            onClick={onCompile}
            disabled={isCompiling}
            className="flex items-center space-x-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-3 py-1.5 rounded transition-all disabled:opacity-50 shadow-sm"
          >
            <Play className={`w-3.5 h-3.5 ${isCompiling ? "animate-spin" : ""}`} />
            <span>{isCompiling ? "Compiling TeX..." : "Compile to PDF"}</span>
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Code Editor */}
        <div className="flex-1 flex flex-col border-r border-slate-200 bg-slate-950">
          <textarea
            value={texSource}
            onChange={(e) => onChangeSource(e.target.value)}
            spellCheck={false}
            className="flex-1 w-full bg-slate-950 text-emerald-300 font-mono text-xs p-4 focus:outline-none resize-none custom-scrollbar leading-relaxed"
            placeholder="% Paste or edit raw LaTeX source code here..."
          />
        </div>

        {/* Status / Log Panel */}
        <div className="w-96 flex flex-col bg-slate-50 overflow-hidden">
          <div className="p-3 border-b border-slate-200 bg-white font-semibold text-xs text-slate-700">
            Compilation Output & Log Console
          </div>

          <div className="flex-1 p-3 overflow-y-auto font-mono text-[11px] text-slate-700 custom-scrollbar space-y-3">
            {compilationResult ? (
              compilationResult.success ? (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800">
                  <div className="flex items-center space-x-1.5 font-bold mb-1">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    <span>Compilation Succeeded!</span>
                  </div>
                  <p className="text-[10px]">
                    PDF generated and ready for preview. Multi-pass resolved references and table column widths.
                  </p>
                </div>
              ) : (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-800">
                  <div className="flex items-center space-x-1.5 font-bold mb-1">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>pdflatex Error Detected</span>
                  </div>
                  <div className="text-[10px] space-y-1">
                    {(compilationResult.errors || []).map((err: string, idx: number) => (
                      <div key={idx} className="text-rose-700">
                        {err}
                      </div>
                    ))}
                  </div>
                </div>
              )
            ) : (
              <div className="text-slate-400 text-center py-10">
                Click "Compile to PDF" to trigger the LaTeX subprocess worker.
              </div>
            )}

            {compilationResult?.log_output && (
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Recent Compiler Log:
                </span>
                <pre className="p-2 bg-slate-900 text-slate-300 rounded text-[10px] overflow-x-auto">
                  {compilationResult.log_output}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
