import React from 'react';
import clsx from 'clsx';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
  group?: boolean;
}

/**
 * Solid content surface with 20px radius and soft shadow, no 1px border (DESIGN_SPEC §4–§6).
 */
export function Card({ elevated, group, className, ...rest }: CardProps) {
  return (
    <div
      className={clsx(group ? 'card-group' : 'card', elevated && 'card-elevated', className)}
      {...rest}
    />
  );
}
