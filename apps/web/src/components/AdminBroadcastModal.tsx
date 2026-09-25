"use client";

import React, { useState } from "react";
import { X, Send, Radio, CheckCircle, ShieldCheck } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

interface AdminBroadcastModalProps {
  onClose: () => void;
  onBroadcastSuccess: (summary: string) => void;
}

export default function AdminBroadcastModal({ onClose, onBroadcastSuccess }: AdminBroadcastModalProps) {
  const [title, setTitle] = useState("🔥 VIP Banker Slip Dropped!");
  const [message, setMessage] = useState("AI confidence 85%. SportyBet & Bet9ja codes ready to load below.");
  const [sportybetCode, setSportybetCode] = useState("SB-9941X");
  const [bet9jaCode, setBet9jaCode] = useState("B9-44120");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/admin/broadcast`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          message,
          sportybet_code: sportybetCode,
          bet9ja_code: bet9jaCode,
          channels: ["web", "telegram", "whatsapp"]
        })
      });

      if (res.ok) {
        setSent(true);
        onBroadcastSuccess("Dispatched to 12,500 Telegram Subscribers & Web Push!");
        setTimeout(() => {
          onClose();
        }, 1800);
      }
    } catch {
      // Local demo simulated response
      setSent(true);
      onBroadcastSuccess("Broadcast simulated successfully to Web & Telegram!");
      setTimeout(() => {
        onClose();
      }, 1800);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-[#0b101c] border border-gold-500/40 w-full max-w-lg rounded-2xl overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-gold-950/60 to-gray-900 border-b border-gray-800 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-gold-500/20 text-gold-400">
              <Radio className="w-4 h-4 text-gold-400" />
            </span>
            <div>
              <h3 className="font-extrabold text-sm sm:text-base text-white">Admin Super-Broadcaster</h3>
              <p className="text-[11px] text-gray-400">Blast booking codes simultaneously across Lagos</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleBroadcast} className="p-4 space-y-4 text-xs">
          {sent ? (
            <div className="text-center py-8 space-y-2">
              <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto animate-bounce" />
              <h4 className="text-base font-extrabold text-white">Broadcast Successfully Dispatched!</h4>
              <p className="text-gray-400 text-xs">
                Sent to Telegram VIP Channel, Web PWA subscribers, and WhatsApp community.
              </p>
            </div>
          ) : (
            <>
              <div>
                <label className="font-bold text-gray-300 block mb-1">Broadcast Headline:</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white font-medium focus:border-gold-500 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="font-bold text-gray-300 block mb-1">Message Body:</label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={2}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white font-medium focus:border-gold-500 focus:outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-red-400 block mb-1">SportyBet Booking Code:</label>
                  <input
                    type="text"
                    value={sportybetCode}
                    onChange={(e) => setSportybetCode(e.target.value)}
                    className="w-full bg-gray-900 border border-red-500/40 rounded-lg px-3 py-2 text-white font-mono font-bold uppercase focus:border-red-400 focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="font-bold text-green-400 block mb-1">Bet9ja Booking Code:</label>
                  <input
                    type="text"
                    value={bet9jaCode}
                    onChange={(e) => setBet9jaCode(e.target.value)}
                    className="w-full bg-gray-900 border border-green-500/40 rounded-lg px-3 py-2 text-white font-mono font-bold uppercase focus:border-green-400 focus:outline-none"
                    required
                  />
                </div>
              </div>

              {/* Channels checkboxes */}
              <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-800 space-y-2">
                <span className="font-bold text-gray-400 block text-[11px] uppercase">
                  Target Broadcast Channels:
                </span>
                <div className="grid grid-cols-3 gap-2 text-[11px]">
                  <div className="flex items-center gap-1.5 text-gray-200">
                    <input type="checkbox" defaultChecked className="accent-gold-500" />
                    <span>Telegram VIP (12.5k)</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-gray-200">
                    <input type="checkbox" defaultChecked className="accent-gold-500" />
                    <span>Web PWA Push (4.2k)</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-gray-200">
                    <input type="checkbox" defaultChecked className="accent-gold-500" />
                    <span>WhatsApp Status</span>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-gold-500 to-amber-600 hover:from-gold-400 hover:to-amber-500 text-black font-extrabold py-2.5 rounded-xl shadow-lg flex items-center justify-center gap-2 text-xs"
              >
                <Send className="w-4 h-4 fill-black" />
                <span>{loading ? "Broadcasting..." : "Broadcast Codes Instantly"}</span>
              </button>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
