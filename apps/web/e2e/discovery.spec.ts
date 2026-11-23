import { test, expect } from "@playwright/test";
test("register, discover, refine, inspect, save and visit evaluations", async ({
  page,
}) => {
  await page.goto("http://localhost:3000");
  await page
    .getByRole("button", { name: "New here? Create an account" })
    .click();
  await page
    .getByLabel("Email", { exact: true })
    .fill("browser-" + Date.now() + "@example.invalid");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-local-only");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await page.getByRole("button", { name: "I have saved it" }).click();
  await page.getByRole("button", { name: "Your profile", exact: true }).click();
  await page.getByLabel("Name", { exact: true }).fill("Fictional candidate");
  await page.getByLabel("Skills (comma separated)").fill("Python, SQL");
  await page.getByRole("button", { name: "Confirm & save profile" }).click();
  await expect(page.getByText("Profile saved.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Discover", exact: true }).click();
  const query = page.getByLabel("Describe your job search or follow-up");
  await query.fill("Find remote Python internships for 2028 graduates");
  await page.getByRole("button", { name: "Ask agent" }).click();
  await expect(page.locator(".job-card").first()).toBeVisible({
    timeout: 90000,
  });
  await query.fill("Only AI/ML ones");
  await page.getByRole("button", { name: "Ask agent" }).click();
  await expect(page.getByText("domain: AI/ML", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "View match evidence" })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.locator('.job-card button[aria-label^="Save"]').first().click();
  await expect(page.getByText("Saved to your opportunities.")).toBeVisible();
  await page.screenshot({ path: "../../docs/discovery.png" });
  await query.fill("No remote roles");
  await page.getByRole("button", { name: "Ask agent" }).click();
  await expect(
    page.getByText("A requirement conflicts with an exclusion.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(page.locator(".job-card")).toHaveCount(0);
  await query.fill("clear filters");
  await page.getByRole("button", { name: "Ask agent" }).click();
  await expect(page.locator(".job-card").first()).toBeVisible();
  await expect(page.getByText("mode: remote", { exact: true })).toHaveCount(0);
  await page.route("**/api/v1/jobs/search", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Search temporarily unavailable" }),
    }),
  );
  await page.getByText("Advanced search", { exact: true }).click();
  await query.fill("another role");
  await page.getByRole("button", { name: "Direct search" }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "Search temporarily unavailable",
  );
  await expect(page.locator(".job-card")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Saved opportunities", exact: true })
    .click();
  await expect(page.getByText("Remove from saved")).toBeVisible();
  await page
    .getByRole("button", { name: "Evaluation lab", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Evaluation lab." }),
  ).toBeVisible();
});
