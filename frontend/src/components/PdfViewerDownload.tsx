"use client";

import React from "react";
import { Download, FileCode, Archive, CheckCircle, ShieldCheck } from "lucide-react";

interface PdfViewerDownloadProps {
  curriculumId: number;
  courseCode: string;
  courseName: string;
  status: string;
  onOpenReviewModal: () => void;
  userRole: string;
}

export const PdfViewerDownload: React.FC<PdfViewerDownloadProps> = ({
  curriculumId,
  courseCode,
  courseName,
  status,
  onOpenReviewModal,
  userRole,
}) => {
  const pdfUrl = `http://localhost:8000/api/v1/curriculum/${curriculumId}/export/pdf`;
  const texUrl = `http://localhost:8000/api/v1/curriculum/${curriculumId}/export/tex`;
  const zipUrl = `http://localhost:8000/api/v1/curriculum/${curriculumId}/export/zip`;

  const getStatusBadge = () => {
    switch (status) {
      case "APPROVED":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "REJECTED":
        return "bg-rose-100 text-rose-800 border-rose-300";
      case "UNDER_REVIEW":
        return "bg-amber-100 text-amber-800 border-amber-300";
      default:
        return "bg-slate-100 text-slate-800 border-slate-300";
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      {/* Top Banner with Action Buttons */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-bold text-nba-navy">
              {courseCode}: {courseName}
            </h3>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-bold border ${getStatusBadge()}`}
            >
              {status}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Complies with AICTE Model Guidelines & National Board of Accreditation (NBA) Format.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* HOD Review Button */}
          {(userRole === "HOD" || userRole === "Admin") && (
            <button
              onClick={onOpenReviewModal}
              className="flex items-center space-x-1.5 text-xs bg-nba-navy hover:bg-slate-800 text-white font-semibold px-3 py-2 rounded-lg transition-colors shadow-sm"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              <span>Review & Approve</span>
            </button>
          )}

          {/* Download PDF */}
          <a
            href={pdfUrl}
            target="_blank"
            rel="noreferrer"
            download
            className="flex items-center space-x-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white font-semibold px-3 py-2 rounded-lg transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </a>

          {/* Download TeX */}
          <a
            href={texUrl}
            target="_blank"
            rel="noreferrer"
            download
            className="flex items-center space-x-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-3 py-2 rounded-lg border border-slate-300 transition-colors"
          >
            <FileCode className="w-3.5 h-3.5 text-slate-500" />
            <span>LaTeX Source</span>
          </a>

          {/* Download ZIP Bundle */}
          <a
            href={zipUrl}
            target="_blank"
            rel="noreferrer"
            download
            className="flex items-center space-x-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-3 py-2 rounded-lg transition-colors shadow-sm"
          >
            <Archive className="w-3.5 h-3.5" />
            <span>Complete ZIP Bundle</span>
          </a>
        </div>
      </div>

      {/* Embedded PDF Preview Frame */}
      <div className="w-full h-[650px] border border-slate-300 rounded-lg overflow-hidden bg-slate-100 flex flex-col">
        <iframe
          src={pdfUrl}
          className="w-full h-full"
          title="Compiled NBA Curriculum PDF"
        />
      </div>
    </div>
  );
};
