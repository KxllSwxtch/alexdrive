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

// Server-side in-memory cache for filter data.
// Next.js data cache has a 2MB per-entry limit; filter response is ~2.9MB.
// This module-level cache bypasses that limit (server-only, survives across requests).
let _filterCache: { data: unknown; expiry: number } | null = null;
let _filterPromise: Promise<unknown> | null = null;
const FILTER_CACHE_TTL = 3600_000; // 1 hour in ms

export async function fetchFiltersCached<T>(): Promise<T> {
  if (_filterCache && Date.now() < _filterCache.expiry) {
    return _filterCache.data as T;
  }
  // Dedup concurrent requests (thundering-herd protection)
  if (!_filterPromise) {
    _filterPromise = backendFetch<T>("/filters", undefined, { revalidate: 0 })
      .then((data) => {
        _filterCache = { data, expiry: Date.now() + FILTER_CACHE_TTL };
        _filterPromise = null;
        return data;
      })
      .catch((err) => {
        _filterPromise = null;
        // Serve stale data if available
        if (_filterCache) return _filterCache.data;
        throw err;
      });
  }
  return _filterPromise as Promise<T>;
}
