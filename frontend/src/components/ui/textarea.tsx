import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex min-h-24 w-full rounded-[8px] border border-[#817f7d] bg-white px-3 py-[7px] text-[14px] font-normal leading-[22px] text-[#1a1a1a] outline-none transition-colors placeholder:text-[#817f7d] focus-visible:border-[#6672ff] disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
