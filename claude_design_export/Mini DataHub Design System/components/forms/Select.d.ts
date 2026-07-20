export interface SelectOption {
  value: string;
  label: string;
}
export interface SelectProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: SelectOption[];
}
