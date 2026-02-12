import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex h-8 w-fit shrink-0 items-center justify-center gap-1 overflow-hidden whitespace-nowrap rounded-[40px] border border-transparent px-3 text-[12px] font-medium leading-[18px] [&>svg]:size-3 [&>svg]:pointer-events-none transition-colors",
  {
    variants: {
      variant: {
        default: "bg-[#e5e4e3] text-[#1a1a1a]",
        secondary: "bg-[#8cd7db] text-[#1a1a1a]",
        destructive: "bg-[#fddcdc] text-[#ea0b0b]",
        outline: "border-[#817f7d] bg-transparent text-[#1a1a1a]",
        ghost: "bg-[#f9f9f9] text-[#817f7d]",
        link: "bg-transparent text-[#6672ff] underline-offset-4 [a&]:hover:underline",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
