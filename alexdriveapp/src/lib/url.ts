/** Convert standard base64 to URL-safe base64 (no padding) */
export function toUrlSafeId(base64Id: string): string {
  return base64Id.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Convert URL-safe base64 back to standard base64 (with padding) */
export function fromUrlSafeId(urlSafeId: string): string {
  let base64 = urlSafeId.replace(/-/g, "+").replace(/_/g, "/");
  const pad = base64.length % 4;
  if (pad === 2) base64 += "==";
  else if (pad === 3) base64 += "=";
  return base64;
}

/** Slugify text: lowercase, replace non-alphanumeric with hyphens, trim */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** Build car detail URL path from translated name, year, and encrypted ID */
export function buildCarDetailPath(
  translatedName: string,
  year: string,
  encryptedId: string,
): string {
  // Extract numeric year (e.g. "2019" from "2019 [2019]" or "2019년")
  const yearMatch = year?.match(/(\d{4})/);
  const yearStr = yearMatch ? yearMatch[1] : "";

  const namePart = slugify(translatedName);
  const slug = yearStr ? `${namePart}-${yearStr}` : namePart;
  const urlSafeId = toUrlSafeId(encryptedId);

  return `/car/${slug}/${urlSafeId}`;
}
