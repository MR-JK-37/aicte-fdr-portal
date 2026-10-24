import React from 'react';
import clsx from 'clsx';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

/** Solid content surface — never glass (DESIGN_SPEC §6: glass is nav/control layer only). */
export function Card({ elevated, className, ...rest }: CardProps) {
  return <div className={clsx('ds-card', elevated && 'ds-card--elevated', className)} {...rest} />;
}
