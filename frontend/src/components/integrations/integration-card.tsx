"use client";

import { type LucideIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { IntegrationConnectionStatus } from "@/types/integration";
import { INTEGRATION_STATUS_LABELS, INTEGRATION_STATUS_COLORS } from "@/types/integration";

interface IntegrationCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  status: IntegrationConnectionStatus;
  onClick?: () => void;
}

export function IntegrationCard({ icon: Icon, title, description, status, onClick }: IntegrationCardProps) {
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
      <CardHeader className="flex flex-row items-center gap-3 pb-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1">
          <CardTitle className="text-base">{title}</CardTitle>
        </div>
        <Badge className={INTEGRATION_STATUS_COLORS[status]}>
          {INTEGRATION_STATUS_LABELS[status]}
        </Badge>
      </CardHeader>
      <CardContent>
        <CardDescription>{description}</CardDescription>
      </CardContent>
    </Card>
  );
}
