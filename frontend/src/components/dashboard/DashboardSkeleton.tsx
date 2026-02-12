import { Card, CardContent, CardHeader } from "@/components/ui/card";

function SkeletonBlock({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-muted ${className}`} />;
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <SkeletonBlock className="h-8 w-64" />
          <SkeletonBlock className="h-4 w-48" />
        </div>
        <div className="flex gap-2">
          <SkeletonBlock className="h-9 w-28" />
          <SkeletonBlock className="h-9 w-9" />
        </div>
      </div>

      {/* Balance summary */}
      <Card>
        <CardHeader>
          <SkeletonBlock className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <SkeletonBlock className="h-3 w-20" />
                <SkeletonBlock className="h-8 w-32" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Chart */}
      <Card>
        <CardHeader>
          <SkeletonBlock className="h-4 w-28" />
        </CardHeader>
        <CardContent>
          <SkeletonBlock className="h-[200px] w-full" />
        </CardContent>
      </Card>

      {/* Widget grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <SkeletonBlock className="h-4 w-24" />
            </CardHeader>
            <CardContent className="space-y-3">
              <SkeletonBlock className="h-10 w-full" />
              <SkeletonBlock className="h-10 w-full" />
              <SkeletonBlock className="h-10 w-3/4" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
