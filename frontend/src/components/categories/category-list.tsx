"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Pencil, Plus, Trash2, Shield } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Category } from "@/types/category";

interface Props {
  categories: Category[];
  onEditCategory: (category: Category) => void;
  onDeleteCategory: (category: Category) => void;
  onAddSubcategory: (category: Category) => void;
  onEditSubcategory: (subcategory: { id: string; name: string }) => void;
  onDeleteSubcategory: (subcategory: { id: string; name: string }) => void;
  canEdit?: boolean;
  canDelete?: boolean;
}

export function CategoryList({
  categories,
  onEditCategory,
  onDeleteCategory,
  onAddSubcategory,
  onEditSubcategory,
  onDeleteSubcategory,
  canEdit = false,
  canDelete = false,
}: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    const next = new Set(expanded);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpanded(next);
  };

  return (
    <div className="space-y-1">
      {categories.map((cat) => (
        <div key={cat.id} className="border rounded-lg">
          <div className="flex items-center gap-3 p-3 hover:bg-muted/50">
            <button onClick={() => toggle(cat.id)} className="p-0.5">
              {expanded.has(cat.id) ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
            <span
              className="h-4 w-4 rounded-full shrink-0"
              style={{ backgroundColor: cat.color }}
            />
            <span className="font-medium flex-1">{cat.name}</span>
            {cat.is_system && (
              <Badge variant="outline" className="text-xs gap-1">
                <Shield className="h-3 w-3" />
                Sistema
              </Badge>
            )}
            <span className="text-xs text-muted-foreground">
              {cat.subcategories.length} sottocategorie
            </span>
            {canEdit && (
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => onEditCategory(cat)}>
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => onAddSubcategory(cat)}>
                  <Plus className="h-3.5 w-3.5" />
                </Button>
                {canDelete && !cat.is_system && (
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-red-500" onClick={() => onDeleteCategory(cat)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                )}
              </div>
            )}
          </div>

          {expanded.has(cat.id) && cat.subcategories.length > 0 && (
            <div className="border-t pl-10 divide-y">
              {cat.subcategories.map((sub) => (
                <div key={sub.id} className="flex items-center gap-3 p-2 text-sm">
                  <span className="flex-1">{sub.name}</span>
                  {canEdit && (
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => onEditSubcategory(sub)}>
                        <Pencil className="h-3 w-3" />
                      </Button>
                      {canDelete && (
                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-red-500" onClick={() => onDeleteSubcategory(sub)}>
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
