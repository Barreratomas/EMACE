import * as React from "react"
import { cn } from "@/lib/utils"

export interface SectionHeaderProps {
  left: React.ReactNode
  right?: React.ReactNode
  className?: string
  rightClassName?: string
}

export function SectionHeader({
  left,
  right,
  className,
  rightClassName,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <div className="min-w-0">{left}</div>
      {right && (
        <div
          className={cn(
            "flex flex-wrap gap-2 w-full justify-start",
            rightClassName
          )}
        >
          {right}
        </div>
      )}
    </div>
  )
}

