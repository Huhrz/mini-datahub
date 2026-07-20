Range slider with a live value readout — used for the min-quality-score filter.

```jsx
<Slider label="最低质量分" value={q} min={0} max={1} step={0.05}
  onChange={setQ} format={(v) => v.toFixed(2)} />
```
