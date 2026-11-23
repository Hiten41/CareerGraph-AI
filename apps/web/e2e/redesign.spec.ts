import { expect, test } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
import path from "node:path";

test("workspace layouts, preferences, saved comparisons and recorded evaluations", async ({
  page,
}) => {
  test.setTimeout(300000);
  const dir = process.env.CG_DESIGN_SHOTS;
  if (dir) await mkdir(dir, { recursive: true });
  const widths = dir ? [1440, 1024, 768, 390, 320] : [1440, 390, 320];
  async function capture(name: string) {
    for (const width of widths) {
      await page.setViewportSize({ width, height: width >= 1024 ? 960 : 844 });
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth + 1,
          ),
        )
        .toBe(true);
      if (dir)
        await page.screenshot({
          path: path.join(dir, name + "-" + width + ".png"),
        });
    }
    await page.setViewportSize({ width: 1440, height: 960 });
  }
  const btn = (name: string) => page.getByRole("button", { name, exact: true });
  await page.goto("http://localhost:3000");
  await btn("Sign in").waitFor();
  await capture("authentication");
  await btn("New here? Create an account").click();
  await page
    .getByLabel("Email", { exact: true })
    .fill("design-" + randomUUID() + "@example.invalid");
  await page.getByLabel("Password", { exact: true }).fill(randomUUID());
  await btn("Create account").click();
  await btn("I have saved it").click();
  await capture("discover");
  await btn("Profile").click();
  await page.getByLabel("Name", { exact: true }).fill("Sample Candidate");
  await page.getByLabel("Skills (comma separated)").fill("Python, SQL");
  await btn("Confirm & save profile").click();
  await expect(page.getByRole("status")).toHaveText("Profile saved.");
  await capture("profile");
  await btn("Preferences & memory").click();
  const pref = page.getByLabel(/Roles, work type/);
  await pref.fill("backend\nremote");
  await btn("Save preferences").click();
  await expect(page.getByRole("status")).toHaveText("Preferences updated.");
  await btn("Discover").click();
  await btn("Preferences & memory").click();
  await expect(pref).toHaveValue("backend\nremote");
  await capture("preferences");
  await btn("Discover").click();
  await btn("Remote Python internships").click();
  const cards = page.locator(".job-card");
  await cards.first().waitFor({ timeout: 60000 });
  await capture("search");
  await cards.first().getByRole("button", { name: "Explain match" }).click();
  await capture("match-evidence");
  await page.keyboard.press("Escape");
  for (const i of [0, 1]) {
    await cards
      .nth(i)
      .getByRole("button", { name: /^Save / })
      .click();
    await expect(
      cards.nth(i).getByRole("button", { name: /^Saved / }),
    ).toBeVisible();
  }
  await btn("Saved Jobs").click();
  await expect(page.locator(".job-card")).toHaveCount(2);
  await page.locator(".job-card .match").first().waitFor();
  await expect(
    page.getByRole("alert").filter({ hasText: "Internal service error" }),
  ).toHaveCount(0);
  await capture("saved");
  for (const checkbox of await page.getByLabel("Compare this job").all())
    await checkbox.check();
  await btn("Compare selected (2/2)").click();
  await expect(
    page.getByRole("heading", { name: "Skill comparison" }),
  ).toBeVisible();
  await btn("Evaluation Lab").click();
  await expect(
    page.getByRole("heading", { name: "Evaluation Lab", exact: true }),
  ).toBeVisible();
  await page.waitForFunction(() => !document.querySelector(".loading"));
  await capture("evaluation");
  await btn("Dark appearance").click();
  await capture("evaluation-dark");
  await btn("Discover").click();
  await capture("search-dark");
  await page.setViewportSize({ width: 320, height: 844 });
  await btn("Navigation").click();
  await btn("Profile").click();
  await expect(page.getByLabel("Name", { exact: true })).toHaveValue(
    "Sample Candidate",
  );
});
