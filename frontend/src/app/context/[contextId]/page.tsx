export default async function Page({ params }: { params: Promise<{ contextId: string }> }) {
  const { contextId } = await params;
  return (
    <>
      <h1>Context {contextId}</h1>
      <div>Dummy page, to be implemented.</div>
    </>
  );
}
