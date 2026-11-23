import { test, expect } from "@playwright/test";
import { randomUUID } from "node:crypto";

test("keep my edits, search, shortlist and account access", async ({
  page,
  request,
}) => {
  const base = process.env.CG_UI_URL || "http://localhost:3000";
  const email = "workspace-test-" + randomUUID() + "@example.invalid";
  const password = randomUUID(),
    replacement = randomUUID();
  const button = (name: string) =>
    page.getByRole("button", { name, exact: true });
  const name = page.getByLabel("Name", { exact: true });
  await page.goto(base);
  await button("New here? Create an account").click();
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await button("Create account").click();
  try {
    const code = await page.locator(".notice code").innerText();
    await button("I have saved it").click();
    await button("Your profile").click();
    await name.fill("Example");
    await button("Confirm & save profile").click();
    await expect(page.getByRole("status")).toHaveText("Profile saved.");
    await name.fill("Unsaved example");
    page.once("dialog", (d) => d.dismiss());
    await button("Discover").click();
    await expect(name).toHaveValue("Unsaved example");
    page.once("dialog", (d) => d.accept());
    await button("Discover").click();
    await button("Your profile").click();
    await expect(name).toHaveValue("Example");
    await button("Discover").click();
    await button("Remote Python internships").click();
    const card = page.locator(".job-card").first();
    await expect(card).toBeVisible({ timeout: 90000 });
    await expect(
      page.getByText("Built-in search · no external AI"),
    ).toBeVisible();
    await card.getByRole("button", { name: /^Save / }).click();
    await expect(card.getByRole("button", { name: /^Saved / })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await button("Saved opportunities").click();
    await button("View saved match evidence").click();
    await expect(page.getByRole("dialog")).toContainText(
      "Why this role appeared",
    );
    await page.keyboard.press("Escape");
    await button("Discover").click();
    await page.locator("#query").fill("Only AI/ML ones");
    await button("Ask agent").click();
    await expect(
      page.getByText("domain: AI/ML", { exact: true }),
    ).toBeVisible();
    await button("Dark appearance").click();
    await page.reload();
    await expect(card).toBeVisible();
    await expect(page.locator(".workspace")).toHaveClass(/dark/);
    await page
      .getByText("Find Remote Python internships", { exact: true })
      .click();
    await expect(page.locator("details[open] li").first()).toBeVisible();
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page
        .locator("nav")
        .evaluate((el) => el.scrollWidth <= el.clientWidth + 1),
    ).toBeTruthy();
    await button("Evaluation lab").click();
    await expect(page.locator("main")).not.toContainText(
      "Run the evaluation script",
    );
    await button("Sign out").click();
    await button("Forgot password?").click();
    await page.getByLabel("Email", { exact: true }).fill(email);
    await page.getByLabel("Recovery code", { exact: true }).fill(code);
    await page.getByLabel("New password", { exact: true }).fill(replacement);
    await button("Reset password").click();
    await expect(page.getByRole("status")).toContainText("Password updated");
    const reuse = await request.post(base + "/api/v1/auth/reset-password", {
      data: { email, password, code },
    });
    expect(reuse.status()).toBe(400);
    await page.getByLabel("Email", { exact: true }).fill(email);
    await page.getByLabel("Password", { exact: true }).fill(replacement);
    await button("Sign in").click();
    await expect(page.locator("#query")).toBeVisible();
  } finally {
    for (const candidate of [replacement, password]) {
      const login = await request.post(base + "/api/v1/auth/login", {
        data: { email, password: candidate },
      });
      if (login.ok()) {
        const remove = await request.delete(base + "/api/v1/auth/me", {
          headers: { "X-CSRF-Token": (await login.json()).csrf },
        });
        expect(remove.ok()).toBeTruthy();
        break;
      }
    }
  }
});
