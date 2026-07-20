/* @ds-bundle: {"format":4,"namespace":"MiniDataHubDesignSystem_f6abe1","components":[{"name":"CoverageHeatmap","sourcePath":"components/data-display/CoverageHeatmap.jsx"},{"name":"DatasetCard","sourcePath":"components/data-display/DatasetCard.jsx"},{"name":"StatCard","sourcePath":"components/data-display/StatCard.jsx"},{"name":"Tag","sourcePath":"components/data-display/Tag.jsx"},{"name":"Alert","sourcePath":"components/feedback/Alert.jsx"},{"name":"Button","sourcePath":"components/forms/Button.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"SearchInput","sourcePath":"components/forms/SearchInput.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Slider","sourcePath":"components/forms/Slider.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"},{"name":"DetailDrawer","sourcePath":"components/overlay/DetailDrawer.jsx"}],"sourceHashes":{"components/data-display/CoverageHeatmap.jsx":"e758d214890e","components/data-display/DatasetCard.jsx":"e993d23e265f","components/data-display/StatCard.jsx":"9bb1b70db2d0","components/data-display/Tag.jsx":"4fe9d6972c51","components/feedback/Alert.jsx":"458aeb26c165","components/forms/Button.jsx":"4a0f3a3a6fd1","components/forms/Checkbox.jsx":"b5e811db0f74","components/forms/SearchInput.jsx":"170f6c6c169d","components/forms/Select.jsx":"c14e3e8eab8b","components/forms/Slider.jsx":"81b7a3c61ce8","components/navigation/Tabs.jsx":"ac5ec7d0e103","components/overlay/DetailDrawer.jsx":"e063e22c9286","handoff/mini-datahub-integration/web/tailwind.config.js":"2a9e98f4a21d","ui_kits/data-hub/App.jsx":"06dab21a6bb0","ui_kits/data-hub/mock-data.js":"7e7e3ac73ab4"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.MiniDataHubDesignSystem_f6abe1 = window.MiniDataHubDesignSystem_f6abe1 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/data-display/CoverageHeatmap.jsx
try { (() => {
const {
  useState
} = React;
/** Embodiment × task-concept coverage heatmap — single-hue accent ramp, gray gaps. */
function CoverageHeatmap({
  embodiments,
  concepts,
  cells
}) {
  const [hover, setHover] = useState(null);
  const lookup = {};
  let max = 0;
  cells.forEach(c => {
    lookup[`${c.embodiment}|${c.concept}`] = c.count;
    if (c.count > max) max = c.count;
  });
  const color = n => {
    if (!n) return "var(--heatmap-empty)";
    const t = 0.15 + 0.85 * (n / max);
    return `color-mix(in srgb, var(--heatmap-fill) ${Math.round(t * 100)}%, white)`;
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-card)",
      border: "1px solid var(--border-subtle)",
      borderRadius: "var(--radius-xl)",
      padding: 24,
      boxShadow: "var(--shadow-sm)",
      fontFamily: "var(--font-sans)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "baseline",
      marginBottom: 4
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontSize: "var(--text-h2)",
      fontWeight: "var(--weight-bold)",
      margin: 0,
      color: "var(--text-primary)"
    }
  }, "\u8986\u76D6\u5EA6\u5730\u56FE"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-xs)",
      color: "var(--text-tertiary)"
    }
  }, "\u989C\u8272\u8D8A\u6DF1\u6570\u636E\u8D8A\u591A \xB7 \u6D45\u7070=\u7A7A\u767D(gap)")), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-secondary)",
      margin: "0 0 16px"
    }
  }, "\u672C\u4F53 \xD7 \u4EFB\u52A1\u6982\u5FF5\u3002\u4E00\u773C\u770B\u51FA\u54EA\u4E9B\u7EC4\u5408\u6570\u636E\u5145\u8DB3\u3001\u54EA\u4E9B\u662F\u7A7A\u767D\u3002"), /*#__PURE__*/React.createElement("div", {
    style: {
      overflowX: "auto"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      borderCollapse: "separate",
      borderSpacing: 4
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null), concepts.map(c => /*#__PURE__*/React.createElement("th", {
    key: c.id,
    style: {
      padding: 4,
      verticalAlign: "bottom"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--text-secondary)",
      writingMode: "vertical-rl",
      height: 80
    }
  }, c.label))))), /*#__PURE__*/React.createElement("tbody", null, embodiments.map(e => /*#__PURE__*/React.createElement("tr", {
    key: e
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-medium)",
      color: "var(--text-secondary)",
      paddingRight: 10,
      whiteSpace: "nowrap"
    }
  }, e), concepts.map(c => {
    const n = lookup[`${e}|${c.id}`] || 0;
    return /*#__PURE__*/React.createElement("td", {
      key: c.id
    }, /*#__PURE__*/React.createElement("div", {
      onMouseEnter: () => setHover({
        e,
        c: c.label,
        n
      }),
      onMouseLeave: () => setHover(null),
      style: {
        width: 36,
        height: 36,
        borderRadius: "var(--radius-md)",
        background: color(n),
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 11,
        fontWeight: 600,
        color: n > max * 0.5 ? "#fff" : "var(--text-secondary)"
      }
    }, n || ""));
  })))))), hover && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 16,
      fontSize: "var(--text-sm)",
      color: "var(--text-secondary)"
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      color: "var(--text-primary)"
    }
  }, hover.e), " \xD7 ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: "var(--text-primary)"
    }
  }, hover.c), "\uFF1A", hover.n > 0 ? `${hover.n} 个数据集` : "空白 — 该组合暂无数据"));
}
Object.assign(__ds_scope, { CoverageHeatmap });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data-display/CoverageHeatmap.jsx", error: String((e && e.message) || e) }); }

