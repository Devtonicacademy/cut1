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

  const handleCopyText = () => {
    navigator.clipboard.writeText(data.whatsapp_share_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleWhatsAppShare = () => {
    const encoded = encodeURIComponent(data.whatsapp_share_text);
    window.open(`https://api.whatsapp.com/send?text=${encoded}`, "_blank");
  };

  const handleTwitterShare = () => {
    const tweet = `🔥 Today's AI Value Slip (${data.total_odds.toFixed(2)} Odds)!\nSportyBet: ${data.sportybet_code} | Bet9ja: ${data.bet9ja_code}\nGenerated on LivelyBorg AI (Lagos) #NaijaBetting #SportyBet`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(tweet)}`, "_blank");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white dark:bg-[#0b101c] border border-slate-200 dark:border-emerald-500/40 w-full max-w-md rounded-2xl overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-4 bg-slate-50 dark:bg-emerald-950/60 border-b border-slate-200 dark:border-gray-800 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </span>
            <h3 className="font-extrabold text-sm text-slate-900 dark:text-white">Shareable Ticket Card</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 dark:text-gray-400 dark:hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* The Visual Ticket Card */}
        <div className="p-4">
          <div className="bg-gradient-to-b from-slate-50 to-slate-100 dark:from-[#121b2d] dark:to-[#0c121e] border border-slate-200 dark:border-emerald-500/30 rounded-xl p-4 shadow-xs relative overflow-hidden">
            {/* Top Badge */}
            <div className="flex justify-between items-center mb-3 border-b border-slate-200 dark:border-gray-800 pb-2">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-[11px] font-black text-slate-900 dark:text-white tracking-wider uppercase">
                  LIVELYBORG AI • LAGOS
                </span>
              </div>
              <span className="text-[10px] font-bold text-amber-800 dark:text-gold-400 bg-amber-100 dark:bg-gold-500/20 px-2 py-0.5 rounded">
                Verified Slip
              </span>
            </div>

            {/* Odds & Payout */}
            <div className="text-center my-3">
              <span className="text-xs text-slate-500 dark:text-gray-400 uppercase font-bold">Total Accumulated Odds</span>
              <p className="text-3xl font-black text-emerald-600 dark:text-emerald-400 font-mono tracking-tight">
                {data.total_odds.toFixed(2)}
              </p>
              <p className="text-xs text-slate-600 dark:text-gray-300 mt-1">
                ₦{data.recommended_stake_ngn.toLocaleString()} Stake →{" "}
                <b className="text-amber-600 dark:text-gold-400 font-mono">₦{data.potential_payout_ngn.toLocaleString()}</b> Return
              </p>
            </div>

            {/* Matches List */}
            <div className="space-y-1.5 my-3 text-xs bg-white dark:bg-black/40 p-2.5 rounded-lg border border-slate-200 dark:border-gray-800/80">
              {data.legs.map((l, idx) => (
                <div key={idx} className="flex justify-between items-center text-[11px]">
                  <span className="text-slate-700 dark:text-gray-300 truncate max-w-[200px]">{l.match_name}</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400 font-mono">{l.market} ({l.odds.toFixed(2)})</span>
                </div>
              ))}
            </div>

            {/* Booking Codes Bar */}
            <div className="grid grid-cols-2 gap-2 text-center text-xs mt-3 pt-2 border-t border-slate-200 dark:border-gray-800">
              <div className="bg-rose-50 dark:bg-red-950/40 border border-rose-200 dark:border-red-500/30 p-1.5 rounded">
                <span className="text-[10px] text-rose-700 dark:text-red-400 font-bold block">SportyBet Code</span>
                <span className="font-mono font-black text-slate-900 dark:text-white text-xs">{data.sportybet_code}</span>
              </div>
              <div className="bg-emerald-50 dark:bg-green-950/40 border border-emerald-200 dark:border-green-500/30 p-1.5 rounded">
                <span className="text-[10px] text-emerald-700 dark:text-green-400 font-bold block">Bet9ja Code</span>
                <span className="font-mono font-black text-slate-900 dark:text-white text-xs">{data.bet9ja_code}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Share Buttons */}
        <div className="p-4 bg-slate-50 dark:bg-gray-950 border-t border-slate-200 dark:border-gray-800/80 space-y-2">
          <button
            onClick={handleWhatsAppShare}
            className="w-full bg-[#25D366] hover:bg-[#20ba5a] text-black font-extrabold text-xs py-2.5 rounded-xl flex items-center justify-center gap-2 shadow-sm transition-colors"
          >
            <MessageSquare className="w-4 h-4 fill-black" />
            <span>Share to WhatsApp Status & Groups</span>
          </button>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleTwitterShare}
              className="bg-slate-900 hover:bg-black dark:bg-gray-900 dark:hover:bg-gray-800 text-white font-bold text-xs py-2 rounded-xl flex items-center justify-center gap-1.5 border border-slate-800 dark:border-gray-700 transition-colors"
            >
              <Twitter className="w-3.5 h-3.5 fill-current" />
              <span>Share to X</span>
            </button>

            <button
              onClick={handleCopyText}
              className="bg-slate-200 hover:bg-slate-300 dark:bg-gray-800 dark:hover:bg-gray-700 text-slate-800 dark:text-gray-200 font-bold text-xs py-2 rounded-xl flex items-center justify-center gap-1.5 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied!" : "Copy Text"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
