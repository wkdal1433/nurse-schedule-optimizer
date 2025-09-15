/**
 * Role Management Module Exports
 * Single Responsibility: Module interface and export management
 * Open/Closed: Easy to add new exports without breaking existing imports
 * Interface Segregation: Clean separation of public API
 * Dependency Inversion: Provides abstractions for external use
 */

// Main component export
export { default as RoleManagement } from './RoleManagementNew';
export { default } from './RoleManagementNew';

// Types export
export * from './types';

// Hook exports for external use if needed
export { useRoleManagement } from './hooks/useRoleManagement';
export { useEmployees } from './hooks/useEmployees';
export { useConstraints } from './hooks/useConstraints';
export { useSupervision } from './hooks/useSupervision';
export { useEmployment } from './hooks/useEmployment';

// Component exports for external use if needed
export { default as EmployeeManagement } from './components/EmployeeManagement';
export { default as ConstraintManagement } from './components/ConstraintManagement';
export { default as SupervisionManagement } from './components/SupervisionManagement';
export { default as EmploymentManagement } from './components/EmploymentManagement';

// Type exports for hook return types
export type { UseRoleManagementReturn } from './hooks/useRoleManagement';
export type { UseEmployeesReturn, EmployeeFormData } from './hooks/useEmployees';
export type { UseConstraintsReturn, ConstraintFormData } from './hooks/useConstraints';
export type { UseSupervisionReturn, SupervisionFormData } from './hooks/useSupervision';
export type { UseEmploymentReturn, EmploymentFormData } from './hooks/useEmployment';