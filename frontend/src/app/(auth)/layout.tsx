export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f9f9f9] p-4">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}
