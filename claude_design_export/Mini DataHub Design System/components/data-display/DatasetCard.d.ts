export interface DatasetSummary {
  dataset_id: string;
  name: string;
  embodiment: string;
  source_format: string;
  commercial_ok: boolean;
  n_episodes: number;
  quality_score?: number;
  has_failure_labels?: boolean;
}
export interface DatasetCardProps {
  dataset: DatasetSummary;
  onClick?: () => void;
}
