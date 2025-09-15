/**
 * Role Management New - Main Orchestrator Component
 * Single Responsibility: Tab coordination and main UI layout
 * Open/Closed: Easy to add new tabs without modifying existing code
 * Interface Segregation: Clean separation of tab-specific UI components
 * Dependency Inversion: Uses abstracted hooks and components
 */

import React from 'react';
import { useRoleManagement } from './hooks/useRoleManagement';
import { RoleManagementProps } from './types';
import EmployeeManagement from './components/EmployeeManagement';
import ConstraintManagement from './components/ConstraintManagement';
import SupervisionManagement from './components/SupervisionManagement';
import EmploymentManagement from './components/EmploymentManagement';

const RoleManagementNew: React.FC<RoleManagementProps> = ({ wardId = 1 }) => {
  const roleManagement = useRoleManagement(wardId);
  
  return (
    <div className="role-management">
      <RoleManagementHeader roleManagement={roleManagement} />
      <RoleManagementTabs roleManagement={roleManagement} />
      <RoleManagementContent roleManagement={roleManagement} wardId={wardId} />
      <RoleManagementStyles />
    </div>
  );
};

interface RoleManagementComponentProps {
  roleManagement: ReturnType<typeof useRoleManagement>;
  wardId?: number;
}

const RoleManagementHeader: React.FC<Pick<RoleManagementComponentProps, 'roleManagement'>> = ({ roleManagement }) => {
  const { state, actions } = roleManagement;
  const { loading } = state;
  const { createDefaultSettings } = actions;

  return (
    <>
      <div className="header">
        <h2>👥 역할 & 고용형태 관리</h2>
        <button onClick={createDefaultSettings} className="btn-secondary">
          기본 설정 생성
        </button>
      </div>
      {loading && <div className="loading">로딩 중...</div>}
    </>
  );
};

const RoleManagementTabs: React.FC<Pick<RoleManagementComponentProps, 'roleManagement'>> = ({ roleManagement }) => {
  const { state, actions } = roleManagement;
  const { activeTab } = state;
  const { setActiveTab } = actions;

  const tabs = [
    { key: 'employees' as const, label: '👤 직원 관리' },
    { key: 'constraints' as const, label: '📋 역할 제약조건' },
    { key: 'supervision' as const, label: '👥 감독 페어' },
    { key: 'employment' as const, label: '🏢 고용형태 규칙' }
  ];

  return (
    <div className="tabs">
      {tabs.map(tab => (
        <button
          key={tab.key}
          className={activeTab === tab.key ? 'active' : ''}
          onClick={() => setActiveTab(tab.key)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};

const RoleManagementContent: React.FC<RoleManagementComponentProps> = ({ roleManagement, wardId = 1 }) => {
  const { state } = roleManagement;
  const { activeTab } = state;

  return (
    <>
      <EmployeeManagement 
        wardId={wardId} 
        isVisible={activeTab === 'employees'} 
      />
      <ConstraintManagement 
        wardId={wardId} 
        isVisible={activeTab === 'constraints'} 
      />
      <SupervisionManagement 
        wardId={wardId} 
        isVisible={activeTab === 'supervision'} 
      />
      <EmploymentManagement 
        wardId={wardId} 
        isVisible={activeTab === 'employment'} 
      />
    </>
  );
};

// Extracted styles component for better separation of concerns
const RoleManagementStyles: React.FC = () => (
  <style jsx>{`
    .role-management {
      padding: 20px;
      max-width: 1600px;
      margin: 0 auto;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    .tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 30px;
      border-bottom: 2px solid #e0e0e0;
    }

    .tabs button {
      padding: 12px 20px;
      border: none;
      background: transparent;
      border-bottom: 3px solid transparent;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.3s;
    }

    .tabs button.active {
      border-bottom-color: #3498db;
      color: #3498db;
      font-weight: 600;
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    .employees-grid,
    .constraints-grid,
    .pairs-grid,
    .employment-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: 20px;
    }

    .employee-card,
    .constraint-card,
    .pair-card,
    .employment-card {
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 10px;
      padding: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .employee-header,
    .constraint-header,
    .pair-header,
    .employment-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 15px;
    }

    .employee-badges,
    .constraint-badge,
    .priority-badge {
      display: flex;
      gap: 5px;
    }

    .badge {
      padding: 4px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }

    .badge.role-head_nurse { background: #e74c3c; color: white; }
    .badge.role-charge_nurse { background: #e67e22; color: white; }
    .badge.role-staff_nurse { background: #3498db; color: white; }
    .badge.role-new_nurse { background: #2ecc71; color: white; }
    .badge.role-education_coordinator { background: #9b59b6; color: white; }

    .badge.employment-full_time { background: #34495e; color: white; }
    .badge.employment-part_time { background: #95a5a6; color: white; }

    .detail-row,
    .limit-item,
    .permission-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      padding-bottom: 4px;
      border-bottom: 1px solid #f0f0f0;
    }

    .employee-capabilities,
    .constraint-flags,
    .permission-flags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 10px 0;
    }

    .capability,
    .flag {
      padding: 4px 8px;
      border-radius: 8px;
      font-size: 12px;
    }

    .capability { background: #d5f4e6; color: #27ae60; }
    .capability.warning { background: #ffeaa7; color: #e17055; }

    .flag.supervisor { background: #74b9ff; color: white; }
    .flag.charge { background: #fdcb6e; color: #2d3436; }
    .flag.allowed { background: #00cec9; color: white; }

    .employee-form,
    .constraint-form,
    .pair-form,
    .employment-form {
      background: #f8f9fa;
      padding: 25px;
      border-radius: 10px;
      margin-bottom: 30px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }

    .form-group.full-width {
      grid-column: 1 / -1;
    }

    .form-group label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
      color: #555;
    }

    .form-group input,
    .form-group select,
    .form-group textarea {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 5px;
      font-size: 14px;
    }

    .form-group small {
      color: #666;
      font-size: 12px;
    }

    .checkbox-section {
      display: flex;
      gap: 20px;
      margin: 15px 0;
    }

    .checkbox-section label {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
    }

    .form-actions {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
    }

    .employee-actions,
    .pair-actions {
      margin-top: 15px;
    }

    .btn-primary,
    .btn-secondary,
    .btn-edit,
    .btn-danger {
      padding: 8px 16px;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.3s;
    }

    .btn-primary { background: #3498db; color: white; }
    .btn-secondary { background: #95a5a6; color: white; }
    .btn-edit { background: #f39c12; color: white; }
    .btn-danger { background: #e74c3c; color: white; }

    .btn-primary:hover { background: #2980b9; }
    .btn-secondary:hover { background: #7f8c8d; }
    .btn-edit:hover { background: #e67e22; }
    .btn-danger:hover { background: #c0392b; }

    .loading {
      text-align: center;
      padding: 20px;
      color: #666;
    }

    .status.active { color: #27ae60; font-weight: bold; }
    .status.inactive { color: #e74c3c; font-weight: bold; }

    .pair-members {
      margin: 15px 0;
    }

    .member {
      margin-bottom: 8px;
    }

    .member .role {
      color: #666;
      font-size: 12px;
    }

    .pair-dates {
      font-size: 12px;
      color: #666;
    }
  `}</style>
);

export default RoleManagementNew;