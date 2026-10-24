import React from 'react';
import clsx from 'clsx';

export interface ToolbarProps extends React.HTMLAttributes<HTMLDivElement> {
  tinted?: boolean;
}

/** Top toolbar — navigation/control layer, Liquid Glass per DESIGN_SPEC §6. */
export function Toolbar({ tinted, className, children, ...rest }: ToolbarProps) {
  return (
    <div className={clsx('ds-toolbar glass', tinted && 'glass--violet', className)} {...rest}>
      {children}
    </div>
  );
}
