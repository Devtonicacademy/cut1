"use client";

import React, { useState } from "react";
import { AccumulatorResponse } from "@/types";
import { X, Copy, Check, MessageSquare, Twitter, Sparkles } from "lucide-react";

interface WhatsAppSlipGeneratorProps {
  data: AccumulatorResponse | null;
  onClose: () => void;
}

export default function WhatsAppSlipGenerator({ data, onClose }: WhatsAppSlipGeneratorProps) {
  const [copied, setCopied] = useState(false);

  if (!data) return null;

  const chance = `${(data.win_probability * 100).toFixed(1)}%`;

  const handleCopyText = () => {
    try {
      navigator.clipboard.writeText(data.whatsapp_share_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable
    }
  };

  const handleWhatsAppShare = () => {
    window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(data.whatsapp_share_text)}`, "_blank", "noopener,noreferrer");
  };

  const handleTwitterShare = () => {
    const tweet = `My ${data.legs.length}-pick slip from LivelyBorg AI: total odds ${data.total_odds.toFixed(2)}, model's chance all win ${chance}. Predictions, not guarantees. 18+`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(tweet)}`, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white dark:bg-[#0B0F19] border border-slate-200 dark:border-emerald-500/40 w-full max-w-md rounded-2xl overflow-hidden shadow-2xl flex flex-col">
        <div className="p-4 bg-slate-50 dark:bg-emerald-950/60 border-b border-slate-200 dark:border-gray-800 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </span>
            <h3 className="font-extrabold text-sm text-slate-900 dark:text-white">Share this slip</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 dark:text-gray-400 dark:hover:text-white p-1" aria-label="Close">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4">
          <div className="bg-gradient-to-b from-slate-50 to-slate-100 dark:from-[#1E293B] dark:to-[#111827] border border-slate-200 dark:border-emerald-500/30 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3 border-b border-slate-200 dark:border-gray-800 pb-2">
              <span className="text-[11px] font-black text-slate-900 dark:text-white tracking-wider uppercase">LivelyBorg AI</span>
              <span className="text-[10px] font-bold text-slate-500 dark:text-gray-400">{data.legs.length} picks</span>
            </div>
            <div className="grid grid-cols-2 text-center my-3">
              <div>
                <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Total odds</span>
                <p className="text-2xl font-black text-slate-900 dark:text-white font-mono">{data.total_odds.toFixed(2)}</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-bold">Chance all win</span>
                <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono">{chance}</p>
              </div>
            </div>
            <div className="space-y-1.5 text-[11px] bg-white dark:bg-black/40 p-2.5 rounded-lg border border-slate-200 dark:border-gray-800/80">
              {data.legs.map((l, idx) => (
                <div key={idx} className="flex justify-between items-center gap-2">
                  <span className="text-slate-700 dark:text-gray-300 truncate">{l.match_name}</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400 font-mono shrink-0">{l.market} ({l.odds.toFixed(2)})</span>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-slate-400 dark:text-gray-500 mt-2 text-center">Predictions, not guarantees. 18+ only.</p>
          </div>
        </div>

        <div className="p-4 bg-slate-50 dark:bg-gray-950 border-t border-slate-200 dark:border-gray-800/80 space-y-2">
          <button
            onClick={handleWhatsAppShare}
            className="w-full bg-[#25D366] hover:bg-[#20ba5a] text-black font-extrabold text-xs py-2.5 rounded-lg flex items-center justify-center gap-2"
          >
            <MessageSquare className="w-4 h-4 fill-black" />
            <span>Share to WhatsApp</span>
          </button>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleTwitterShare}
              className="bg-slate-900 hover:bg-black dark:bg-gray-900 dark:hover:bg-gray-800 text-white font-bold text-xs py-2 rounded-lg flex items-center justify-center gap-1.5 border border-slate-800 dark:border-gray-700"
            >
              <Twitter className="w-3.5 h-3.5 fill-current" />
              <span>Share to X</span>
            </button>
            <button
              onClick={handleCopyText}
              className="bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 text-slate-800 dark:text-gray-200 font-bold text-xs py-2 rounded-lg flex items-center justify-center gap-1.5"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied!" : "Copy text"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
