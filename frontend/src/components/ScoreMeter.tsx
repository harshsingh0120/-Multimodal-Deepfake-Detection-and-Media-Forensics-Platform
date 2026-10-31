import { bandStyleFor, pct } from "../lib/format";

interface Props {
  score: number;
  size?: number;
  label?: string;
}

/** Radial gauge for a 0–1 score. */
export default function ScoreMeter({ score, size = 148, label = "evidence" }: Props) {
  const style = bandStyleFor(score);
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = c * score;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1e2740" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={style.hex}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
          style={{ transition: "stroke-dasharray 0.9s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-extrabold text-white">{pct(score)}</span>
        <span className="text-[10px] uppercase tracking-wide text-slate-400">{label}</span>
      </div>
    </div>
  );
}
