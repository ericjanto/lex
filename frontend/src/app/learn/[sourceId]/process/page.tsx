import ProcessLemmata from "@/components/ProcessLemmata";

export default async function ProcessPage({ params }: { params: Promise<{ sourceId: string }> }) {
    const { sourceId } = await params;
    return <ProcessLemmata sourceId={parseInt(sourceId)} />;
}
