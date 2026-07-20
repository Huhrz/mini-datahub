Dataset list-item card — name, id, quality score, and facet tags. Click opens the detail drawer.

```jsx
<DatasetCard dataset={{
  dataset_id: "lerobot/pusht", name: "PushT", embodiment: "single_arm",
  source_format: "lerobot_v3", commercial_ok: true, n_episodes: 206,
  quality_score: 0.82, has_failure_labels: false,
}} onClick={() => setSelected(id)} />
```