// components/data-display/StatCard.jsx
try { (() => {
/** Top-of-page metric card (dataset count / episode count / frame count). */
function StatCard({
  label,
  value,
  icon
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-card)",
      border: "1px solid var(--border-subtle)",
      borderRadius: "var(--radius-lg)",
      padding: "16px 18px",
      boxShadow: "var(--shadow-sm)",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-medium)",
      color: "var(--text-secondary)"
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-h1)",
      fontWeight: "var(--weight-bold)",
      color: "var(--text-primary)",
      marginTop: 4,
      fontFamily: "var(--font-mono)"
    }
  }, value)), icon && /*#__PURE__*/React.createElement("i", {
    "data-lucide": icon,
    style: {
      width: 18,
      height: 18,
      color: "var(--text-tertiary)"
    }
  }));
}
Object.assign(__ds_scope, { StatCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data-display/StatCard.jsx", error: String((e && e.message) || e) }); }

// components/data-display/Tag.jsx
try { (() => {
/**
 * Small label pill — mirrors the source app's `TONES` map exactly
 * (slate→neutral, indigo→accent, emerald→success, amber→warning, rose→danger).
 * Used for embodiment/format/license/quality/failure tags on dataset cards
 * and in the detail drawer (task/scene/modality/action-convention tags).
 */
function Tag({
  children,
  tone = "neutral"
}) {
  const tones = {
    neutral: {
      background: "var(--tone-neutral-bg)",
      color: "var(--tone-neutral-fg)"
    },
    accent: {
      background: "var(--tone-accent-bg)",
      color: "var(--tone-accent-fg)"
    },
    success: {
      background: "var(--tone-success-bg)",
      color: "var(--tone-success-fg)"
    },
    warning: {
      background: "var(--tone-warning-bg)",
      color: "var(--tone-warning-fg)"
    },
    danger: {
      background: "var(--tone-danger-bg)",
      color: "var(--tone-danger-fg)"
    }
  };
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--text-xs)",
      fontWeight: "var(--weight-medium)",
      padding: "3px 8px",
      borderRadius: "var(--radius-sm)",
      marginRight: 4,
      marginBottom: 4,
      ...tones[tone]
    }
  }, children);
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data-display/Tag.jsx", error: String((e && e.message) || e) }); }

// components/data-display/DatasetCard.jsx
try { (() => {
/** One row in the dataset list/grid — opens the detail drawer on click. */
function DatasetCard({
  dataset: d,
  onClick
}) {
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClick,
    style: {
      background: "var(--surface-card)",
      border: "1px solid var(--border-subtle)",
      borderRadius: "var(--radius-lg)",
      padding: "14px 16px",
      boxShadow: "var(--shadow-sm)",
      cursor: onClick ? "pointer" : "default",
      transition: "box-shadow var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard)"
    },
    onMouseEnter: e => {
      e.currentTarget.style.boxShadow = "var(--shadow-md)";
      e.currentTarget.style.borderColor = "var(--accent-300)";
    },
    onMouseLeave: e => {
      e.currentTarget.style.boxShadow = "var(--shadow-sm)";
      e.currentTarget.style.borderColor = "var(--border-subtle)";
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: "var(--weight-semibold)",
      color: "var(--text-primary)",
      fontSize: "var(--text-body)"
    }
  }, d.name), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-xs)",
      color: "var(--text-tertiary)",
      fontFamily: "var(--font-mono)"
    }
  }, d.dataset_id)), d.quality_score != null && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-semibold)",
      color: "var(--accent)",
      fontFamily: "var(--font-mono)"
    }
  }, "\u8D28\u91CF ", d.quality_score.toFixed(2))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 8
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Tag, {
    tone: "accent"
  }, d.embodiment), /*#__PURE__*/React.createElement(__ds_scope.Tag, {
    tone: "neutral"
  }, d.source_format), /*#__PURE__*/React.createElement(__ds_scope.Tag, {
    tone: d.commercial_ok ? "success" : "warning"
  }, d.commercial_ok ? "可商用" : "非商用"), /*#__PURE__*/React.createElement(__ds_scope.Tag, {
    tone: "neutral"
  }, d.n_episodes, " \u8F68\u8FF9"), d.has_failure_labels && /*#__PURE__*/React.createElement(__ds_scope.Tag, {
    tone: "danger"
  }, "\u542B\u5931\u8D25")));
}
Object.assign(__ds_scope, { DatasetCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data-display/DatasetCard.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Alert.jsx
try { (() => {
/** Inline notice banner — used for the non-commercial-use warning in the detail drawer. */
function Alert({
  children,
  tone = "warning",
  icon = "alert-triangle"
}) {
  const tones = {
    warning: {
      background: "var(--warning-subtle)",
      border: "var(--amber-600)",
      color: "var(--amber-700)"
    },
    danger: {
      background: "var(--danger-subtle)",
      border: "var(--rose-600)",
      color: "var(--rose-700)"
    },
    info: {
      background: "var(--info-subtle)",
      border: "var(--sky-600)",
      color: "var(--sky-700)"
    }
  };
  const t = tones[tone];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      background: t.background,
      border: `1px solid ${t.border}`,
      borderRadius: "var(--radius-md)",
      padding: "10px 14px",
      fontSize: "var(--text-sm)",
      color: t.color
    }
  }, icon && /*#__PURE__*/React.createElement("i", {
    "data-lucide": icon,
    style: {
      width: 16,
      height: 16,
      flexShrink: 0
    }
  }), /*#__PURE__*/React.createElement("span", null, children));
}
Object.assign(__ds_scope, { Alert });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Alert.jsx", error: String((e && e.message) || e) }); }

// components/forms/Button.jsx
try { (() => {
/**
 * Primary interactive action. `primary` = filled accent (viz / submit
 * actions); `secondary` = outlined (homepage link, secondary actions);
 * `ghost` = borderless (tab-adjacent, low-emphasis).
 */
function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  onClick,
  disabled = false,
  href,
  target
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
    textDecoration: "none"
  };
  const variants = {
    primary: {
      background: "var(--accent)",
      color: "var(--text-on-accent)",
      borderColor: "var(--accent)"
    },
    secondary: {
      background: "var(--surface-card)",
      color: "var(--text-primary)",
      borderColor: "var(--border-default)"
    },
    ghost: {
      background: "transparent",
      color: "var(--text-secondary)",
      borderColor: "transparent"
    }
  };
  const style = {
    ...base,
    ...variants[variant]
  };
  const content = /*#__PURE__*/React.createElement(React.Fragment, null, icon && /*#__PURE__*/React.createElement("i", {
    "data-lucide": icon,
    style: {
      width: 14,
      height: 14
    }
  }), children);
  if (href) {
    return /*#__PURE__*/React.createElement("a", {
      href: href,
      target: target,
      rel: "noreferrer",
      style: style
    }, content);
  }
  return /*#__PURE__*/React.createElement("button", {
    onClick: onClick,
    disabled: disabled,
    style: style
  }, content);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Button.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
/** Labeled checkbox — used for "仅可商用" / "仅含失败标注" toggle filters. */
function Checkbox({
  label,
  checked,
  onChange
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      fontSize: "var(--text-sm)",
      color: "var(--text-primary)",
      cursor: "pointer",
      marginTop: 6
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: checked,
    onChange: e => onChange(e.target.checked),
    style: {
      accentColor: "var(--accent)",
      width: 14,
      height: 14
    }
  }), label);
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/SearchInput.jsx
try { (() => {
/** Search field with a leading icon, used at the top of the filter sidebar. */
function SearchInput({
  value,
  onChange,
  placeholder = "搜索名称 / ID"
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative"
    }
  }, /*#__PURE__*/React.createElement("i", {
    "data-lucide": "search",
    style: {
      position: "absolute",
      left: 10,
      top: "50%",
      transform: "translateY(-50%)",
      width: 14,
      height: 14,
      color: "var(--text-tertiary)"
    }
  }), /*#__PURE__*/React.createElement("input", {
    value: value,
    onChange: e => onChange(e.target.value),
    placeholder: placeholder,
    style: {
      width: "100%",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--text-sm)",
      padding: "8px 10px 8px 30px",
      border: "1px solid var(--border-default)",
      borderRadius: "var(--radius-md)",
      color: "var(--text-primary)",
      background: "var(--surface-card)",
      outline: "none"
    }
  }));
}
Object.assign(__ds_scope, { SearchInput });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/SearchInput.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
/** Labeled dropdown used for each facet filter (embodiment, format, provenance, concept). */
function Select({
  label,
  value,
  onChange,
  options
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: "var(--space-3)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-secondary)",
      marginBottom: 4
    }
  }, label), /*#__PURE__*/React.createElement("select", {
    value: value,
    onChange: e => onChange(e.target.value),
    style: {
      width: "100%",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--text-sm)",
      padding: "7px 8px",
      border: "1px solid var(--border-default)",
      borderRadius: "var(--radius-md)",
      background: "var(--surface-card)",
      color: "var(--text-primary)"
    }
  }, options.map(o => /*#__PURE__*/React.createElement("option", {
    key: o.value,
    value: o.value
  }, o.label))));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Slider.jsx
