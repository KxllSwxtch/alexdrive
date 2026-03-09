import { cn } from "@/lib/utils"

interface LogoProps {
  size?: "sm" | "md" | "lg"
  className?: string
}

const sizeClasses = {
  sm: "text-base",
  md: "text-lg",
  lg: "text-xl",
} as const

export function Logo({ size = "md", className }: LogoProps) {
  return (
    <span className={cn("font-heading tracking-[0.08em]", sizeClasses[size], className)}>
      <span className="font-light text-gold">Alex</span>
      <span className="font-bold text-text-primary">Drive</span>
    </span>
  )
}
