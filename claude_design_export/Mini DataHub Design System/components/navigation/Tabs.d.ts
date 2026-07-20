export interface TabItem {
  key: string;
  label: string;
}
export interface TabsProps {
  items: TabItem[];
  active: string;
  onChange: (key: string) => void;
}
