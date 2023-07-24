export function appendQueryParams(
  href: string,
  params: { [key: string]: string | number } = {}
): string {
  const url = new URL(href);

  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value.toString());
  }
  return url.toString();
}
