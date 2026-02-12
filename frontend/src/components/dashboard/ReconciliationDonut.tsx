"use client";

import { useRouter } from "next/navigation";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RiconciliazioneSection } from "@/types/dashboard";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface Props {
  data: RiconciliazioneSection;
}

export function ReconciliationDonut({ data }: Props) {
  const router = useRouter();

  const chartData = [
    { name: "Riconciliati", value: Number(data.percentuale) },
    { name: "Non riconciliati", value: 100 - Number(data.percentuale) },
  ];

  const COLORS = ["#22c55e", "#e5e7eb"];

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push("/riconciliazione")}>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">Riconciliazione</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="relative h-[120px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={35}
                outerRadius={50}
                paddingAngle={2}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
              >
                {chartData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl font-bold">{data.percentuale}%</span>
          </div>
        </div>

        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Non riconciliati</span>
            <span className="font-medium">{data.movimenti_non_riconciliati}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Importo</span>
            <span className="font-medium">{formatCurrency(data.importo_non_riconciliato)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
