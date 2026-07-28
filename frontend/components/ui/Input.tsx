"use client";

import { cn } from "@/lib/utils";
import { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes, forwardRef } from "react";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-11 w-full rounded-xl border border-ink-800/15 bg-white px-3 text-sm text-ink-900 outline-none transition placeholder:text-ink-700/40 focus:border-campus-500 focus:ring-2 focus:ring-campus-200",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "h-11 w-full rounded-xl border border-ink-800/15 bg-white px-3 text-sm text-ink-900 outline-none transition focus:border-campus-500 focus:ring-2 focus:ring-campus-200",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  ),
);
Select.displayName = "Select";

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "min-h-[96px] w-full rounded-xl border border-ink-800/15 bg-white px-3 py-2 text-sm text-ink-900 outline-none transition focus:border-campus-500 focus:ring-2 focus:ring-campus-200",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export function Label({
  children,
  htmlFor,
  className,
}: {
  children: React.ReactNode;
  htmlFor?: string;
  className?: string;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className={cn("mb-1.5 block text-xs font-semibold uppercase tracking-wide text-ink-700/70", className)}
    >
      {children}
    </label>
  );
}
