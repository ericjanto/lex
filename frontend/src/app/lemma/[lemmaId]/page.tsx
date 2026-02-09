import PaginatedContexts from "@/components/PaginatedContexts";
import LemmaOverview from "@/components/LemmaOverview";
import { API_BASE_URL } from "@/lib/const";

export default async function Page({ params }: { params: Promise<{ lemmaId: string }> }) {
  const { lemmaId } = await params;
  const lemmaIdNum = parseInt(lemmaId);
  return (
    <>
      <LemmaOverview lemmaId={lemmaIdNum} />
      <br />
      <PaginatedContexts
        fetchQuery={`${API_BASE_URL}/lemma_contexts/${lemmaId}`}
        page_size={100}
        highlightedLemmaId={lemmaIdNum}
      />
    </>
  );
}
