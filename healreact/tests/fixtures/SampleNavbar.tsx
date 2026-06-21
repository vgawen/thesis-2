import React from "react";

/**
 * Synthetic navbar — tests L1 intent labelling on:
 *   - role-only elements with no aria-label (logo link)
 *   - duplicate accessible names across separate groups (two "Search" labels)
 *   - dropdown toggles that have icon-only text
 *   - sign-in vs sign-up disambiguation (same component, same role, sibling)
 */
export function SampleNavbar() {
  const { t } = useTranslation();
  return (
    <nav aria-label="primary" className="topbar">
      <a href="/" className="brand">
        <img src="/logo.svg" alt="Acme" />
      </a>

      <form role="search" onSubmit={(e) => e.preventDefault()}>
        <label htmlFor="q-top">{t("search.label")}</label>
        <input id="q-top" name="q" type="search" placeholder={t("search.placeholder")} />
        <button type="submit" aria-label={t("search.submit")}>
          🔍
        </button>
      </form>

      <ul className="account-menu">
        <li>
          <button data-testid="user-menu-toggle" aria-haspopup="menu" aria-expanded="false">
            <span aria-hidden="true">▾</span>
            <span className="sr-only">{t("nav.account.toggle")}</span>
          </button>
        </li>
        <li>
          <a href="/login" className="btn-ghost">
            {t("nav.signIn")}
          </a>
        </li>
        <li>
          <a href="/signup" className="btn-primary" data-intent="create-account">
            {t("nav.signUp")}
          </a>
        </li>
      </ul>
    </nav>
  );
}

declare function useTranslation(): { t: (k: string) => string };
