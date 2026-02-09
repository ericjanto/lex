import StatusPageClient from "./StatusPageClient";

export type StatusVal = "new" | "synced" | "learned";

export default async function Page({ params }: { params: Promise<{ statusVal: string }> }) {
  const { statusVal } = await params;

  if (
    statusVal !== "new" &&
    statusVal !== "synced" &&
    statusVal !== "learned"
  ) {
    return <div>Invalid status value</div>;
  }

  return <StatusPageClient statusVal={statusVal as StatusVal} />;
}
