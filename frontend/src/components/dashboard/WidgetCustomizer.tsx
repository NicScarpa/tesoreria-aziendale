"use client";

import { useState } from "react";
import { ChevronUp, ChevronDown, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import type { DashboardWidget, WidgetType } from "@/types/dashboard";
import { WIDGET_TYPE_LABELS } from "@/types/dashboard";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  widgets: DashboardWidget[];
  onSave: (widgets: DashboardWidget[]) => void;
  onReset: () => void;
}

export function WidgetCustomizer({ open, onOpenChange, widgets, onSave, onReset }: Props) {
  const [localWidgets, setLocalWidgets] = useState<DashboardWidget[]>([]);

  // Sync when dialog opens
  const handleOpenChange = (nextOpen: boolean) => {
    if (nextOpen) {
      setLocalWidgets([...widgets].sort((a, b) => a.posizione - b.posizione));
    }
    onOpenChange(nextOpen);
  };

  const toggleVisibility = (index: number) => {
    setLocalWidgets((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], visibile: !next[index].visibile };
      return next;
    });
  };

  const moveUp = (index: number) => {
    if (index === 0) return;
    setLocalWidgets((prev) => {
      const next = [...prev];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      return next.map((w, i) => ({ ...w, posizione: i }));
    });
  };

  const moveDown = (index: number) => {
    if (index === localWidgets.length - 1) return;
    setLocalWidgets((prev) => {
      const next = [...prev];
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      return next.map((w, i) => ({ ...w, posizione: i }));
    });
  };

  const handleSave = () => {
    onSave(localWidgets.map((w, i) => ({ ...w, posizione: i })));
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Personalizza Dashboard</DialogTitle>
          <DialogDescription>
            Scegli quali widget mostrare e in che ordine.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-1 max-h-[400px] overflow-y-auto py-2">
          {localWidgets.map((widget, index) => (
            <div
              key={widget.widget_type}
              className="flex items-center justify-between rounded-lg border p-3"
            >
              <div className="flex items-center gap-3">
                <Switch
                  checked={widget.visibile}
                  onCheckedChange={() => toggleVisibility(index)}
                />
                <span className="text-sm font-medium">
                  {WIDGET_TYPE_LABELS[widget.widget_type as WidgetType] || widget.widget_type}
                </span>
              </div>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => moveUp(index)}
                  disabled={index === 0}
                >
                  <ChevronUp className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => moveDown(index)}
                  disabled={index === localWidgets.length - 1}
                >
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        <DialogFooter className="flex justify-between sm:justify-between">
          <Button variant="outline" size="sm" onClick={onReset}>
            <RotateCcw className="mr-2 h-3 w-3" /> Ripristina
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button size="sm" onClick={handleSave}>
              Salva
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
