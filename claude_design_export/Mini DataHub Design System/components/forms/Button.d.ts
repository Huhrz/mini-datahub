export interface ButtonProps {
  /** Button label / content */
  children: React.ReactNode;
  /** Visual style */
  variant?: "primary" | "secondary" | "ghost";
  /** Compact vs default sizing */
  size?: "sm" | "md";
  /** Optional Lucide icon name rendered before the label */
  icon?: string;
  onClick?: () => void;
  disabled?: boolean;
  href?: string;
  target?: string;
}
