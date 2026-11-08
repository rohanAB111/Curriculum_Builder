"use client";

import React, { useState } from "react";
import { X, CheckCircle, XCircle, AlertCircle, ShieldCheck } from "lucide-react";

interface ReviewWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitReview: (status: string, comments: string) => Promise<void>;
  courseCode: string;
  courseName: string;
}

export const ReviewWorkflowModal: React.FC<ReviewWorkflowModalProps> = ({
  isOpen,
  onClose,
  onSubmitReview,
  courseCode,
  courseName,
}) => {
  const [selectedStatus, setSelectedStatus] = useState("APPROVED");
  const [comments, setComments] = useState(
    "Approved for Board of Studies consideration. The course outcomes and industry 4.0 modules align with AICTE mandates."
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onSubmitReview(selectedStatus, comments);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-5">
        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-nba-navy" />
            <h3 className="font-bold text-nba-navy text-base">HOD / Reviewer Curriculum Audit</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200">
          <span className="font-semibold text-slate-900">Target Course: </span>
          {courseCode} - {courseName}
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2">
            Accreditation Decision
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: "APPROVED", label: "Approve", icon: CheckCircle, color: "text-emerald-700 border-emerald-300 bg-emerald-50" },
              { id: "CHANGES_REQUESTED", label: "Request Changes", icon: AlertCircle, color: "text-amber-700 border-amber-300 bg-amber-50" },
              { id: "REJECTED", label: "Reject", icon: XCircle, color: "text-rose-700 border-rose-300 bg-rose-50" },
            ].map((opt) => {
              const Icon = opt.icon;
              const isSelected = selectedStatus === opt.id;
              return (
                <button
                  key={opt.id}
                  onClick={() => setSelectedStatus(opt.id)}
                  className={`flex flex-col items-center p-3 rounded-lg border text-xs font-semibold transition-all ${
                    isSelected ? opt.color + " ring-2 ring-nba-navy" : "border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <Icon className="w-5 h-5 mb-1" />
                  <span>{opt.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Review Comments & Rubric Feedback
          </label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            rows={4}
            className="w-full text-xs p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-nba-navy focus:outline-none"
            placeholder="Enter observations on CO-PO correlation, contact hour balance, or textbook currency..."
          />
        </div>

        <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
          <button
            onClick={onClose}
            className="text-xs px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="text-xs px-4 py-2 bg-nba-navy text-white rounded-lg font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? "Recording..." : "Submit Review Audit"}
          </button>
        </div>
      </div>
    </div>
  );
};
