/**
 * Role Management 모듈 타입 정의
 * Single Responsibility: 타입 정의와 인터페이스만 담당
 * Open/Closed: Easy to add new types without modifying existing ones
 * Interface Segregation: Clean separation of type definitions by domain
 * Dependency Inversion: Provides type abstractions for the module
 */

export interface RoleManagementProps {
  wardId?: number;
}

export type TabType = 'employees' | 'constraints' | 'supervision' | 'employment';

export interface RoleManagementState {
  activeTab: TabType;
  loading: boolean;
}

// Base component props for consistency
export interface BaseManagementProps {
  wardId: number;
  isVisible: boolean;
}

// Form action states
export interface BaseFormState {
  showForm: boolean;
  loading: boolean;
}

// Common form actions
export interface BaseFormActions<T> {
  setShowForm: (show: boolean) => void;
  setFormData: (data: T) => void;
  resetForm: () => void;
}

// Loading operations interface
export interface BaseLoadActions {
  loading: boolean;
}

// Re-export from API services for convenience
export type {
  EmployeeRoleInfo,
  RoleConstraint,
  SupervisionPair,
  EmploymentTypeRule
} from '../../../services/api';

// Utility type for display name functions
export type DisplayNameFunction = (key: string) => string;

// Array field update helper type
export type ArrayFieldUpdater<T> = (field: keyof T, value: string) => void;