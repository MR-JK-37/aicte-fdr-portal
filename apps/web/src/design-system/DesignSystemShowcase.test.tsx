import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DesignSystemShowcase } from './DesignSystemShowcase';

describe('DesignSystemShowcase', () => {
  it('renders every primitive without throwing', () => {
    render(<DesignSystemShowcase />);
    expect(screen.getByText('Buttons')).toBeTruthy();
    expect(screen.getByText('Evidence-attribute chips')).toBeTruthy();
    expect(screen.getByText('Status badges')).toBeTruthy();
    expect(screen.getByText('Data-view states')).toBeTruthy();
  });
});
