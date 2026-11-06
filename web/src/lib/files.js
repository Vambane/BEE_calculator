// Local file helpers. Nothing here touches the network.

export function downloadText(text, filename, type = "text/plain") {
  const blob = new Blob([text], { type: `${type};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Read a picked file as text, refusing anything over maxBytes before reading it. */
export async function readTextFile(file, maxBytes) {
  if (file.size > maxBytes) {
    throw new Error(`That file is over ${Math.round(maxBytes / 1_000_000)} MB.`);
  }
  const buf = await file.arrayBuffer();
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(buf).replace(/^﻿/, "");
  } catch {
    // Excel "CSV" on Windows is often cp1252.
    return new TextDecoder("windows-1252").decode(buf);
  }
}

/** Open the OS file picker and resolve with the chosen File (or null). */
export function pickFile(accept) {
  return new Promise((resolve) => {
    const input = Object.assign(document.createElement("input"), { type: "file", accept });
    input.onchange = () => resolve(input.files?.[0] ?? null);
    input.oncancel = () => resolve(null);
    input.click();
  });
}
