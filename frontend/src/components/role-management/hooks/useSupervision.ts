/**
 * Supervision Management Hook
 * Single Responsibility: Supervision pair state management and operations
 * Open/Closed: Easy to extend with new supervision features
 * Interface Segregation: Focused on supervision-specific operations
 * Dependency Inversion: Uses rolesAPI abstraction
 */

import { useState, useEffect } from 'react';
import { rolesAPI, SupervisionPair, EmployeeRoleInfo } from '../../../services/api';

export interface SupervisionFormData {
  supervisor_id: number;
  supervisee_id: number;
  pairing_type: string;
  end_date: string;
}

export interface UseSupervisionReturn {
  state: {
    pairs: SupervisionPair[];
    showForm: boolean;
    formData: SupervisionFormData;
    loading: boolean;
  };
  actions: {
    loadPairs: () => Promise<void>;
    createPair: () => Promise<void>;
    deactivatePair: (pairId: number) => Promise<void>;
    setFormData: (data: SupervisionFormData) => void;
    setShowForm: (show: boolean) => void;
    resetForm: () => void;
  };
  utils: {
    getRoleDisplayName: (role: string) => string;
    getSupervisors: (employees: EmployeeRoleInfo[]) => EmployeeRoleInfo[];
    getSupervisees: (employees: EmployeeRoleInfo[]) => EmployeeRoleInfo[];
  };
}

const createDefaultFormData = (): SupervisionFormData => ({
  supervisor_id: 0,
  supervisee_id: 0,
  pairing_type: 'mentor',
  end_date: ''
});

const roleDisplayNames: Record<string, string> = {
  'head_nurse': '수간호사',
  'charge_nurse': '책임간호사',
  'staff_nurse': '일반간호사',
  'new_nurse': '신입간호사',
  'education_coordinator': '교육담당자'
};

export const useSupervision = (wardId: number): UseSupervisionReturn => {
  const [pairs, setPairs] = useState<SupervisionPair[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<SupervisionFormData>(createDefaultFormData());
  const [loading, setLoading] = useState(false);

  const loadPairs = async () => {
    setLoading(true);
    try {
      const response = await rolesAPI.getSupervisionPairs(wardId);
      setPairs(response.data);
    } catch (error) {
      console.error('감독 페어 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const createPair = async () => {
    if (formData.supervisor_id === 0 || formData.supervisee_id === 0) {
      alert('감독자와 피감독자를 모두 선택해주세요.');
      return;
    }

    setLoading(true);
    try {
      await rolesAPI.createSupervisionPair(formData);
      await loadPairs();
      resetForm();
      alert('감독 페어가 생성되었습니다.');
    } catch (error) {
      console.error('감독 페어 생성 실패:', error);
      alert('감독 페어 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const deactivatePair = async (pairId: number) => {
    if (!confirm('이 감독 페어를 비활성화하시겠습니까?')) return;

    setLoading(true);
    try {
      await rolesAPI.deactivateSupervisionPair(pairId);
      await loadPairs();
      alert('감독 페어가 비활성화되었습니다.');
    } catch (error) {
      console.error('감독 페어 비활성화 실패:', error);
      alert('감독 페어 비활성화에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setShowForm(false);
    setFormData(createDefaultFormData());
  };

  const getRoleDisplayName = (role: string) => {
    return roleDisplayNames[role] || role;
  };

  const getSupervisors = (employees: EmployeeRoleInfo[]) => {
    return employees.filter(emp => emp.can_supervise);
  };

  const getSupervisees = (employees: EmployeeRoleInfo[]) => {
    return employees.filter(emp => emp.requires_supervision || emp.role === 'new_nurse');
  };

  // Load pairs when wardId changes
  useEffect(() => {
    loadPairs();
  }, [wardId]);

  return {
    state: {
      pairs,
      showForm,
      formData,
      loading
    },
    actions: {
      loadPairs,
      createPair,
      deactivatePair,
      setFormData,
      setShowForm,
      resetForm
    },
    utils: {
      getRoleDisplayName,
      getSupervisors,
      getSupervisees
    }
  };
};