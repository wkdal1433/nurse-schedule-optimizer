/**
 * Employee Management Hook
 * Single Responsibility: Employee state management and operations
 * Open/Closed: Easy to extend with new employee features
 * Interface Segregation: Focused on employee-specific operations
 * Dependency Inversion: Uses rolesAPI abstraction
 */

import { useState, useEffect } from 'react';
import { rolesAPI, EmployeeRoleInfo } from '../../../services/api';

export interface EmployeeFormData extends Partial<EmployeeRoleInfo> {
  // Specific form fields for employee updates
}

export interface UseEmployeesReturn {
  state: {
    employees: EmployeeRoleInfo[];
    selectedEmployee: EmployeeRoleInfo | null;
    showForm: boolean;
    formData: EmployeeFormData;
    loading: boolean;
  };
  actions: {
    loadEmployees: () => Promise<void>;
    selectEmployee: (employee: EmployeeRoleInfo) => void;
    updateEmployee: () => Promise<void>;
    setFormData: (data: EmployeeFormData) => void;
    setShowForm: (show: boolean) => void;
    resetForm: () => void;
  };
  utils: {
    getRoleDisplayName: (role: string) => string;
    getEmploymentTypeDisplayName: (type: string) => string;
  };
}

const roleDisplayNames: Record<string, string> = {
  'head_nurse': '수간호사',
  'charge_nurse': '책임간호사',
  'staff_nurse': '일반간호사',
  'new_nurse': '신입간호사',
  'education_coordinator': '교육담당자'
};

const employmentTypeNames: Record<string, string> = {
  'full_time': '정규직',
  'part_time': '시간제'
};

export const useEmployees = (wardId: number): UseEmployeesReturn => {
  const [employees, setEmployees] = useState<EmployeeRoleInfo[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeRoleInfo | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<EmployeeFormData>({});
  const [loading, setLoading] = useState(false);

  const loadEmployees = async () => {
    setLoading(true);
    try {
      const response = await rolesAPI.getEmployeesByWard(wardId);
      setEmployees(response.data);
    } catch (error) {
      console.error('직원 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectEmployee = (employee: EmployeeRoleInfo) => {
    setSelectedEmployee(employee);
    setFormData({
      role: employee.role,
      employment_type: employee.employment_type,
      allowed_shifts: employee.allowed_shifts,
      max_hours_per_week: employee.max_hours_per_week,
      max_days_per_week: employee.max_days_per_week,
      can_work_alone: employee.can_work_alone,
      requires_supervision: employee.requires_supervision,
      can_supervise: employee.can_supervise,
      specialization: employee.specialization
    });
    setShowForm(true);
  };

  const updateEmployee = async () => {
    if (!selectedEmployee || !formData) return;
    
    setLoading(true);
    try {
      await rolesAPI.updateEmployeeRole(selectedEmployee.employee_id, formData);
      await loadEmployees();
      resetForm();
      alert('직원 역할 정보가 업데이트되었습니다.');
    } catch (error) {
      console.error('직원 업데이트 실패:', error);
      alert('직원 정보 업데이트에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setShowForm(false);
    setSelectedEmployee(null);
    setFormData({});
  };

  const getRoleDisplayName = (role: string) => {
    return roleDisplayNames[role] || role;
  };

  const getEmploymentTypeDisplayName = (type: string) => {
    return employmentTypeNames[type] || type;
  };

  // Load employees when wardId changes
  useEffect(() => {
    loadEmployees();
  }, [wardId]);

  return {
    state: {
      employees,
      selectedEmployee,
      showForm,
      formData,
      loading
    },
    actions: {
      loadEmployees,
      selectEmployee,
      updateEmployee,
      setFormData,
      setShowForm,
      resetForm
    },
    utils: {
      getRoleDisplayName,
      getEmploymentTypeDisplayName
    }
  };
};