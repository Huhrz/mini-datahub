Button reference — primary / secondary / ghost, with icon.

```jsx
<Button variant="primary" icon="play">在线可视化</Button>
<Button variant="secondary" icon="link" href="https://example.com" target="_blank">数据集主页</Button>
<Button variant="ghost" size="sm">取消</Button>
```

Variants: `primary` (filled accent, main CTA), `secondary` (outlined), `ghost` (borderless, low emphasis). `size`: `sm` | `md`. `icon` accepts any Lucide icon name (rendered via `data-lucide`, requires the Lucide CDN script + `lucide.createIcons()`).
