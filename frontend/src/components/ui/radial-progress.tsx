import { useMemo } from "react";
import { RadialBar, RadialBarChart, PolarAngleAxis, ResponsiveContainer } from "recharts";
import { cn } from "@/lib/cn";

interface Props {
  value: number;
  size?: number;
  label?: string;
  color?: string;
  className?: string;
}

export function RadialProgress({
  value,
  size = 120,
  label,
  color = "var(--color-primary)",
  className,
}: Props) {
  const pct = Math.min(100, Math.max(0, Math.round(value)));
  const data = useMemo(() => [{ name: "v", value: pct, fill: color }], [pct, color]);

  return (
    <div
      className={cn("relative", className)}
      style={{ width: size, height: size }}
      aria-label={label ?? `progress ${pct}%`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          innerRadius="72%"
          outerRadius="100%"
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar dataKey="value" cornerRadius={10} background={{ fill: "var(--color-muted)" }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-semibold tabular-nums">{pct}%</span>
        {label ? <span className="text-xs text-muted-foreground">{label}</span> : null}
      </div>
    </div>
  );
}
