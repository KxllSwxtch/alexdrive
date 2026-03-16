/** IDs are simple numeric — pass through unchanged */
export function toUrlSafeId(id: string): string {
  return id;
}

/** IDs are simple numeric — pass through unchanged */
export function fromUrlSafeId(urlSafeId: string): string {
  return urlSafeId;
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
  // Extract numeric year (e.g. "2019" from "24.05" or "2019/08" or "2019년")
  const yearMatch = year?.match(/(\d{4})/);
  const yearStr = yearMatch ? yearMatch[1] : "";

  const namePart = slugify(name);
  const slug = yearStr ? `${namePart}-${yearStr}` : namePart;

  return `/car/${slug}/${id}`;
}
