import React from 'react';
import clsx from 'clsx';

export type ButtonVariant =
  | 'primary'
  | 'accent'
  | 'soft'
  | 'danger-soft'
  | 'danger'
  | 'filled'
  | 'tonal'
  | 'outline'
  | 'text'
  | 'destructive';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /** Icon-only button: circular, requires `aria-label`. */
  iconOnly?: boolean;
  block?: boolean;
  compact?: boolean;
}

export function Button({
  variant = 'primary',
  iconOnly,
  block,
  compact,
  className,
  ...rest
}: ButtonProps) {
  if (iconOnly && !rest['aria-label'] && import.meta.env?.DEV) {
    // Fail loud in dev rather than ship an unlabelled icon button (WCAG 2.2 name requirement)
    // eslint-disable-next-line no-console
    console.warn('Icon-only <Button> is missing aria-label');
  }

  // Map legacy names to reference classes
  let variantClass = 'btn-primary';
  if (variant === 'primary' || variant === 'filled') variantClass = 'btn-primary';
  else if (variant === 'accent') variantClass = 'btn-accent';
  else if (variant === 'soft' || variant === 'tonal') variantClass = 'btn-soft';
  else if (variant === 'danger-soft' || variant === 'destructive') variantClass = 'btn-danger-soft';
  else if (variant === 'danger') variantClass = 'btn-danger';
  else if (variant === 'outline') variantClass = 'btn-soft';
  else if (variant === 'text') variantClass = 'btn-soft';

  return (
    <button
      className={clsx(
        'btn',
        variantClass,
        iconOnly && (compact ? 'btn-icon-compact' : 'btn-icon'),
        block && 'btn-block',
        compact && 'btn-compact',
        className
      )}
      {...rest}
    />
  );
}
