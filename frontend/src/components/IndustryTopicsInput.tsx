"use client";

import React, { useState } from "react";
import { Sparkles, X, Plus } from "lucide-react";

interface IndustryTopicsInputProps {
  value: string;
  onChange: (value: string) => void;
}

const PRESET_TOPICS = [
  "Edge AI",
  "vLLM",
  "TensorRT-LLM",
  "Kafka Streams",
  "TinyML",
  "LangGraph",
  "Ray Distributed",
  "eBPF Observability",
  "gRPC Microservices",
  "OpenTelemetry",
];

export const IndustryTopicsInput: React.FC<IndustryTopicsInputProps> = ({
  value,
  onChange,
}) => {
  const [customTag, setCustomTag] = useState("");

  const currentTags = value
    ? value
        .split(",")
        .map((t) => t.strip ? t.strip() : t.trim())
        .filter(Boolean)
    : [];

  const handleAddTag = (tag: string) => {
    const clean = tag.trim();
    if (!clean || currentTags.includes(clean)) return;
    const nextTags = [...currentTags, clean];
    onChange(nextTags.join(", "));
  };

  const handleRemoveTag = (tag: string) => {
    const nextTags = currentTags.filter((t) => t !== tag);
    onChange(nextTags.join(", "));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      handleAddTag(customTag);
      setCustomTag("");
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
      <div className="border-b border-slate-100 pb-3">
        <h3 className="text-base font-bold text-nba-navy flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-nba-accent" />
          3. Industry Integration & Novel Trending Topics
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Specify modern engineering tools and frameworks. The RAG generator injects these into advanced modules (Modules 4-6) while preserving rigorous foundational theory in Modules 1-3.
        </p>
      </div>

      {/* Tag pills */}
      <div className="flex flex-wrap gap-2 items-center p-3 bg-slate-50 border border-slate-200 rounded-lg min-h-[50px]">
        {currentTags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-nba-light text-nba-navy border border-blue-200"
          >
            <span>{tag}</span>
            <button
              onClick={() => handleRemoveTag(tag)}
              className="text-slate-400 hover:text-nba-accent"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}

        <input
          type="text"
          value={customTag}
          onChange={(e) => setCustomTag(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type tool / domain and press Enter (e.g. TinyML)..."
          className="text-xs bg-transparent focus:outline-none flex-1 min-w-[180px] py-1"
        />
      </div>

      {/* Suggested Industry Presets */}
      <div>
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2">
          Recommended AICTE / Industry 4.0 Focus:
        </span>
        <div className="flex flex-wrap gap-1.5">
          {PRESET_TOPICS.map((preset) => {
            const isSelected = currentTags.includes(preset);
            return (
              <button
                key={preset}
                disabled={isSelected}
                onClick={() => handleAddTag(preset)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-all flex items-center space-x-1 ${
                  isSelected
                    ? "bg-slate-200 text-slate-400 border-slate-200 cursor-default"
                    : "bg-white text-slate-700 border-slate-300 hover:border-nba-navy hover:text-nba-navy"
                }`}
              >
                {!isSelected && <Plus className="w-3 h-3 text-slate-400" />}
                <span>{preset}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
