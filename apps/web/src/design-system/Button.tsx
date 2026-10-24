import React from 'react';
import clsx from 'clsx';

export type ButtonVariant = 'filled' | 'tonal' | 'outline' | 'text' | 'destructive';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /** Icon-only button: square, round, requires `aria-label`. */
  iconOnly?: boolean;
}

export function Button({ variant = 'filled', iconOnly, className, ...rest }: ButtonProps) {
  if (iconOnly && !rest['aria-label'] && import.meta.env.DEV) {
    // Fail loud in dev rather than ship an unlabelled icon button (WCAG 2.2 target size + name requirement).
    // eslint-disable-next-line no-console
    console.warn('Icon-only <Button> is missing aria-label');
  }
  return (
    <button
      className={clsx('ds-btn', `ds-btn--${variant}`, iconOnly && 'ds-btn--icon', className)}
      {...rest}
    />
  );
}
