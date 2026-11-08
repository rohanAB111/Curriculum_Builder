"use client";

import React from "react";
import { X, Cpu, Key, Sliders, Check } from "lucide-react";

export interface ModelConfigState {
  provider: string; // "ollama" | "openai" | "gemini" | "anthropic" | "groq"
  modelName: string;
  ollamaUrl: string;
  apiKey: string;
  temperature: number;
}

interface ModelConfigDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  config: ModelConfigState;
  onChangeConfig: (newConfig: ModelConfigState) => void;
}

export const ModelConfigDrawer: React.FC<ModelConfigDrawerProps> = ({
  isOpen,
  onClose,
  config,
  onChangeConfig,
}) => {
  if (!isOpen) return null;

  const handleFieldChange = (field: keyof ModelConfigState, value: any) => {
    onChangeConfig({ ...config, [field]: value });
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex justify-end">
      <div className="bg-white w-full max-w-md h-full shadow-2xl border-l border-slate-200 flex flex-col justify-between p-6 overflow-y-auto">
        <div className="space-y-6">
          <div className="flex justify-between items-center border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-2">
              <Cpu className="w-5 h-5 text-nba-navy" />
              <h3 className="font-bold text-nba-navy text-base">Inference & Model Settings</h3>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Provider Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-2">
              Inference Engine Provider
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "ollama", label: "Ollama (Local)", desc: "Private, on-premise execution" },
                { id: "openai", label: "OpenAI", desc: "GPT-4o / o3-mini" },
                { id: "gemini", label: "Google Gemini", desc: "Gemini 2.5 Pro / 1.5 Flash" },
                { id: "anthropic", label: "Anthropic", desc: "Claude 3.5 Sonnet" },
                { id: "groq", label: "Groq", desc: "Ultra-fast Llama 3.3" },
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleFieldChange("provider", p.id)}
                  className={`text-left p-2.5 rounded-lg border text-xs transition-all ${
                    config.provider === p.id
                      ? "border-nba-navy bg-nba-light text-nba-navy font-bold ring-1 ring-nba-navy"
                      : "border-slate-200 text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <div className="font-semibold">{p.label}</div>
                  <div className="text-[10px] text-slate-500 font-normal">{p.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Provider-Specific Configuration */}
          {config.provider === "ollama" ? (
            <div className="space-y-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                  Ollama Base Endpoint URL
                </label>
                <input
                  type="text"
                  value={config.ollamaUrl}
                  onChange={(e) => handleFieldChange("ollamaUrl", e.target.value)}
                  placeholder="http://localhost:11434"
                  className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded font-mono bg-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                  Target Ollama Model Name
                </label>
                <select
                  value={config.modelName || "qwen2.5:32b"}
                  onChange={(e) => handleFieldChange("modelName", e.target.value)}
                  className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded bg-white font-medium"
                >
                  <option value="qwen2.5:32b">qwen2.5:32b (Recommended for structured LaTeX)</option>
                  <option value="deepseek-r1:14b">deepseek-r1:14b (Advanced Reasoning)</option>
                  <option value="llama3.1:8b">llama3.1:8b (Fast Local Prototyping)</option>
                  <option value="mistral-nemo">mistral-nemo:12b</option>
                </select>
              </div>
            </div>
          ) : (
            <div className="space-y-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1 flex items-center gap-1">
                  <Key className="w-3.5 h-3.5 text-slate-400" />
                  API Secret Key
                </label>
                <input
                  type="password"
                  value={config.apiKey}
                  onChange={(e) => handleFieldChange("apiKey", e.target.value)}
                  placeholder="sk-... (Saved securely for current session)"
                  className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded font-mono bg-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                  Model Variant
                </label>
                <input
                  type="text"
                  value={config.modelName}
                  onChange={(e) => handleFieldChange("modelName", e.target.value)}
                  placeholder={
                    config.provider === "openai"
                      ? "gpt-4o"
                      : config.provider === "anthropic"
                      ? "claude-3-5-sonnet-20241022"
                      : "gemini-2.5-pro"
                  }
                  className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded bg-white font-mono"
                />
              </div>
            </div>
          )}

          {/* Temperature Slider */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                <Sliders className="w-3.5 h-3.5" />
                Temperature (Determinism vs Creativity)
              </label>
              <span className="text-xs font-mono font-bold text-nba-navy">
                {config.temperature}
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={config.temperature}
              onChange={(e) => handleFieldChange("temperature", parseFloat(e.target.value))}
              className="w-full accent-nba-navy cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1">
              <span>0.0 (Strict / NBA Deterministic)</span>
              <span>1.0 (Creative Exploratory)</span>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200">
          <button
            onClick={onClose}
            className="w-full flex items-center justify-center space-x-2 bg-nba-navy text-white text-xs font-semibold py-2.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <Check className="w-4 h-4" />
            <span>Save Configuration</span>
          </button>
        </div>
      </div>
    </div>
  );
};
