/** Encode carmanager encrypted ID for use in URL paths */
export function toUrlSafeId(id: string): string {
  return encodeURIComponent(id);
}

/** Decode carmanager encrypted ID from URL path */
export function fromUrlSafeId(urlSafeId: string): string {
  return decodeURIComponent(urlSafeId);
}

/** Slugify text: lowercase, replace non-alphanumeric with hyphens, trim */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** Build car detail URL path from name, year, and ID */
export function buildCarDetailPath(
  name: string,
  year: string,
  id: string,
): string {
  const yearMatch = year?.match(/(\d{4})/);
  const yearStr = yearMatch ? yearMatch[1] : "";

  const namePart = slugify(name);
  const slug = yearStr ? `${namePart}-${yearStr}` : namePart;

  return `/car/${slug}/${toUrlSafeId(id)}`;
}
