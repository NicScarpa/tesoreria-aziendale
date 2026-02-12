import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[8px] text-[13px] font-semibold transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none",
  {
    variants: {
      variant: {
        default: "border border-transparent bg-primary text-primary-foreground hover:bg-[#333333]",
        destructive:
          "border border-transparent bg-destructive text-white hover:opacity-90",
        outline:
          "border border-[#1a1a1a] bg-transparent text-[#1a1a1a] hover:bg-[#f2f2f2]",
        secondary:
          "border border-transparent bg-[#f2f2f2] text-[#1a1a1a] hover:bg-[#e5e4e3]",
        ghost: "border border-transparent bg-transparent text-[#1a1a1a] hover:bg-[#f2f2f2]",
        link: "border border-transparent bg-transparent text-[#6672ff] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-[38px] px-4 text-[14px] leading-[22px] has-[>svg]:px-3",
        xs: "h-6 gap-1 rounded-[8px] px-2 text-[11px] leading-[16px] has-[>svg]:px-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-8 rounded-[8px] gap-1.5 px-3 text-[12px] leading-[18px] has-[>svg]:px-2.5",
        lg: "h-12 rounded-[8px] px-6 text-[16px] leading-[24px] has-[>svg]:px-4",
        icon: "size-[38px]",
        "icon-xs": "size-6 rounded-[8px] [&_svg:not([class*='size-'])]:size-3",
        "icon-sm": "size-8",
        "icon-lg": "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
