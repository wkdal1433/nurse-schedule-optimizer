import React from 'react';
import { AppleDesign } from '../../styles/AppleDesignSystem';

interface AppleInputProps {
  type?: 'text' | 'number' | 'email' | 'tel';
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: boolean;
  icon?: React.ReactNode;
  label?: string;
}

const AppleInput: React.FC<AppleInputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled = false,
  error = false,
  icon,
  label,
}) => {
  const inputContainerStyles: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: AppleDesign.spacing.sm,
  };

  const labelStyles: React.CSSProperties = {
    ...AppleDesign.typography.subheadline,
    color: AppleDesign.colors.secondaryLabel,
    fontWeight: '500',
  };

  const inputWrapperStyles: React.CSSProperties = {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  };

  const inputStyles: React.CSSProperties = {
    width: '100%',
    padding: icon ? `${AppleDesign.spacing.md} ${AppleDesign.spacing.md} ${AppleDesign.spacing.md} 48px` : AppleDesign.spacing.md,
    border: `1px solid ${error ? AppleDesign.colors.systemRed : AppleDesign.colors.systemGray4}`,
    borderRadius: AppleDesign.borderRadius.medium,
    background: AppleDesign.colors.systemBackground,
    color: AppleDesign.colors.label,
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif',
    ...AppleDesign.typography.body,
    outline: 'none',
    transition: 'all 0.2s ease',
    minHeight: '44px',
    WebkitAppearance: 'none',
    boxSizing: 'border-box',
  };

  const iconStyles: React.CSSProperties = {
    position: 'absolute',
    left: AppleDesign.spacing.md,
    color: AppleDesign.colors.systemGray,
    fontSize: '16px',
    zIndex: 1,
    pointerEvents: 'none',
  };

  const focusStyles = {
    borderColor: AppleDesign.colors.systemBlue,
    boxShadow: `0 0 0 3px ${AppleDesign.colors.systemBlue}20`,
  };

  return (
    <div style={inputContainerStyles}>
      {label && <label style={labelStyles}>{label}</label>}
      <div style={inputWrapperStyles}>
        {icon && <div style={iconStyles}>{icon}</div>}
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          style={inputStyles}
          onFocus={(e) => {
            Object.assign(e.target.style, focusStyles);
          }}
          onBlur={(e) => {
            e.target.style.borderColor = error ? AppleDesign.colors.systemRed : AppleDesign.colors.systemGray4;
            e.target.style.boxShadow = 'none';
          }}
          onMouseEnter={(e) => {
            if (!disabled && e.target instanceof HTMLInputElement) {
              e.target.style.borderColor = AppleDesign.colors.systemGray3;
            }
          }}
          onMouseLeave={(e) => {
            if (document.activeElement !== e.target && e.target instanceof HTMLInputElement) {
              e.target.style.borderColor = error ? AppleDesign.colors.systemRed : AppleDesign.colors.systemGray4;
            }
          }}
        />
      </div>
    </div>
  );
};

export default AppleInput;