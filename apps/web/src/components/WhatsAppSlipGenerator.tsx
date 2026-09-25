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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-[#0b101c] border border-emerald-500/40 w-full max-w-md rounded-2xl overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-4 bg-emerald-950/60 border-b border-gray-800 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </span>
            <h3 className="font-extrabold text-sm text-white">Shareable Ticket Card</h3>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* The Visual Ticket Card (Styled for Screenshots & WhatsApp Status) */}
        <div className="p-4">
          <div className="bg-gradient-to-b from-[#121b2d] to-[#0c121e] border border-emerald-500/30 rounded-xl p-4 shadow-inner relative overflow-hidden">
            {/* Top Badge */}
            <div className="flex justify-between items-center mb-3 border-b border-gray-800 pb-2">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-[11px] font-black text-white tracking-wider uppercase">
                  LIVELYBORG AI • LAGOS
                </span>
              </div>
              <span className="text-[10px] font-bold text-gold-400 bg-gold-500/20 px-2 py-0.5 rounded">
                Verified Slip
              </span>
            </div>

            {/* Odds & Payout */}
            <div className="text-center my-3">
              <span className="text-xs text-gray-400 uppercase font-bold">Total Accumulated Odds</span>
              <p className="text-3xl font-black text-emerald-400 font-mono tracking-tight">
                {data.total_odds.toFixed(2)}
              </p>
              <p className="text-xs text-gray-300 mt-1">
                ₦{data.recommended_stake_ngn.toLocaleString()} Stake →{" "}
                <b className="text-gold-400 font-mono">₦{data.potential_payout_ngn.toLocaleString()}</b> Return
              </p>
            </div>

            {/* Matches List */}
            <div className="space-y-1.5 my-3 text-xs bg-black/40 p-2.5 rounded-lg border border-gray-800/80">
              {data.legs.map((l, idx) => (
                <div key={idx} className="flex justify-between items-center text-[11px]">
                  <span className="text-gray-300 truncate max-w-[200px]">{l.match_name}</span>
                  <span className="font-bold text-emerald-400 font-mono">{l.market} ({l.odds.toFixed(2)})</span>
                </div>
              ))}
            </div>

            {/* Booking Codes Bar */}
            <div className="grid grid-cols-2 gap-2 text-center text-xs mt-3 pt-2 border-t border-gray-800">
              <div className="bg-red-950/40 border border-red-500/30 p-1.5 rounded">
                <span className="text-[10px] text-red-400 font-bold block">SportyBet Code</span>
                <span className="font-mono font-black text-white text-xs">{data.sportybet_code}</span>
              </div>
              <div className="bg-green-950/40 border border-green-500/30 p-1.5 rounded">
                <span className="text-[10px] text-green-400 font-bold block">Bet9ja Code</span>
                <span className="font-mono font-black text-white text-xs">{data.bet9ja_code}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Viral Share Buttons */}
        <div className="p-4 bg-gray-900 border-t border-gray-800 space-y-2">
          <button
            onClick={handleWhatsAppShare}
            className="w-full bg-[#25D366] hover:bg-[#20ba5a] text-black font-extrabold text-xs py-2.5 rounded-xl flex items-center justify-center gap-2 shadow-md transition-colors"
          >
            <MessageSquare className="w-4 h-4 fill-black" />
            <span>Share to WhatsApp Status & Chats</span>
          </button>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleTwitterShare}
              className="bg-[#1DA1F2] hover:bg-[#1a90d9] text-white font-bold text-xs py-2 rounded-xl flex items-center justify-center gap-1.5 transition-colors"
            >
              <Twitter className="w-3.5 h-3.5 fill-white" />
              <span>Share to X (Twitter)</span>
            </button>

            <button
              onClick={handleCopyText}
              className="bg-gray-800 hover:bg-gray-700 text-white font-bold text-xs py-2 rounded-xl flex items-center justify-center gap-1.5 transition-colors border border-gray-700"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied!" : "Copy Text"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
