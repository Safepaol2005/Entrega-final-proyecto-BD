"use client";

import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "ember";

const variants: Record<Variant, string> = {
  primary:
    "bg-campus-600 text-white hover:bg-campus-700 shadow-lift border border-campus-700/30",
  secondary:
    "bg-white text-ink-800 border border-ink-800/15 hover:border-campus-500/40 hover:bg-campus-50",
  ghost: "bg-transparent text-ink-700 hover:bg-ink-800/5",
  danger: "bg-red-600 text-white hover:bg-red-700",
  ember:
    "bg-ember-500 text-ink-950 hover:bg-ember-400 font-semibold shadow-lift",
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: "sm" | "md" | "lg";
};

export const Button = forwardRef<HTMLButtonElement, Props>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const sizes = {
      sm: "h-9 px-3 text-sm",
      md: "h-11 px-4 text-sm",
      lg: "h-12 px-5 text-base",
    };
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition disabled:opacity-50 disabled:pointer-events-none",
          variants[variant],
          sizes[size],
          className,
        )}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";
