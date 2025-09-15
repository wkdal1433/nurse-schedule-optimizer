/**
 * Main Role Management Hook
 * Single Responsibility: Central state coordination and tab management
 * Open/Closed: Easy to add new tabs without modification
 * Interface Segregation: Clean interface for main coordination
 * Dependency Inversion: Abstracts over specific domain hooks
 */

import { useState } from 'react';
import { TabType, RoleManagementState } from '../types';
import { rolesAPI } from '../../../services/api';

export interface UseRoleManagementReturn {
  state: RoleManagementState;
  actions: {
    setActiveTab: (tab: TabType) => void;
    setLoading: (loading: boolean) => void;
    createDefaultSettings: () => Promise<void>;
  };
}

export const useRoleManagement = (wardId: number): UseRoleManagementReturn => {
  const [activeTab, setActiveTab] = useState<TabType>('employees');
  const [loading, setLoading] = useState(false);

  const createDefaultSettings = async () => {
    if (!confirm('기본 역할 설정을 생성하시겠습니까?')) return;

    setLoading(true);
    try {
      await rolesAPI.createDefaultRoleSettings(wardId);
      alert('기본 역할 설정이 생성되었습니다.');
    } catch (error) {
      console.error('기본 설정 생성 실패:', error);
      alert('기본 설정 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return {
    state: {
      activeTab,
      loading
    },
    actions: {
      setActiveTab,
      setLoading,
      createDefaultSettings
    }
  };
};