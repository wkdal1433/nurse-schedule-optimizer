import React from 'react';
import { AppleDesign } from '../../styles/AppleDesignSystem';

interface AppleCardProps {
  children: React.ReactNode;
  padding?: 'small' | 'medium' | 'large';
  elevated?: boolean;
  interactive?: boolean;
  onClick?: () => void;
  selected?: boolean;
}

const AppleCard: React.FC<AppleCardProps> = ({
  children,
  padding = 'medium',
  elevated = false,
  interactive = false,
  onClick,
  selected = false,
}) => {
  const getPaddingValue = () => {
    const paddingMap = {
      small: AppleDesign.spacing.md,
      medium: AppleDesign.spacing.lg,
      large: AppleDesign.spacing.xl,
    };
    return paddingMap[padding];
  };

  const cardStyles: React.CSSProperties = {
    background: selected
      ? `linear-gradient(135deg, ${AppleDesign.colors.systemBlue}15, ${AppleDesign.colors.systemBlue}08)`
      : AppleDesign.colors.systemBackground,
    border: selected
      ? `2px solid ${AppleDesign.colors.systemBlue}`
      : `1px solid ${AppleDesign.colors.systemGray5}`,
    borderRadius: AppleDesign.borderRadius.large,
    padding: getPaddingValue(),
    boxShadow: elevated
      ? AppleDesign.shadows.large
      : AppleDesign.shadows.small,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    transition: 'all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
    cursor: interactive ? 'pointer' : 'default',
    position: 'relative',
    overflow: 'hidden',
  };

  const handleClick = () => {
    if (interactive && onClick) {
      // iOS 햅틱 피드백
      if (window.navigator.vibrate) {
        window.navigator.vibrate(10);
      }
      onClick();
    }
  };

  return (
    <div
      style={cardStyles}
      onClick={handleClick}
      onMouseEnter={(e) => {
        if (interactive) {
          (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
          (e.currentTarget as HTMLElement).style.boxShadow = AppleDesign.shadows.xlarge;
        }
      }}
      onMouseLeave={(e) => {
        if (interactive) {
          (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
          (e.currentTarget as HTMLElement).style.boxShadow = elevated
            ? AppleDesign.shadows.large
            : AppleDesign.shadows.small;
        }
      }}
      onMouseDown={(e) => {
        if (interactive) {
          (e.currentTarget as HTMLElement).style.transform = 'translateY(-1px) scale(0.98)';
        }
      }}
      onMouseUp={(e) => {
        if (interactive) {
          (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px) scale(1)';
        }
      }}
    >
      {selected && (
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '16px',
            color: AppleDesign.colors.systemBlue,
            fontSize: '20px',
            fontWeight: '600',
          }}
        >
          ✓
        </div>
      )}
      {children}
    </div>
  );
};

export default AppleCard;