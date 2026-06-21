import React from "react";

export function SampleCart() {
  const { t } = useTranslation();
  return (
    <div className="cart-root">
      <h1>{t("cart.title")}</h1>
      <ul aria-label="cart items">
        <li>
          <input
            type="number"
            aria-label={t("cart.qty")}
            data-testid="cart-qty-input"
            min={1}
            max={99}
          />
          <button
            data-testid="remove-item-btn"
            aria-label="Remove item"
            onClick={() => {}}
          >
            Remove
          </button>
        </li>
      </ul>
      <form onSubmit={(e) => e.preventDefault()}>
        <label htmlFor="coupon">{t("cart.coupon")}</label>
        <input id="coupon" name="coupon" placeholder="Coupon code" />
        <button type="submit" className="btn-primary">
          {t("cart.apply")}
        </button>
      </form>
      <a href="/checkout" role="button" data-intent="checkout-button" className="btn">
        Checkout
      </a>
      <div role="button" tabIndex={0} onClick={() => {}}>
        Custom div-button
      </div>
    </div>
  );
}

declare function useTranslation(): { t: (k: string) => string };
