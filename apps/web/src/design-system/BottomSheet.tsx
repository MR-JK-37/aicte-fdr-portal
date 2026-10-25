import React from 'react';
import clsx from 'clsx';

export interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

/**
 * BottomSheet: rounded top 28px, grabber, blurred and dimmed scrim backdrop.
 * (DESIGN_SPEC §5.10 / G-24).
 */
export const BottomSheet: React.FC<BottomSheetProps> = ({
  open,
  onClose,
  children,
  className = '',
}) => {
  if (!open) return null;

  return (
    <>
      <div
        data-testid="bottom-sheet-scrim"
        className="scrim"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        data-testid="bottom-sheet"
        className={clsx('sheet', className)}
      >
        <div data-testid="sheet-grabber" className="sheet-grabber" />
        {children}
      </div>
    </>
  );
};
