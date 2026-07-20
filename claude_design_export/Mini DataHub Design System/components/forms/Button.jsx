import React from "react";

/**
 * Primary interactive action. `primary` = filled accent (viz / submit
 * actions); `secondary` = outlined (homepage link, secondary actions);
 * `ghost` = borderless (tab-adjacent, low-emphasis).
 */
export function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  onClick,
  disabled = false,
  href,
  target,
}) {
  const base = {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    fontFamily: "var(--font-sans)",
    fontWeight: "var(--weight-semibold)",
    fontSize: size === "sm" ? "var(--text-xs)" : "var(--text-sm)",
    padding: size === "sm" ? "6px 10px" : "9px 16px",
    borderRadius: "var(--radius-md)",
    border: "1px solid transparent",
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.5 : 1,
    transition: "background var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard)",
    textDecoration: "none",
  };

  const variants = {
    primary: {
      background: "var(--accent)",
      color: "var(--text-on-accent)",
      borderColor: "var(--accent)",
    },
    secondary: {
      background: "var(--surface-card)",
      color: "var(--text-primary)",
      borderColor: "var(--border-default)",
    },
    ghost: {
      background: "transparent",
      color: "var(--text-secondary)",
      borderColor: "transparent",
    },
  };

  const style = { ...base, ...variants[variant] };
  const content = (
    <>
      {icon && <i data-lucide={icon} style={{ width: 14, height: 14 }} />}
      {children}
    </>
  );

  if (href) {
    return (
      <a href={href} target={target} rel="noreferrer" style={style}>
        {content}
      </a>
    );
  }
  return (
    <button onClick={onClick} disabled={disabled} style={style}>
      {content}
    </button>
  );
}