try { (() => {
/** Range slider with live value label — used for min quality score. */
function Slider({
  label,
  value,
  min = 0,
  max = 1,
  step = 0.05,
  onChange,
  format
}) {
  const display = format ? format(value) : value;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-3)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-secondary)",
      marginBottom: 4
    }
  }, label, "\uFF1A", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--text-primary)",
      fontFamily: "var(--font-mono)"
    }
  }, display)), /*#__PURE__*/React.createElement("input", {
    type: "range",
    min: min,
    max: max,
    step: step,
    value: value,
    onChange: e => onChange(parseFloat(e.target.value)),
    style: {
      width: "100%",
      accentColor: "var(--accent)"
    }
  }));
}
Object.assign(__ds_scope, { Slider });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Slider.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
/** Top-level view switch — "数据集" / "覆盖度地图" in the source app. */
function Tabs({
  items,
  active,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8
    }
  }, items.map(it => {
    const isActive = it.key === active;
    return /*#__PURE__*/React.createElement("button", {
      key: it.key,
      onClick: () => onChange(it.key),
      style: {
        fontFamily: "var(--font-sans)",
        fontSize: "var(--text-sm)",
        fontWeight: "var(--weight-semibold)",
        padding: "8px 16px",
        borderRadius: "var(--radius-md)",
        border: isActive ? "1px solid var(--accent)" : "1px solid var(--border-subtle)",
        background: isActive ? "var(--accent)" : "var(--surface-card)",
        color: isActive ? "var(--text-on-accent)" : "var(--text-secondary)",
        cursor: "pointer",
        transition: "all var(--duration-fast) var(--ease-standard)"
      }
    }, it.label);
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// components/overlay/DetailDrawer.jsx
try { (() => {
/** Right-side slide-over — used for the dataset detail panel. Click the
 * scrim or the × to close. */
function DetailDrawer({
  open,
  onClose,
  title,
  subtitle,
  children
}) {
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "fixed",
      inset: 0,
      zIndex: 30,
      display: "flex",
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: "absolute",
      inset: 0,
      background: "var(--surface-overlay-scrim)"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      width: "min(480px, 100%)",
      background: "var(--surface-card)",
      height: "100%",
      overflowY: "auto",
      padding: 28,
      boxShadow: "var(--shadow-2xl)",
      fontFamily: "var(--font-sans)"
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    style: {
      position: "absolute",
      top: 16,
      right: 20,
      border: "none",
      background: "none",
      color: "var(--text-tertiary)",
      fontSize: 20,
      cursor: "pointer",
      lineHeight: 1
    }
  }, "\xD7"), /*#__PURE__*/React.createElement("h2", {
    style: {
      fontSize: "var(--text-h2)",
      fontWeight: "var(--weight-bold)",
      margin: "0 0 2px",
      color: "var(--text-primary)"
    }
  }, title), subtitle && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-xs)",
      color: "var(--text-tertiary)",
      marginBottom: 16,
      fontFamily: "var(--font-mono)"
    }
  }, subtitle), children));
}
Object.assign(__ds_scope, { DetailDrawer });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/overlay/DetailDrawer.jsx", error: String((e && e.message) || e) }); }

