import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground",
        success:
          "border-transparent bg-[color:var(--color-success)]/15 text-[color:var(--color-success)]",
        warning:
          "border-transparent bg-[color:var(--color-warning)]/15 text-[color:var(--color-warning)]",
        info: "border-transparent bg-[color:var(--color-info)]/15 text-[color:var(--color-info)]",
        modelscope:
          "border-transparent bg-[color:var(--color-brand-modelscope)]/15 text-[color:var(--color-brand-modelscope)]",
        siliconflow:
          "border-transparent bg-[color:var(--color-brand-siliconflow)]/15 text-[color:var(--color-brand-siliconflow)]",
        deepseek:
          "border-transparent bg-[color:var(--color-brand-deepseek)]/15 text-[color:var(--color-brand-deepseek)]",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
