/**
 * Constraints Management Hook
 * Single Responsibility: Role constraint state management and operations
 * Open/Closed: Easy to extend with new constraint features
 * Interface Segregation: Focused on constraint-specific operations
 * Dependency Inversion: Uses rolesAPI abstraction
 */

import { useState, useEffect } from 'react';
import { rolesAPI, RoleConstraint } from '../../../services/api';

export type ConstraintFormData = Omit<RoleConstraint, 'id'>;

export interface UseConstraintsReturn {
  state: {
    constraints: RoleConstraint[];
    showForm: boolean;
    formData: ConstraintFormData;
    loading: boolean;
  };
  actions: {
    loadConstraints: () => Promise<void>;
    createConstraint: () => Promise<void>;
    setFormData: (data: ConstraintFormData) => void;
    setShowForm: (show: boolean) => void;
    resetForm: () => void;
    updateArrayField: (field: keyof ConstraintFormData, value: string) => void;
  };
  utils: {
    getRoleDisplayName: (role: string) => string;
  };
}

const createDefaultConstraint = (wardId: number): ConstraintFormData => ({
  role: 'staff_nurse',
  ward_id: wardId,
  allowed_shifts: ['day', 'evening', 'night'],
  forbidden_shifts: [],
  min_per_shift: 1,
  max_per_shift: 10,
  requires_pairing_with_roles: [],
  cannot_work_with_roles: [],
  must_have_supervisor: false,
  can_be_sole_charge: true
});

const roleDisplayNames: Record<string, string> = {
  'head_nurse': '수간호사',
  'charge_nurse': '책임간호사',
  'staff_nurse': '일반간호사',
  'new_nurse': '신입간호사',
  'education_coordinator': '교육담당자'
};

export const useConstraints = (wardId: number): UseConstraintsReturn => {
  const [constraints, setConstraints] = useState<RoleConstraint[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ConstraintFormData>(createDefaultConstraint(wardId));
  const [loading, setLoading] = useState(false);

  const loadConstraints = async () => {
    setLoading(true);
    try {
      const response = await rolesAPI.getRoleConstraints(wardId);
      setConstraints(response.data);
    } catch (error) {
      console.error('역할 제약조건 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const createConstraint = async () => {
    setLoading(true);
    try {
      await rolesAPI.createRoleConstraint(formData);
      await loadConstraints();
      resetForm();
      alert('역할 제약조건이 생성되었습니다.');
    } catch (error) {
      console.error('제약조건 생성 실패:', error);
      alert('제약조건 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const updateArrayField = (field: keyof ConstraintFormData, value: string) => {
    const array = value.split(',').map(s => s.trim()).filter(s => s);
    setFormData({ ...formData, [field]: array });
  };

  const resetForm = () => {
    setShowForm(false);
    setFormData(createDefaultConstraint(wardId));
  };

  const getRoleDisplayName = (role: string) => {
    return roleDisplayNames[role] || role;
  };

  // Load constraints when wardId changes
  useEffect(() => {
    loadConstraints();
  }, [wardId]);

  // Update formData wardId when prop changes
  useEffect(() => {
    setFormData(prev => ({ ...prev, ward_id: wardId }));
  }, [wardId]);

  return {
    state: {
      constraints,
      showForm,
      formData,
      loading
    },
    actions: {
      loadConstraints,
      createConstraint,
      setFormData,
      setShowForm,
      resetForm,
      updateArrayField
    },
    utils: {
      getRoleDisplayName
    }
  };
};