// handoff/mini-datahub-integration/web/tailwind.config.js
try { (() => {
/** @type {import('tailwindcss').Config} */
let __ds_default_handoff_mini_datahub_integration_web_tailwind_config_1p3eo4q;
try {
  __ds_default_handoff_mini_datahub_integration_web_tailwind_config_1p3eo4q = {
    darkMode: "class",
    content: ["./index.html", "./src/**/*.{js,jsx}"],
    theme: {
      extend: {
        colors: {
          // Replaced the old indigo `brand` scale with a teal/cyan "accent"
          // scale — matches the Mini DataHub design system's v2 tokens.
          accent: {
            50: "#ecfeff",
            100: "#cffafe",
            200: "#a5f3fc",
            300: "#67e8f9",
            400: "#22d3ee",
            500: "#06b6d4",
            600: "#0891b2",
            700: "#0e7490",
            800: "#155e75",
            900: "#164e63"
          }
        },
        fontFamily: {
          // Space Grotesk for UI/display, IBM Plex Mono for ids/values/code.
          // Both loaded via Google Fonts in index.css.
          sans: ["Space Grotesk", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "PingFang SC", "Microsoft YaHei", "sans-serif"],
          mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"]
        }
      }
    },
    plugins: []
  };
} catch {}
Object.assign(__ds_scope, { __ds_default_handoff_mini_datahub_integration_web_tailwind_config_1p3eo4q });
})(); } catch (e) { __ds_ns.__errors.push({ path: "handoff/mini-datahub-integration/web/tailwind.config.js", error: String((e && e.message) || e) }); }

