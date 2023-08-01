export default function Page({ params }: { params: { contextId: string } }) {
  return (
    <>
      <h1>Context {params.contextId}</h1>
      <div>Dummy page, to be implemented.</div>
    </>
  );
}
