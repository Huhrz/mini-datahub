Right-side slide-over panel for the dataset detail view. Scrim click or × closes it.

```jsx
<DetailDrawer open={!!selected} onClose={() => setSelected(null)}
  title="ALOHA Sim Insertion" subtitle="lerobot/aloha_sim_insertion_human">
  ...detail content...
</DetailDrawer>
```