// ui_kits/data-hub/App.jsx
try { (() => {
const {
  StatCard,
  Tag,
  Tabs,
  SearchInput,
  Select,
  Checkbox,
  Slider,
  DatasetCard,
  DetailDrawer,
  Alert,
  Button,
  CoverageHeatmap
} = window.MiniDataHubDesignSystem_f6abe1;
const {
  STATS,
  FACETS,
  DATASETS,
  COVERAGE_CELLS
} = window.MOCK;
const EMBODIMENT_OPTS = [{
  value: "",
  label: "（不限）"
}, ...FACETS.embodiments.map(e => ({
  value: e,
  label: e
}))];
const FORMAT_OPTS = [{
  value: "",
  label: "（不限）"
}, ...FACETS.formats.map(e => ({
  value: e,
  label: e
}))];
const PROV_OPTS = [{
  value: "",
  label: "（不限）"
}, ...FACETS.provenances.map(e => ({
  value: e,
  label: e
}))];
const CONCEPT_OPTS = [{
  value: "",
  label: "（不限）"
}, ...FACETS.concepts.map(c => ({
  value: c.id,
  label: c.label
}))];
const CONCEPT_LABELS = {
  抓取放置: "pick_place",
  推动: "pushing",
  插入装配: "insertion",
  折叠: "folding",
  开启: "opening",
  堆叠: "stacking",
  导航: "navigation"
};
function fmtNum(n) {
  return n.toLocaleString("en-US");
}
function Sidebar({
  filters,
  setFilter
}) {
  return /*#__PURE__*/React.createElement("aside", {
    style: {
      width: "var(--sidebar-width)",
      flexShrink: 0,
      background: "var(--surface-card)",
      border: "1px solid var(--border-subtle)",
      borderRadius: "var(--radius-xl)",
      padding: 20,
      boxShadow: "var(--shadow-sm)",
      height: "fit-content"
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: "var(--text-h3)",
      fontWeight: "var(--weight-bold)",
      margin: "0 0 14px",
      display: "flex",
      alignItems: "center",
      gap: 6,
      color: "var(--text-primary)"
    }
  }, /*#__PURE__*/React.createElement("i", {
    "data-lucide": "sliders-horizontal",
    style: {
      width: 16,
      height: 16
    }
  }), " \u7B5B\u9009"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement(SearchInput, {
    value: filters.search,
    onChange: v => setFilter("search", v)
  })), /*#__PURE__*/React.createElement(Select, {
    label: "\u4EFB\u52A1\u6982\u5FF5",
    value: filters.concept,
    onChange: v => setFilter("concept", v),
    options: CONCEPT_OPTS
  }), /*#__PURE__*/React.createElement(Select, {
    label: "\u672C\u4F53\u7C7B\u578B",
    value: filters.embodiment,
    onChange: v => setFilter("embodiment", v),
    options: EMBODIMENT_OPTS
  }), /*#__PURE__*/React.createElement(Select, {
    label: "\u6E90\u683C\u5F0F",
    value: filters.format,
    onChange: v => setFilter("format", v),
    options: FORMAT_OPTS
  }), /*#__PURE__*/React.createElement(Select, {
    label: "\u91C7\u96C6\u65B9\u5F0F",
    value: filters.provenance,
    onChange: v => setFilter("provenance", v),
    options: PROV_OPTS
  }), /*#__PURE__*/React.createElement(Checkbox, {
    label: "\u4EC5\u53EF\u5546\u7528",
    checked: filters.commercial_only,
    onChange: v => setFilter("commercial_only", v)
  }), /*#__PURE__*/React.createElement(Checkbox, {
    label: "\u4EC5\u542B\u5931\u8D25\u6807\u6CE8",
    checked: filters.failures_only,
    onChange: v => setFilter("failures_only", v)
  }), /*#__PURE__*/React.createElement(Slider, {
    label: "\u6700\u4F4E\u8D28\u91CF\u5206",
    value: filters.min_quality,
    onChange: v => setFilter("min_quality", v),
    format: v => v.toFixed(2)
  }));
}
function Detail({
  d,
  onClose
}) {
  if (!d) return null;
  return /*#__PURE__*/React.createElement(DetailDrawer, {
    open: !!d,
    onClose: onClose,
    title: d.name,
    subtitle: d.dataset_id
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: 10,
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement(StatCard, {
    label: "\u672C\u4F53",
    value: d.embodiment
  }), /*#__PURE__*/React.createElement(StatCard, {
    label: "\u8F68\u8FF9\u6570",
    value: fmtNum(d.n_episodes)
  }), /*#__PURE__*/React.createElement(StatCard, {
    label: "\u53EF\u5546\u7528",
    value: d.commercial_ok ? "是" : "否"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-secondary)",
      marginBottom: 16,
      lineHeight: 1.8
    }
  }, /*#__PURE__*/React.createElement("div", null, "\u8BB8\u53EF\u8BC1\uFF1A", /*#__PURE__*/React.createElement("code", {
    style: {
      background: "var(--surface-sunken)",
      padding: "2px 6px",
      borderRadius: 4,
      fontFamily: "var(--font-mono)",
      color: "var(--text-primary)"
    }
  }, d.license_spdx), "\u3000 \u6E90\u683C\u5F0F\uFF1A", /*#__PURE__*/React.createElement("code", {
    style: {
      background: "var(--surface-sunken)",
      padding: "2px 6px",
      borderRadius: 4,
      fontFamily: "var(--font-mono)",
      color: "var(--text-primary)"
    }
  }, d.source_format)), /*#__PURE__*/React.createElement("div", null, "\u91C7\u96C6\u65B9\u5F0F\uFF1A", d.provenance_type, "\u3000\u6765\u6E90\uFF1A", d.source), /*#__PURE__*/React.createElement("div", null, "\u8D28\u91CF\u5206\uFF1A", /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      color: "var(--text-primary)",
      fontWeight: 600
    }
  }, d.quality_score?.toFixed(2)), d.quality_tier === "metadata" && /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--text-tertiary)"
    }
  }, " \uFF08\u5143\u6570\u636E\u521D\u7B5B\uFF09"))), !d.commercial_ok && /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(Alert, {
    tone: "warning"
  }, "\u8BE5\u6570\u636E\u96C6\u4E0D\u53EF\u5546\u7528\uFF0C\u8BF7\u52FF\u6DF7\u5165\u5546\u4E1A\u8BAD\u7EC3\u96C6\u3002")), d.action_convention && /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 12,
      fontSize: "var(--text-sm)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      color: "var(--text-primary)"
    }
  }, "\u52A8\u4F5C\u7EA6\u5B9A\uFF1A"), Object.entries(d.action_convention).map(([k, v]) => /*#__PURE__*/React.createElement(Tag, {
    key: k
  }, k, "=", String(v)))), ["tasks", "scenes", "modalities"].map(f => (d[f] || []).length > 0 ? /*#__PURE__*/React.createElement("div", {
    key: f,
    style: {
      marginBottom: 10,
      fontSize: "var(--text-sm)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      color: "var(--text-primary)"
    }
  }, {
    tasks: "任务",
    scenes: "场景",
    modalities: "模态"
  }[f], "\uFF1A"), d[f].map(v => /*#__PURE__*/React.createElement(Tag, {
    key: v,
    tone: "accent"
  }, v))) : null), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginTop: 20
    }
  }, (d.source === "huggingface" || String(d.source_format).includes("lerobot")) && /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    icon: "play",
    href: `https://huggingface.co/spaces/lerobot/visualize_dataset?dataset=${d.dataset_id}`,
    target: "_blank"
  }, "\u5728\u7EBF\u53EF\u89C6\u5316"), d.homepage && /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    icon: "external-link",
    href: d.homepage,
    target: "_blank"
  }, "\u6570\u636E\u96C6\u4E3B\u9875")));
}
function App() {
  const [tab, setTab] = React.useState("list");
  const [selected, setSelected] = React.useState(null);
  const [theme, setTheme] = React.useState("dark");
  const [filters, setFilters] = React.useState({
    search: "",
    embodiment: "",
    format: "",
    provenance: "",
    concept: "",
    commercial_only: false,
    failures_only: false,
    min_quality: 0
  });
  const setFilter = (k, v) => setFilters(f => ({
    ...f,
    [k]: v
  }));
  React.useEffect(() => {
    window.lucide && window.lucide.createIcons();
  });
  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
  }, [theme]);
  const filtered = DATASETS.filter(d => {
    if (filters.search && !`${d.name} ${d.dataset_id}`.toLowerCase().includes(filters.search.toLowerCase())) return false;
    if (filters.embodiment && d.embodiment !== filters.embodiment) return false;
    if (filters.format && d.source_format !== filters.format) return false;
    if (filters.provenance && d.provenance_type !== filters.provenance) return false;
    if (filters.commercial_only && !d.commercial_ok) return false;
    if (filters.failures_only && !d.has_failure_labels) return false;
    if (filters.min_quality && (d.quality_score || 0) < filters.min_quality) return false;
    if (filters.concept) {
      const ids = (d.tasks || []).map(t => CONCEPT_LABELS[t]);
      if (!ids.includes(filters.concept)) return false;
    }
    return true;
  });
  const selectedDataset = DATASETS.find(d => d.dataset_id === selected);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      minHeight: "100vh"
    }
  }, /*#__PURE__*/React.createElement("header", {
    style: {
      background: "var(--surface-inverse)",
      color: "var(--text-on-inverse)",
      padding: "28px 0",
      borderBottom: "1px solid var(--border-subtle)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--content-max-width)",
      margin: "0 auto",
      padding: "0 32px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: "var(--text-h1)",
      fontWeight: 700,
      margin: 0,
      letterSpacing: "var(--tracking-hero)",
      textTransform: "uppercase",
      color: "var(--text-on-inverse)"
    }
  }, "\u673A\u5668\u4EBA DataHub"), /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--gray-400)",
      marginTop: 6,
      fontSize: "var(--text-sm)"
    }
  }, "\u8DE8\u6E90\u805A\u5408 \xB7 \u7EDF\u4E00\u68C0\u7D22 \xB7 \u81EA\u52A8\u8D28\u68C0 \xB7 \u8986\u76D6\u5EA6\u5730\u56FE \u2014\u2014 \u5177\u8EAB\u667A\u80FD\u6570\u636E\u7684\u8054\u90A6\u95E8\u6237")), /*#__PURE__*/React.createElement("button", {
    onClick: () => setTheme(t => t === "dark" ? "light" : "dark"),
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6,
      background: "transparent",
      border: "1px solid var(--border-strong)",
      borderRadius: "var(--radius-md)",
      padding: "7px 12px",
      color: "var(--text-on-inverse)",
      fontSize: "var(--text-xs)",
      fontFamily: "var(--font-sans)",
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement("i", {
    "data-lucide": theme === "dark" ? "sun" : "moon",
    style: {
      width: 14,
      height: 14
    }
  }), theme === "dark" ? "浅色" : "深色"))), /*#__PURE__*/React.createElement("main", {
    style: {
      maxWidth: "var(--content-max-width)",
      margin: "0 auto",
      padding: "24px 32px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: 16,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(StatCard, {
    label: "\u6570\u636E\u96C6\u6570\u91CF",
    value: fmtNum(STATS.n_datasets),
    icon: "database"
  }), /*#__PURE__*/React.createElement(StatCard, {
    label: "\u8F68\u8FF9\u603B\u6570",
    value: fmtNum(STATS.n_episodes),
    icon: "git-branch"
  }), /*#__PURE__*/React.createElement(StatCard, {
    label: "\u603B\u5E27\u6570",
    value: fmtNum(STATS.n_frames),
    icon: "film"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    items: [{
      key: "list",
      label: "数据集"
    }, {
      key: "coverage",
      label: "覆盖度地图"
    }],
    active: tab,
    onChange: setTab
  })), tab === "coverage" ? /*#__PURE__*/React.createElement(CoverageHeatmap, {
    embodiments: FACETS.embodiments,
    concepts: FACETS.concepts,
    cells: COVERAGE_CELLS
  }) : /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 24,
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement(Sidebar, {
    filters: filters,
    setFilter: setFilter
  }), /*#__PURE__*/React.createElement("section", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-secondary)",
      marginBottom: 12
    }
  }, "\u5171 ", filtered.length, " \u4E2A\u6570\u636E\u96C6"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 10
    }
  }, filtered.map(d => /*#__PURE__*/React.createElement(DatasetCard, {
    key: d.dataset_id,
    dataset: d,
    onClick: () => setSelected(d.dataset_id)
  })), filtered.length === 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--text-tertiary)",
      fontSize: "var(--text-sm)",
      padding: "40px 0",
      textAlign: "center"
    }
  }, "\u6CA1\u6709\u7B26\u5408\u6761\u4EF6\u7684\u6570\u636E\u96C6\uFF0C\u8BD5\u8BD5\u653E\u5BBD\u7B5B\u9009\u3002"))))), /*#__PURE__*/React.createElement(Detail, {
    d: selectedDataset,
    onClose: () => setSelected(null)
  }));
}
ReactDOM.createRoot(document.getElementById("root")).render(/*#__PURE__*/React.createElement(App, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/data-hub/App.jsx", error: String((e && e.message) || e) }); }

// ui_kits/data-hub/mock-data.js
try { (() => {
// Fake catalog data standing in for the DuckDB-backed API (hub_data.py / api.py)
// in the source app. Shapes mirror schema.py's DatasetMeta exactly.
// Plain globals (no ES module export) so a bundler-less <script src> works.
window.MOCK = {};
window.MOCK.STATS = {
  n_datasets: 128,
  n_episodes: 46920,
  n_frames: 8412300
};
window.MOCK.FACETS = {
  embodiments: ["single_arm", "bimanual", "humanoid", "mobile", "quadruped"],
  formats: ["lerobot_v3", "rlds", "hdf5", "mcap"],
  provenances: ["teleop", "kinesthetic", "sim", "autonomous", "human_video"],
  concepts: [{
    id: "pick_place",
    label: "抓取放置 / Pick & Place"
  }, {
    id: "insertion",
    label: "插入装配 / Insertion"
  }, {
    id: "pushing",
    label: "推动 / Pushing"
  }, {
    id: "folding",
    label: "折叠 / Folding"
  }, {
    id: "opening",
    label: "开启 / Opening"
  }, {
    id: "stacking",
    label: "堆叠 / Stacking"
  }]
};
window.MOCK.DATASETS = [{
  dataset_id: "lerobot/aloha_sim_insertion_human",
  name: "ALOHA Sim Insertion",
  embodiment: "bimanual",
  source_format: "lerobot_v3",
  commercial_ok: true,
  n_episodes: 400,
  quality_score: 0.91,
  has_failure_labels: true,
  license_spdx: "apache-2.0",
  provenance_type: "teleop",
  source: "huggingface",
  quality_tier: "deep",
  action_convention: {
    space: "joint",
    frame: "base",
    abs_or_delta: "delta",
    units: "rad"
  },
  tasks: ["插入装配"],
  scenes: ["桌面"],
  modalities: ["彩色图像", "本体状态"],
  homepage: "https://huggingface.co/datasets/lerobot/aloha_sim_insertion_human"
}, {
  dataset_id: "lerobot/pusht",
  name: "PushT",
  embodiment: "single_arm",
  source_format: "lerobot_v3",
  commercial_ok: false,
  n_episodes: 206,
  quality_score: 0.74,
  has_failure_labels: false,
  license_spdx: "cc-by-nc-sa-4.0",
  provenance_type: "teleop",
  source: "huggingface",
  quality_tier: "metadata",
  action_convention: {
    space: "end_effector",
    frame: "world",
    abs_or_delta: "abs",
    units: "m"
  },
  tasks: ["推动"],
  scenes: ["桌面"],
  modalities: ["彩色图像", "本体状态"],
  homepage: "https://huggingface.co/datasets/lerobot/pusht"
}, {
  dataset_id: "openx/fractal20220817_data",
  name: "Fractal (RT-1)",
  embodiment: "single_arm",
  source_format: "rlds",
  commercial_ok: true,
  n_episodes: 87212,
  quality_score: 0.68,
  has_failure_labels: false,
  license_spdx: "apache-2.0",
  provenance_type: "teleop",
  source: "openx",
  quality_tier: "metadata",
  action_convention: {
    space: "end_effector",
    frame: "base",
    abs_or_delta: "delta",
    units: "m"
  },
  tasks: ["抓取放置", "开启"],
  scenes: ["厨房", "办公室"],
  modalities: ["彩色图像", "语言"],
  homepage: "https://robotics-transformer1.github.io/"
}, {
  dataset_id: "agibot/agibot_world_beta",
  name: "AgiBot World (beta)",
  embodiment: "humanoid",
  source_format: "hdf5",
  commercial_ok: true,
  n_episodes: 8500,
  quality_score: 0.83,
  has_failure_labels: true,
  license_spdx: "cc-by-4.0",
  provenance_type: "teleop",
  source: "agibot",
  quality_tier: "deep",
  action_convention: {
    space: "joint",
    frame: "base",
    abs_or_delta: "abs",
    units: "rad"
  },
  tasks: ["堆叠", "折叠", "插入装配"],
  scenes: ["家庭", "工厂制造"],
  modalities: ["彩色图像", "深度", "本体状态", "语言"],
  homepage: "https://agibot-world.com/"
}, {
  dataset_id: "robomind/mobile_manip_v2",
  name: "RoboMind Mobile Manip v2",
  embodiment: "mobile",
  source_format: "mcap",
  commercial_ok: false,
  n_episodes: 1120,
  quality_score: 0.55,
  has_failure_labels: true,
  license_spdx: "cc-by-nc-4.0",
  provenance_type: "autonomous",
  source: "robomind",
  quality_tier: "metadata",
  action_convention: {
    space: "base_velocity",
    frame: "world",
    abs_or_delta: "delta",
    units: "m/s"
  },
  tasks: ["导航", "抓取放置"],
  scenes: ["商业场所"],
  modalities: ["彩色图像", "本体状态"],
  homepage: ""
}, {
  dataset_id: "unitree/quadruped_terrain",
  name: "Quadruped Terrain Traversal",
  embodiment: "quadruped",
  source_format: "rlds",
  commercial_ok: true,
  n_episodes: 3040,
  quality_score: 0.79,
  has_failure_labels: false,
  license_spdx: "apache-2.0",
  provenance_type: "sim",
  source: "unitree",
  quality_tier: "metadata",
  action_convention: {
    space: "joint",
    frame: "base",
    abs_or_delta: "delta",
    units: "rad"
  },
  tasks: ["导航"],
  scenes: ["工厂制造"],
  modalities: ["本体状态", "触觉力觉"],
  homepage: ""
}];
window.MOCK.COVERAGE_CELLS = [{
  embodiment: "single_arm",
  concept: "pick_place",
  count: 42
}, {
  embodiment: "single_arm",
  concept: "pushing",
  count: 18
}, {
  embodiment: "single_arm",
  concept: "opening",
  count: 6
}, {
  embodiment: "bimanual",
  concept: "insertion",
  count: 31
}, {
  embodiment: "bimanual",
  concept: "folding",
  count: 9
}, {
  embodiment: "bimanual",
  concept: "stacking",
  count: 4
}, {
  embodiment: "humanoid",
  concept: "stacking",
  count: 12
}, {
  embodiment: "humanoid",
  concept: "folding",
  count: 7
}, {
  embodiment: "mobile",
  concept: "pick_place",
  count: 3
}, {
  embodiment: "quadruped",
  concept: "pick_place",
  count: 0
}];
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/data-hub/mock-data.js", error: String((e && e.message) || e) }); }

__ds_ns.CoverageHeatmap = __ds_scope.CoverageHeatmap;

__ds_ns.DatasetCard = __ds_scope.DatasetCard;

__ds_ns.StatCard = __ds_scope.StatCard;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Alert = __ds_scope.Alert;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.SearchInput = __ds_scope.SearchInput;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Slider = __ds_scope.Slider;

__ds_ns.Tabs = __ds_scope.Tabs;

__ds_ns.DetailDrawer = __ds_scope.DetailDrawer;

})();
