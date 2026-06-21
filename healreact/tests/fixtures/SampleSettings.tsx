import React from "react";

/**
 * Synthetic settings panel — tests L1 intent labelling on:
 *   - fieldset grouping (notifications fieldset has 3 checkboxes with the
 *     same intent shape but different topics)
 *   - select dropdowns
 *   - destructive button (delete account) — must not collapse with cancel
 *   - cancel vs save vs discard ambiguity inside one footer row
 */
export function SampleSettings() {
  const { t } = useTranslation();
  return (
    <section aria-labelledby="settings-h">
      <h2 id="settings-h">{t("settings.title")}</h2>

      <form onSubmit={(e) => e.preventDefault()}>
        <fieldset>
          <legend>{t("settings.notifications.legend")}</legend>
          <label>
            <input type="checkbox" name="notifyEmail" defaultChecked />
            {t("settings.notifications.email")}
          </label>
          <label>
            <input type="checkbox" name="notifyPush" />
            {t("settings.notifications.push")}
          </label>
          <label>
            <input type="checkbox" name="notifyDigest" />
            {t("settings.notifications.weeklyDigest")}
          </label>
        </fieldset>

        <fieldset>
          <legend>{t("settings.locale.legend")}</legend>
          <label htmlFor="lang">{t("settings.locale.language")}</label>
          <select id="lang" name="language" defaultValue="en">
            <option value="en">English</option>
            <option value="zh">中文</option>
            <option value="ja">日本語</option>
          </select>
        </fieldset>

        <footer className="settings-actions">
          <button type="button" data-testid="settings-discard">
            {t("settings.discard")}
          </button>
          <button type="submit" className="btn-primary">
            {t("settings.save")}
          </button>
        </footer>
      </form>

      <section className="danger-zone" aria-label={t("settings.dangerZone")}>
        <button
          type="button"
          className="btn-destructive"
          data-testid="delete-account-btn"
          aria-label={t("settings.deleteAccount")}
        >
          {t("settings.deleteAccount")}
        </button>
      </section>
    </section>
  );
}

declare function useTranslation(): { t: (k: string) => string };
