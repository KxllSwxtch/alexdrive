export function formatPrice(price: string): string {
  // jenya prices are full won amounts like "9,290,000"
  const cleaned = price.replace(/[^0-9]/g, "").trim();
  const num = parseInt(cleaned, 10);
  if (isNaN(num)) return price;
  return `₩${num.toLocaleString("en-US")}`;
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
  const manMatch = mileage.match(/([\d,.]+)\s*만/);
  if (manMatch) {
    const num = parseFloat(manMatch[1].replace(/,/g, ""));
    if (isNaN(num)) return mileage;
    const km = Math.round(num * 10000);
    return `${km.toLocaleString("en-US")} km`;
  }
  const kmMatch = mileage.match(/([\d,]+)\s*km/i);
  if (kmMatch) {
    const num = parseInt(kmMatch[1].replace(/,/g, ""), 10);
    if (isNaN(num)) return mileage;
    return `${num.toLocaleString("en-US")} km`;
  }
  return mileage;
}
