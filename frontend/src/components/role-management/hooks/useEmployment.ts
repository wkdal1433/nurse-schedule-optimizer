/**
 * Employment Rules Management Hook
 * Single Responsibility: Employment rule state management and operations
 * Open/Closed: Easy to extend with new employment features
 * Interface Segregation: Focused on employment-specific operations
 * Dependency Inversion: Uses rolesAPI abstraction
 */

import { useState, useEffect } from 'react';
import { rolesAPI, EmploymentTypeRule } from '../../../services/api';

export type EmploymentFormData = Omit<EmploymentTypeRule, 'id'>;

export interface UseEmploymentReturn {
  state: {
    rules: EmploymentTypeRule[];
    showForm: boolean;
    formData: EmploymentFormData;
    loading: boolean;
  };
  actions: {
    loadRules: () => Promise<void>;
    createRule: () => Promise<void>;
    setFormData: (data: EmploymentFormData) => void;
    setShowForm: (show: boolean) => void;
    resetForm: () => void;
    updateArrayField: (field: keyof EmploymentFormData, value: string) => void;
  };
  utils: {
    getEmploymentTypeDisplayName: (type: string) => string;
  };
}

const createDefaultRule = (wardId: number): EmploymentFormData => ({
  employment_type: 'full_time',
  ward_id: wardId,
  max_hours_per_day: 8,
  max_hours_per_week: 40,
  max_days_per_week: 5,
  max_consecutive_days: 5,
  allowed_shift_types: ['day', 'evening', 'night'],
  forbidden_shift_types: [],
  weekend_work_allowed: true,
  night_shift_allowed: true,
  holiday_work_allowed: true,
  scheduling_priority: 5
});

const employmentTypeNames: Record<string, string> = {
  'full_time': '정규직',
  'part_time': '시간제'
};

export const useEmployment = (wardId: number): UseEmploymentReturn => {
  const [rules, setRules] = useState<EmploymentTypeRule[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<EmploymentFormData>(createDefaultRule(wardId));
  const [loading, setLoading] = useState(false);

  const loadRules = async () => {
    setLoading(true);
    try {
      const response = await rolesAPI.getEmploymentTypeRules(undefined, wardId);
      setRules(response.data);
    } catch (error) {
      console.error('고용형태 규칙 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const createRule = async () => {
    setLoading(true);
    try {
      await rolesAPI.createEmploymentTypeRule(formData);
      await loadRules();
      resetForm();
      alert('고용형태 규칙이 생성되었습니다.');
    } catch (error) {
      console.error('고용형태 규칙 생성 실패:', error);
      alert('고용형태 규칙 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const updateArrayField = (field: keyof EmploymentFormData, value: string) => {
    const array = value.split(',').map(s => s.trim()).filter(s => s);
    setFormData({ ...formData, [field]: array });
  };

  const resetForm = () => {
    setShowForm(false);
    setFormData(createDefaultRule(wardId));
  };

  const getEmploymentTypeDisplayName = (type: string) => {
    return employmentTypeNames[type] || type;
  };

  // Load rules when wardId changes
  useEffect(() => {
    loadRules();
  }, [wardId]);

  // Update formData wardId when prop changes
  useEffect(() => {
    setFormData(prev => ({ ...prev, ward_id: wardId }));
  }, [wardId]);

  return {
    state: {
      rules,
      showForm,
      formData,
      loading
    },
    actions: {
      loadRules,
      createRule,
      setFormData,
      setShowForm,
      resetForm,
      updateArrayField
    },
    utils: {
      getEmploymentTypeDisplayName
    }
  };
};