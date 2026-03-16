export function formatPrice(price: string | number): string {
  if (typeof price === "number") {
    if (price === 0) return "";
    return `₩${price.toLocaleString("en-US")}`;
  }
  const cleaned = price.replace(/[^0-9]/g, "").trim();
  const num = parseInt(cleaned, 10);
  if (isNaN(num)) return price;
  return `₩${num.toLocaleString("en-US")}`;
}

/** Format man-won price (만원) for display: e.g. 3240 → "3,240 만원" */
export function formatPriceMan(priceMan: number): string {
  if (!priceMan) return "";
  return `${priceMan.toLocaleString("en-US")} 만원`;
}

/** Convert man-won to full KRW: 3240 → 32400000 */
export function manWonToKrw(priceMan: number): number {
  return priceMan * 10000;
}

/** Format man-won to full KRW display: 3240 → "₩32,400,000" */
export function formatPriceKrw(priceManWon: number): string {
  if (!priceManWon) return "";
  return formatPrice(manWonToKrw(priceManWon));
}

export function formatKrw(value: number): string {
  return Math.round(value).toLocaleString("en-US");
}

export function parseKrwInput(raw: string): number {
  return parseInt(raw.replace(/\D/g, ""), 10) || 0;
}

export function priceStringToKrw(price: string): number {
  const cleaned = price.replace(/[^0-9]/g, "").trim();
  const num = parseInt(cleaned, 10);
  return isNaN(num) ? 0 : num;
}

export function formatMileage(mileage: string): string {
  // namsuwon provides pre-formatted "35,983Km" — normalize to "35,983 km"
  const kmMatch = mileage.match(/([\d,]+)\s*[Kk][Mm]/i);
  if (kmMatch) {
    const num = parseInt(kmMatch[1].replace(/,/g, ""), 10);
    if (isNaN(num)) return mileage;
    return `${num.toLocaleString("en-US")} km`;
  }
  // Fallback: Korean 만km format
  const manMatch = mileage.match(/([\d,.]+)\s*만/);
  if (manMatch) {
    const num = parseFloat(manMatch[1].replace(/,/g, ""));
    if (isNaN(num)) return mileage;
    const km = Math.round(num * 10000);
    return `${km.toLocaleString("en-US")} km`;
  }
  return mileage;
}
