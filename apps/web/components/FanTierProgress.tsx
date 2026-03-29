"use client";

import { getFanTier, getNextFanTier, pointsToNextTier, FAN_TIERS } from "@/lib/fanTiers";
import { FanAvatar } from "./FanAvatar";

interface FanTierProgressProps {
  totalPoints: number;
  initial?: string;
}

export function FanTierProgress({ totalPoints, initial = "F" }: FanTierProgressProps) {
  const current = getFanTier(totalPoints);
  const next = getNextFanTier(totalPoints);
  const remaining = pointsToNextTier(totalPoints);
  const isMax = !next;

  const progressPct = isMax ? 100 : next
    ? Math.round(((totalPoints - current.minPoints) / (next.minPoints - current.minPoints)) * 100)
    : 100;

  return (
    <div className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-5">
      <div className="flex items-center gap-4 mb-4">
        <FanAvatar totalPoints={totalPoints} initial={initial} size="lg" />
        <div>
          <div className="text-[#f9fafb] font-bold text-lg flex items-center gap-2">
            {current.emoji} {current.name}
          </div>
          <div className="text-sm text-[#9ca3af]">{current.description}</div>
        </div>
      </div>

      {!isMax && next && (
        <>
          <div className="flex justify-between text-xs text-[#9ca3af] mb-1.5">
            <span>{totalPoints} points owned</span>
            <span>{remaining} more to unlock {next.emoji} {next.name}</span>
          </div>
          <div className="w-full h-2 bg-[#2a2a38] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${progressPct}%`, background: `linear-gradient(90deg, ${current.ringColor}, ${next.ringColor})` }}
            />
          </div>
        </>
      )}
      {isMax && (
        <div className="text-center text-sm text-[#f97316] font-bold mt-2">⚡ Maximum tier reached — you are a Melodio Legend</div>
      )}

      {/* All tiers strip */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#2a2a38]">
        {FAN_TIERS.map((t) => (
          <div key={t.id} className="flex flex-col items-center gap-1">
            <span
              className={`text-lg ${totalPoints >= t.minPoints ? "opacity-100" : "opacity-25"}`}
              title={t.name}
            >
              {t.emoji}
            </span>
            <span className={`text-[9px] ${totalPoints >= t.minPoints ? "text-[#9ca3af]" : "text-[#4b5563]"}`}>
              {t.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
