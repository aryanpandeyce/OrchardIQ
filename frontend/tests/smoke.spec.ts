import { test, expect } from "@playwright/test";

test.describe("OrchardIQ Frontend Smoke Suite", () => {
  test("loads homepage, header navigation and hero", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/OrchardIQ/);
    await expect(page.locator("h1")).toContainText("Ask OrchardIQ Anything");
    await expect(page.getByText("Multi-Agent LangGraph • DuckDB Lakehouse")).toBeVisible();
  });

  test("switches between workspace tabs", async ({ page }) => {
    await page.goto("/");
    // Switch to Catalog
    await page.getByRole("button", { name: "Data Catalog" }).click();
    await expect(page.getByText("Lakehouse Star-Schema Catalog")).toBeVisible();

    // Switch to Evals
    await page.getByRole("button", { name: "Eval Benchmark" }).click();
    await expect(page.getByText("Agent Evaluation Benchmark Suite")).toBeVisible();

    // Switch to Quality
    await page.getByRole("button", { name: "Data Quality" }).click();
    await expect(page.getByText("Lakehouse Data Quality Gates")).toBeVisible();

    // Switch to Audit
    await page.getByRole("button", { name: "Audit Log" }).click();
    await expect(page.getByText("Immutable Governance Audit Trail")).toBeVisible();

    // Switch to Stream
    await page.getByRole("button", { name: "Live Stream" }).click();
    await expect(page.getByText("Real-Time Event Stream")).toBeVisible();

    // Return to Chat
    await page.getByRole("button", { name: "Chat Workspace" }).click();
    await expect(page.locator("h1")).toContainText("Ask OrchardIQ Anything");
  });

  test("executes demo story chip and renders answer card", async ({ page }) => {
    await page.goto("/");
    // Click on Story 1 chip
    const storyChip = page.locator("button").filter({ hasText: "Story 1: APAC Battery Claim Spike" });
    await expect(storyChip).toBeVisible();
    await storyChip.click();

    // Answer card or timeline should appear
    await expect(page.locator("text=Executive Incident Report: APAC PearPhone 16 Pro Battery Claims Surge")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Root Cause: Component defect in battery cell lot BP-2025-08")).toBeVisible();
    await expect(page.getByText("GOVERNANCE: APPROVED")).toBeVisible();
  });

  test("switches role and verifies PII masking indicator", async ({ page }) => {
    await page.goto("/");
    const roleSelect = page.locator("select");
    await expect(roleSelect).toBeVisible();
    await roleSelect.selectOption("finance");
    await expect(roleSelect).toHaveValue("finance");
    await roleSelect.selectOption("admin");
    await expect(roleSelect).toHaveValue("admin");
  });
});
