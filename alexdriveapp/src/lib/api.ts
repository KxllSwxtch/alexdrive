const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:3001";

export async function backendFetch<T>(
  path: string,
  searchParams?: URLSearchParams,
  nextOptions?: NextFetchRequestConfig,
): Promise<T> {
  const url = new URL(`/api${path}`, BACKEND_URL);
  if (searchParams) url.search = searchParams.toString();
  const res = await fetch(url.toString(), {
    signal: AbortSignal.timeout(30_000),
    headers: { Accept: "application/json" },
    next: nextOptions,
  });
  if (!res.ok) throw new Error(`Backend error: ${res.status}`);
  return res.json() as Promise<T>;
}
