import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const api = "http://127.0.0.1:8000";
const pdfPath = name => path.resolve("../backend/demo_documents", name);

test.afterEach(async ({ page, request }, info) => {
  if (info.status !== info.expectedStatus) {
    console.log("Browser failure page:", await page.locator("body").innerText().catch(() => "Page unavailable"));
    console.log("Persisted bid state:", await (await request.get(`${api}/bids`)).text());
  }
});

test("real services: tender, bidder, Golden Demo, evidence, decision, audit and exports", async ({ page, request }) => {
  await expect.poll(async () => (await request.get(`${api}/tenders`)).status(), { timeout: 60000 }).toBe(200);
  await page.goto("/tenders");
  await page.getByRole("button", { name: "Create tender", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Tender title").fill("SIH browser workflow tender");
  await dialog.getByLabel("Department").fill("Health");
  await dialog.getByLabel("Deadline").fill("2027-01-01");
  await dialog.getByLabel("Budget").fill("INR 100000000");
  await dialog.getByRole("button", { name: "Create tender", exact: true }).click();
  await expect(page).toHaveURL(/\/tenders\/tnd-/);
  const tenderId = decodeURIComponent(page.url().split("/").pop());
  await page.getByText("Register a bidder", { exact: true }).click();
  await page.getByLabel("Legal bidder name").fill("TechNova Systems Pvt. Ltd.");
  await page.getByLabel("GSTIN (optional)").fill("27AADCB2230M1Z2");
  await page.getByRole("button", { name: "Register and upload" }).click();
  await expect(page).toHaveURL(/\/evaluations\/bid-/);
  const techId = page.url().split("/").pop();
  await page.getByLabel("Select PDF").setInputFiles(pdfPath("technova.pdf"));
  await expect(page.getByText("Evaluation complete — awaiting officer decision", { exact: true })).toBeVisible({ timeout: 120000 });
  await expect(page.getByText("LOW RISK", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Inspect", exact: true })).toHaveCount(5);
  const pdfLink = page.getByRole("link", { name: "Open original PDF" });
  const pdf = await request.get(await pdfLink.getAttribute("href"));
  expect(pdf.status()).toBe(200);
  expect((await pdf.body()).subarray(0, 5).toString()).toBe("%PDF-");
  await page.getByLabel("Officer outcome").selectOption("Approve");
  await page.getByLabel("Rationale").fill("Original PDF and rule evidence checked in browser workflow.");
  await page.getByRole("button", { name: "Record decision and rationale" }).click();
  await expect(page.getByText("Recorded decision:").filter({ hasText: "Approve" })).toBeVisible();

  for (const [name, filename, status, risk] of [
    ["Apex Industrial Solutions Pvt. Ltd.", "apex.pdf", "FAIL", "CRITICAL"],
    ["MedCore Technologies Pvt. Ltd.", "medcore.pdf", "REVIEW", "MEDIUM"],
  ]) {
    const created = await request.post(`${api}/bids`, { data: { tender_id: tenderId, bidder_name: name } });
    expect(created.status()).toBe(200);
    const bid = await created.json();
    await page.goto(`/evaluations/${bid.id}`);
    await page.getByLabel("Select PDF").setInputFiles(pdfPath(filename));
    await expect(page.getByText("Evaluation complete — awaiting officer decision", { exact: true })).toBeVisible({ timeout: 120000 });
    await expect(page.getByText(`${risk} RISK`, { exact: true })).toBeVisible();
    const persisted = await (await request.get(`${api}/bids/${bid.id}`)).json();
    expect(persisted.status).toBe(status);
  }
  const detail = await (await request.get(`${api}/bids/${techId}`)).json();
  const tender = await (await request.get(`${api}/tenders/${tenderId}`)).json();
  const listing = await (await request.get(`${api}/bids`)).json();
  expect(tender.bids.find(b => b.id === techId).score).toBe(detail.score);
  expect(listing.find(b => b.id === techId).status).toBe(detail.status);

  await page.goto("/evaluations");
  await page.getByPlaceholder("Search bidders").fill("MedCore");
  await expect(page.getByRole("heading", { name: "MedCore Technologies Pvt. Ltd." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "TechNova Systems Pvt. Ltd." })).toHaveCount(0);
  await page.locator("select").first().selectOption("FAIL");
  await expect(page.getByText("No bidders match your filters.")).toBeVisible();
  await page.goto("/audit");
  await page.getByLabel("Search events").fill("Original PDF and rule evidence checked");
  await expect(page.getByText(/Decision Recorded: Approve; rationale/)).toBeVisible();
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export filtered CSV" }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe("audit-events.csv");
  await page.goto("/reports");
  await expect(page.getByRole("button", { name: "Export CSV" })).toHaveCount(3);
  await page.goto("/settings");
  await expect(page.getByText("Runtime configuration (read-only)")).toBeVisible();
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "What needs your attention?" })).toBeVisible();
  for (const width of [390, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Tenders", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Tenders", exact: true })).toBeVisible();

  for (const content of [Buffer.from("not pdf"), Buffer.from("%PDF-1.4\ncorrupt\n%%EOF")]) {
    const rejected = await request.post(`${api}/upload/${techId}`, { multipart: { file: { name: "invalid.pdf", mimeType: "application/pdf", buffer: content } } });
    expect(rejected.status()).toBe(422);
  }
});
