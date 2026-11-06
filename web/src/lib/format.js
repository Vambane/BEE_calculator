// South African number formatting: space as thousands separator, "R" prefix for rand.

const NBSP = " ";

export function groupThousands(n, decimals = 0) {
  if (n === null || n === undefined || Number.isNaN(n)) return "";
  const fixed = Math.abs(n).toFixed(decimals);
  const [int, frac] = fixed.split(".");
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, NBSP);
  return (n < 0 ? "−" : "") + grouped + (frac ? `.${frac}` : "");
}

export const rand = (n, decimals = 0) => `R${NBSP}${groupThousands(n, decimals)}`;

export function pts(n, decimals = 1) {
  if (n === null || n === undefined) return "–";
  return Number(n).toFixed(decimals).replace(/\.0+$/, decimals > 0 ? "" : "");
}

/** Points with up to 2 decimals, trailing zeros dropped (14 → "14", 3.25 → "3.25"). */
export function g(n) {
  if (n === null || n === undefined) return "–";
  return String(Math.round(n * 100) / 100);
}

/** Parse what a person typed: "1 250 000", "R1,250,000.50", "51%", "−3" → number | null. */
export function parseNumber(raw) {
  if (raw === null || raw === undefined) return null;
  const s = String(raw)
    .trim()
    .replace(/^R/i, "")
    .replace(/[%\s  ,]/g, "")
    .replace(/[−–]/g, "-");
  if (s === "" || s === "-" || s === ".") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}
