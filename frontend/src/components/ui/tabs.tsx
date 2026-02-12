"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Tabs as TabsPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"

function Tabs({
  className,
  orientation = "horizontal",
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Root>) {
  return (
    <TabsPrimitive.Root
      data-slot="tabs"
      data-orientation={orientation}
      orientation={orientation}
      className={cn(
        "group/tabs flex gap-2 data-[orientation=horizontal]:flex-col",
        className
      )}
      {...props}
    />
  )
}

const tabsListVariants = cva(
  "inline-flex w-fit items-center justify-center text-[#1a1a1a] group/tabs-list group-data-[orientation=vertical]/tabs:h-fit group-data-[orientation=vertical]/tabs:flex-col",
  {
    variants: {
      variant: {
        default: "rounded-[8px] bg-[#e5e4e3] p-0.5 group-data-[orientation=horizontal]/tabs:h-12",
        line: "gap-1 rounded-none bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function TabsList({
  className,
  variant = "default",
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List> &
  VariantProps<typeof tabsListVariants>) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      data-variant={variant}
      className={cn(tabsListVariants({ variant }), className)}
      {...props}
    />
  )
}

function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        "relative inline-flex h-[48px] min-w-[100px] items-center justify-center gap-1.5 rounded-[8px] border border-transparent px-6 text-[13px] font-medium leading-[19.5px] whitespace-nowrap transition-colors group-data-[orientation=vertical]/tabs:w-full group-data-[orientation=vertical]/tabs:justify-start disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        "group-data-[variant=default]/tabs-list:data-[state=active]:bg-[#6672ff] group-data-[variant=default]/tabs-list:data-[state=active]:text-white group-data-[variant=default]/tabs-list:data-[state=active]:shadow-none",
        "group-data-[variant=default]/tabs-list:text-[#1a1a1a] group-data-[variant=default]/tabs-list:hover:bg-[#d7d4d1]",
        "group-data-[variant=line]/tabs-list:h-[40px] group-data-[variant=line]/tabs-list:min-w-0 group-data-[variant=line]/tabs-list:rounded-none group-data-[variant=line]/tabs-list:px-4 group-data-[variant=line]/tabs-list:text-[#817f7d] group-data-[variant=line]/tabs-list:data-[state=active]:bg-transparent group-data-[variant=line]/tabs-list:data-[state=active]:text-[#6672ff]",
        "after:absolute after:bottom-0 after:left-1/2 after:h-[2px] after:w-0 after:-translate-x-1/2 after:bg-[#6672ff] after:transition-all group-data-[variant=line]/tabs-list:data-[state=active]:after:w-full",
        className
      )}
      {...props}
    />
  )
}

function TabsContent({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className={cn("flex-1 outline-none", className)}
      {...props}
    />
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent, tabsListVariants }
