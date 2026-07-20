export interface SliderProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (v: number) => void;
  /** Formats the value for display, e.g. v => v.toFixed(2) */
  format?: (v: number) => string;
}
