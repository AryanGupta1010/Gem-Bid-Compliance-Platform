type Cell = string | number | boolean | null | undefined;
function toCSV(rows: Record<string, Cell>[]): string {
  if (!rows.length) return "";
  const headers = Array.from(new Set(rows.flatMap(row => Object.keys(row))));
  const quote = (value: Cell) => {
    let text = String(value ?? "");
    if (/^[\s]*[=+@-]/.test(text)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  };
  return [headers.map(quote).join(","), ...rows.map(row => headers.map(key => quote(row[key])).join(","))].join("\r\n");
}
export function exportToCSV(filename: string, rows: Record<string, Cell>[]) {
  const url = URL.createObjectURL(new Blob(["\ufeff", toCSV(rows)], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; document.body.appendChild(anchor);
  anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
