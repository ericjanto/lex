import StatusPageClient from "./StatusPageClient";

export type StatusVal = "staged" | "committed" | "pushed";

export default async function Page({ params }: { params: Promise<{ statusVal: string }> }) {
  const { statusVal } = await params;

  if (
    statusVal !== "staged" &&
    statusVal !== "committed" &&
    statusVal !== "pushed"
  ) {
    return <div>Invalid status value</div>;
  }

  return <StatusPageClient statusVal={statusVal as StatusVal} />;
}
