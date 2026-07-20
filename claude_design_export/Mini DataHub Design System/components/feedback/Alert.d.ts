export interface AlertProps {
  children: React.ReactNode;
  tone?: "warning" | "danger" | "info";
  icon?: string;
}
