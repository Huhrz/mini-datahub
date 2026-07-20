export interface HeatmapCell {
  embodiment: string;
  concept: string;
  count: number;
}
export interface CoverageHeatmapProps {
  embodiments: string[];
  concepts: { id: string; label: string }[];
  cells: HeatmapCell[];
}
