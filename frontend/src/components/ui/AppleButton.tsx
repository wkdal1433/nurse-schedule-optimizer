import React from 'react';
import { AppleDesign } from '../../styles/AppleDesignSystem';

interface AppleButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'destructive';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  fullWidth?: boolean;
  icon?: React.ReactNode;
}

const AppleButton: React.FC<AppleButtonProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  onClick,
  fullWidth = false,
  icon,
}) => {
  const getButtonStyles = () => {
    const baseStyles = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: icon ? '8px' : '0',
      border: 'none',
      borderRadius: AppleDesign.borderRadius.medium,
      fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif',
      fontWeight: '600',
      cursor: disabled ? 'not-allowed' : 'pointer',
      transition: 'all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
      outline: 'none',
      position: 'relative' as const,
      overflow: 'hidden' as const,
      width: fullWidth ? '100%' : 'auto',
      opacity: disabled ? 0.6 : 1,
      touchAction: 'manipulation' as const,
      WebkitTapHighlightColor: 'transparent',
    };

    const sizeStyles = {
      small: {
        padding: '8px 16px',
        ...AppleDesign.typography.footnote,
        minHeight: '32px',
      },
      medium: {
        padding: '12px 20px',
        ...AppleDesign.typography.body,
        minHeight: '44px',
      },
      large: {
        padding: '16px 24px',
        ...AppleDesign.typography.title3,
        minHeight: '56px',
      },
    };

    const variantStyles = {
      primary: {
        background: AppleDesign.colors.systemBlue,
        color: 'white',
        boxShadow: AppleDesign.shadows.medium,
      },
      secondary: {
        background: AppleDesign.colors.secondarySystemGroupedBackground,
        color: AppleDesign.colors.systemBlue,
        border: `1px solid ${AppleDesign.colors.systemGray4}`,
        boxShadow: AppleDesign.shadows.small,
      },
      destructive: {
        background: AppleDesign.colors.systemRed,
        color: 'white',
        boxShadow: AppleDesign.shadows.medium,
      },
    };

    return {
      ...baseStyles,
      ...sizeStyles[size],
      ...variantStyles[variant],
    };
  };

  const handleClick = () => {
    if (!disabled && !loading && onClick) {
      // iOS 햅틱 피드백 시뮬레이션
      if (window.navigator.vibrate) {
        window.navigator.vibrate(10);
      }
      onClick();
    }
  };

  return (
    <button
      style={getButtonStyles()}
      onClick={handleClick}
      disabled={disabled || loading}
      onMouseDown={(e) => {
        if (!disabled) {
          (e.target as HTMLElement).style.transform = 'scale(0.97)';
        }
      }}
      onMouseUp={(e) => {
        (e.target as HTMLElement).style.transform = 'scale(1)';
      }}
      onMouseLeave={(e) => {
        (e.target as HTMLElement).style.transform = 'scale(1)';
      }}
    >
      {loading ? (
        <div
          style={{
            width: '20px',
            height: '20px',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '50%',
            borderTop: '2px solid white',
            animation: 'spin 1s linear infinite',
          }}
        />
      ) : (
        <>
          {icon}
          {children}
        </>
      )}

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
};

export default AppleButton;