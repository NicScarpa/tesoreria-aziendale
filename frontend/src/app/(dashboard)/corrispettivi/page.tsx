"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CorrispettiviRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/fatture/corrispettivi");
  }, [router]);
  return null;
}
