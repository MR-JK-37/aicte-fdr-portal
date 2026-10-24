import React, { useId } from 'react';
import clsx from 'clsx';
import { Icon } from './Icon';

interface FieldWrapperProps {
  label?: string;
  helperText?: string;
  errorText?: string;
  id?: string;
  children: (id: string, describedBy: string | undefined) => React.ReactNode;
}

function FieldWrapper({ label, helperText, errorText, id, children }: FieldWrapperProps) {
  const autoId = useId();
  const fieldId = id ?? autoId;
  const helperId = (errorText ?? helperText) ? `${fieldId}-helper` : undefined;
  return (
    <div className="ds-field">
      {label && <label className="ds-field__label" htmlFor={fieldId}>{label}</label>}
      {children(fieldId, helperId)}
      {errorText ? (
        <span id={helperId} className="ds-field__helper ds-field__helper--error" role="alert">{errorText}</span>
      ) : helperText ? (
        <span id={helperId} className="ds-field__helper">{helperText}</span>
      ) : null}
    </div>
  );
}

export interface TextInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label?: string;
  helperText?: string;
  errorText?: string;
  id?: string;
  /** ₹ amount field: shows the currency prefix and uses tabular numerals, per DESIGN_SPEC §3. */
  amount?: boolean;
  leadingIcon?: React.ComponentProps<typeof Icon>['name'];
}

export function TextInput({ label, helperText, errorText, id, amount, leadingIcon, className, ...rest }: TextInputProps) {
  return (
    <FieldWrapper label={label} helperText={helperText} errorText={errorText} id={id}>
      {(fieldId, describedBy) => (
        <div className={clsx('ds-input-wrap', errorText && 'ds-input-wrap--error', className)}>
          {leadingIcon && <Icon name={leadingIcon} size={16} />}
          {amount && <span className="ds-input-wrap__affix">₹</span>}
          <input
            id={fieldId}
            aria-invalid={!!errorText}
            aria-describedby={describedBy}
            className={amount ? 'num' : undefined}
            inputMode={amount ? 'decimal' : rest.inputMode}
            {...rest}
          />
        </div>
      )}
    </FieldWrapper>
  );
}

export interface SearchInputProps extends Omit<TextInputProps, 'leadingIcon' | 'amount' | 'type'> {}

export function SearchInput(props: SearchInputProps) {
  return <TextInput type="search" leadingIcon="search" placeholder="Search" {...props} />;
}

export interface SelectOption { value: string; label: string }
export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  label?: string;
  helperText?: string;
  errorText?: string;
  id?: string;
  options: SelectOption[];
}

export function Select({ label, helperText, errorText, id, options, className, ...rest }: SelectProps) {
  return (
    <FieldWrapper label={label} helperText={helperText} errorText={errorText} id={id}>
      {(fieldId, describedBy) => (
        <div className={clsx('ds-input-wrap', errorText && 'ds-input-wrap--error', className)}>
          <select id={fieldId} aria-invalid={!!errorText} aria-describedby={describedBy} {...rest}>
            {options.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      )}
    </FieldWrapper>
  );
}
