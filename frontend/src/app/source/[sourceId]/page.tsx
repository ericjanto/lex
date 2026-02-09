import PaginatedContexts from "@/components/PaginatedContexts";
import SourceOverview from "@/components/SourceOverview";
import { API_BASE_URL } from "@/lib/const";

export default async function Page({ params }: { params: Promise<{ sourceId: string }> }) {
  const { sourceId } = await params;
  const sourceIdNum = parseInt(sourceId);
  return (
    <>
      <SourceOverview sourceId={sourceIdNum} />
      <br />
      <PaginatedContexts
        fetchQuery={`${API_BASE_URL}/source_contexts/${sourceId}`}
        page_size={100}
      />
    </>
  );
}
