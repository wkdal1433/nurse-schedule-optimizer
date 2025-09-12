import React, { useState, useEffect } from 'react';
import { 
  Schedule, 
  ShiftAssignment, 
  ReplacementSuggestion, 
  ValidationResult,
  EmergencyLog,
  manualEditingAPI 
} from '../services/api';

interface ManualScheduleEditorProps {
  wardId: number;
}

const ManualScheduleEditor: React.FC<ManualScheduleEditorProps> = ({ wardId }) => {
  const [activeTab, setActiveTab] = useState('schedule');
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);
  const [assignments, setAssignments] = useState<ShiftAssignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 편집 상태
  const [editingAssignment, setEditingAssignment] = useState<ShiftAssignment | null>(null);
  const [replacementSuggestions, setReplacementSuggestions] = useState<ReplacementSuggestion[]>([]);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  
  // 응급 상황 상태
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [emergencyData, setEmergencyData] = useState({
    assignment_id: 0,
    replacement_employee_id: 0,
    emergency_reason: '',
    admin_id: 1 // 임시 관리자 ID
  });
  
  // 응급 로그 상태
  const [emergencyLogs, setEmergencyLogs] = useState<EmergencyLog[]>([]);

  // 새 배정 생성 상태
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newAssignment, setNewAssignment] = useState({
    schedule_id: 0,
    employee_id: 1,
    shift_date: new Date().toISOString().split('T')[0],
    shift_type: 'day',
    admin_id: 1,
    override: false,
    override_reason: '',
    notes: ''
  });

  // 일괄 교환 상태
  const [selectedAssignments, setSelectedAssignments] = useState<number[]>([]);
  const [swapMode, setSwapMode] = useState(false);

  useEffect(() => {
    loadSchedules();
  }, [wardId]);

  useEffect(() => {
    if (selectedSchedule) {
      loadAssignments(selectedSchedule.id);
    }
  }, [selectedSchedule]);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const response = await manualEditingAPI.getSchedules(wardId, undefined, 20);
      setSchedules(response.data);
      if (response.data.length > 0) {
        setSelectedSchedule(response.data[0]);
      }
    } catch (err: any) {
      setError('스케줄 로딩 중 오류: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const loadAssignments = async (scheduleId: number) => {
    try {
      setLoading(true);
      const response = await manualEditingAPI.getScheduleAssignments(scheduleId);
      setAssignments(response.data);
    } catch (err: any) {
      setError('배정 로딩 중 오류: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleEditAssignment = async (assignment: ShiftAssignment) => {
    setEditingAssignment(assignment);
    
    // 대체자 추천 로드
    try {
      const suggestions = await manualEditingAPI.getReplacementSuggestions(assignment.id, false, 5);
      setReplacementSuggestions(suggestions.data);
    } catch (err: any) {
      console.error('추천 로딩 실패:', err);
      setReplacementSuggestions([]);
    }
  };

  const handleValidateChange = async (assignmentId: number, newEmployeeId?: number) => {
    try {
      const result = await manualEditingAPI.validateChange({
        assignment_id: assignmentId,
        new_employee_id: newEmployeeId
      });
      setValidationResult(result.data);
    } catch (err: any) {
      alert('검증 중 오류: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleApplyChange = async (assignmentId: number, newEmployeeId: number, override: boolean = false) => {
    if (!override && validationResult && !validationResult.valid) {
      if (!confirm('검증을 통과하지 못했습니다. 강제로 적용하시겠습니까?')) {
        return;
      }
      override = true;
    }

    try {
      await manualEditingAPI.applyChange({
        assignment_id: assignmentId,
        new_employee_id: newEmployeeId,
        override,
        override_reason: override ? '관리자 강제 변경' : undefined,
        admin_id: 1
      });
      
      alert('변경이 성공적으로 적용되었습니다!');
      setEditingAssignment(null);
      setValidationResult(null);
      setReplacementSuggestions([]);
      
      if (selectedSchedule) {
        loadAssignments(selectedSchedule.id);
      }
    } catch (err: any) {
      alert('변경 적용 중 오류: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleEmergencyReassignment = async () => {
    if (!emergencyData.emergency_reason.trim()) {
      alert('응급 상황 사유를 입력해주세요.');
      return;
    }

    try {
      await manualEditingAPI.emergencyReassignment(emergencyData);
      alert('응급 재배치가 완료되었습니다!');
      setShowEmergencyModal(false);
      setEmergencyData({
        assignment_id: 0,
        replacement_employee_id: 0,
        emergency_reason: '',
        admin_id: 1
      });
      
      if (selectedSchedule) {
        loadAssignments(selectedSchedule.id);
      }
    } catch (err: any) {
      alert('응급 재배치 중 오류: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCreateAssignment = async () => {
    if (!selectedSchedule) return;

    try {
      await manualEditingAPI.createAssignment({
        ...newAssignment,
        schedule_id: selectedSchedule.id
      });
      
      alert('새 배정이 생성되었습니다!');
      setShowCreateModal(false);
      setNewAssignment({
        schedule_id: 0,
        employee_id: 1,
        shift_date: new Date().toISOString().split('T')[0],
        shift_type: 'day',
        admin_id: 1,
        override: false,
        override_reason: '',
        notes: ''
      });
      
      loadAssignments(selectedSchedule.id);
    } catch (err: any) {
      alert('배정 생성 중 오류: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteAssignment = async (assignmentId: number) => {
    if (!confirm('정말로 이 배정을 삭제하시겠습니까?')) return;

    try {
      await manualEditingAPI.deleteAssignment(assignmentId, 1, '관리자 요청');
      alert('배정이 삭제되었습니다!');
      
      if (selectedSchedule) {
        loadAssignments(selectedSchedule.id);
      }
    } catch (err: any) {
      alert('삭제 중 오류: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleBulkSwap = async () => {
    if (selectedAssignments.length !== 2) {
      alert('정확히 2개의 배정을 선택해주세요.');
      return;
    }

    try {
      await manualEditingAPI.bulkSwap({
        swap_pairs: [[selectedAssignments[0], selectedAssignments[1]]],
        admin_id: 1,
        validation_level: 'standard'
      });
      
      alert('근무 교환이 완료되었습니다!');
      setSelectedAssignments([]);
      setSwapMode(false);
      
      if (selectedSchedule) {
        loadAssignments(selectedSchedule.id);
      }
    } catch (err: any) {
      alert('교환 중 오류: ' + (err.response?.data?.detail || err.message));
    }
  };

  const loadEmergencyLogs = async () => {
    try {
      const response = await manualEditingAPI.getEmergencyLogs({ limit: 20 });
      setEmergencyLogs(response.data.logs);
    } catch (err: any) {
      setError('응급 로그 로딩 중 오류: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getShiftTypeColor = (shiftType: string) => {
    switch (shiftType) {
      case 'day': return '#007bff';
      case 'evening': return '#ffc107';
      case 'night': return '#343a40';
      default: return '#6c757d';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#28a745';
      case 'draft': return '#ffc107';
      case 'archived': return '#6c757d';
      default: return '#dee2e6';
    }
  };

  if (loading && schedules.length === 0) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>로딩 중...</div>;
  }

  return (
    <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>✏️ 수동 스케줄 편집기</h2>
        <div>
          <button
            onClick={() => setShowCreateModal(true)}
            disabled={!selectedSchedule}
            style={{
              padding: '8px 16px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: selectedSchedule ? 'pointer' : 'not-allowed',
              marginRight: '10px',
              opacity: selectedSchedule ? 1 : 0.5
            }}
          >
            새 배정 추가
          </button>
          <button
            onClick={() => setSwapMode(!swapMode)}
            disabled={!selectedSchedule}
            style={{
              padding: '8px 16px',
              backgroundColor: swapMode ? '#dc3545' : '#17a2b8',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: selectedSchedule ? 'pointer' : 'not-allowed',
              opacity: selectedSchedule ? 1 : 0.5
            }}
          >
            {swapMode ? '교환 취소' : '교환 모드'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#f8d7da',
          color: '#721c24',
          padding: '10px',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div style={{ display: 'flex', marginBottom: '20px', borderBottom: '1px solid #dee2e6' }}>
        {[
          { id: 'schedule', label: '📅 스케줄 편집' },
          { id: 'emergency', label: '🚨 응급 상황' },
          { id: 'logs', label: '📋 변경 기록' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              if (tab.id === 'logs') {
                loadEmergencyLogs();
              }
            }}
            style={{
              padding: '10px 20px',
              border: 'none',
              backgroundColor: activeTab === tab.id ? '#007bff' : 'transparent',
              color: activeTab === tab.id ? 'white' : '#007bff',
              cursor: 'pointer',
              borderRadius: '4px 4px 0 0'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 스케줄 선택 */}
      {activeTab === 'schedule' && (
        <div>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>스케줄 선택</label>
            <select
              value={selectedSchedule?.id || ''}
              onChange={(e) => {
                const schedule = schedules.find(s => s.id === parseInt(e.target.value));
                setSelectedSchedule(schedule || null);
              }}
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
            >
              <option value="">스케줄을 선택하세요</option>
              {schedules.map((schedule) => (
                <option key={schedule.id} value={schedule.id}>
                  {schedule.schedule_name} ({schedule.status}) - 점수: {schedule.optimization_score.toFixed(1)}
                </option>
              ))}
            </select>
          </div>

          {swapMode && (
            <div style={{
              backgroundColor: '#e3f2fd',
              padding: '15px',
              borderRadius: '4px',
              marginBottom: '20px',
              border: '1px solid #2196f3'
            }}>
              <h4>🔄 교환 모드</h4>
              <p>교환할 두 개의 배정을 선택하세요. 선택됨: {selectedAssignments.length}/2</p>
              {selectedAssignments.length === 2 && (
                <button
                  onClick={handleBulkSwap}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#4caf50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  교환 실행
                </button>
              )}
            </div>
          )}

          {/* 근무 배정 목록 */}
          {selectedSchedule && (
            <div>
              <h3>근무 배정 목록</h3>
              <div style={{ display: 'grid', gap: '10px' }}>
                {assignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    style={{
                      border: selectedAssignments.includes(assignment.id) 
                        ? '3px solid #2196f3' 
                        : '1px solid #dee2e6',
                      borderRadius: '4px',
                      padding: '15px',
                      backgroundColor: assignment.is_override ? '#fff3cd' : '#f8f9fa',
                      cursor: swapMode ? 'pointer' : 'default'
                    }}
                    onClick={() => {
                      if (swapMode) {
                        if (selectedAssignments.includes(assignment.id)) {
                          setSelectedAssignments(prev => prev.filter(id => id !== assignment.id));
                        } else if (selectedAssignments.length < 2) {
                          setSelectedAssignments(prev => [...prev, assignment.id]);
                        } else {
                          alert('최대 2개까지만 선택할 수 있습니다.');
                        }
                      }
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <h4 style={{ margin: '0 0 5px 0' }}>
                          {assignment.employee_name || `직원 ID: ${assignment.employee_id}`}
                          {assignment.is_override && (
                            <span style={{ 
                              backgroundColor: '#ffc107',
                              color: '#856404',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              marginLeft: '10px'
                            }}>
                              강제 배정
                            </span>
                          )}
                        </h4>
                        <p style={{ margin: '5px 0', color: '#6c757d' }}>
                          <span style={{
                            backgroundColor: getShiftTypeColor(assignment.shift_type),
                            color: 'white',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            marginRight: '10px'
                          }}>
                            {assignment.shift_type}
                          </span>
                          {new Date(assignment.shift_date).toLocaleDateString('ko-KR')}
                        </p>
                        {assignment.override_reason && (
                          <p style={{ margin: '5px 0', fontSize: '14px', fontStyle: 'italic', color: '#856404' }}>
                            사유: {assignment.override_reason}
                          </p>
                        )}
                      </div>
                      {!swapMode && (
                        <div>
                          <button
                            onClick={() => handleEditAssignment(assignment)}
                            style={{
                              padding: '4px 8px',
                              backgroundColor: '#007bff',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              marginRight: '5px',
                              fontSize: '12px'
                            }}
                          >
                            편집
                          </button>
                          <button
                            onClick={() => {
                              setEmergencyData({
                                assignment_id: assignment.id,
                                replacement_employee_id: 0,
                                emergency_reason: '',
                                admin_id: 1
                              });
                              setShowEmergencyModal(true);
                            }}
                            style={{
                              padding: '4px 8px',
                              backgroundColor: '#dc3545',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              marginRight: '5px',
                              fontSize: '12px'
                            }}
                          >
                            응급
                          </button>
                          <button
                            onClick={() => handleDeleteAssignment(assignment.id)}
                            style={{
                              padding: '4px 8px',
                              backgroundColor: '#6c757d',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            삭제
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {assignments.length === 0 && (
                <p style={{ textAlign: 'center', color: '#6c757d', padding: '40px' }}>
                  배정된 근무가 없습니다.
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* 응급 상황 탭 */}
      {activeTab === 'emergency' && (
        <div>
          <h3>🚨 응급 상황 관리</h3>
          <p>병가, 사고, 예상치 못한 결근 등의 응급 상황에 대한 즉시 대응</p>
          
          <div style={{ 
            border: '1px solid #dc3545', 
            borderRadius: '4px', 
            padding: '20px',
            backgroundColor: '#f8d7da',
            marginBottom: '20px'
          }}>
            <h4>응급 상황 지침</h4>
            <ul>
              <li>응급 상황 시 모든 제약조건을 무시하고 즉시 재배치 가능</li>
              <li>시스템이 자동으로 최적의 대체자를 추천</li>
              <li>모든 응급 조치는 로그에 기록됨</li>
              <li>영향받은 직원들에게 자동으로 알림 발송</li>
            </ul>
          </div>

          <div style={{ 
            border: '1px solid #28a745', 
            borderRadius: '4px', 
            padding: '15px',
            backgroundColor: '#d4edda'
          }}>
            <p><strong>빠른 응급 재배치:</strong> 스케줄 편집 탭에서 각 배정의 "응급" 버튼을 클릭하세요.</p>
          </div>
        </div>
      )}

      {/* 변경 기록 탭 */}
      {activeTab === 'logs' && (
        <div>
          <h3>📋 응급 상황 기록</h3>
          
          <div style={{ display: 'grid', gap: '10px' }}>
            {emergencyLogs.map((log) => (
              <div
                key={log.id}
                style={{
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  padding: '15px',
                  backgroundColor: log.status === 'resolved' ? '#d4edda' : '#fff3cd'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h4 style={{ margin: '0 0 5px 0' }}>
                      {log.emergency_type}
                      <span style={{
                        backgroundColor: log.status === 'resolved' ? '#28a745' : '#ffc107',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        marginLeft: '10px'
                      }}>
                        {log.status}
                      </span>
                    </h4>
                    <p style={{ margin: '5px 0', color: '#6c757d' }}>
                      <strong>사유:</strong> {log.reason}
                    </p>
                    <p style={{ margin: '5px 0', color: '#6c757d' }}>
                      <strong>발생일시:</strong> {new Date(log.created_at).toLocaleString('ko-KR')}
                    </p>
                    {log.resolution_time && (
                      <p style={{ margin: '5px 0', color: '#6c757d' }}>
                        <strong>해결일시:</strong> {new Date(log.resolution_time).toLocaleString('ko-KR')}
                      </p>
                    )}
                  </div>
                  <div>
                    <span style={{
                      backgroundColor: log.urgency_level === 'critical' ? '#dc3545' : 
                                     log.urgency_level === 'high' ? '#fd7e14' : '#ffc107',
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '12px'
                    }}>
                      긴급도: {log.urgency_level}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {emergencyLogs.length === 0 && (
            <p style={{ textAlign: 'center', color: '#6c757d', padding: '40px' }}>
              응급 상황 기록이 없습니다.
            </p>
          )}
        </div>
      )}

      {/* 편집 모달 */}
      {editingAssignment && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            width: '600px',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            <h3>근무 배정 편집</h3>
            
            <div style={{ marginBottom: '20px' }}>
              <p><strong>현재 배정:</strong> {editingAssignment.employee_name} - {editingAssignment.shift_type} - {new Date(editingAssignment.shift_date).toLocaleDateString('ko-KR')}</p>
            </div>

            {/* 대체자 추천 */}
            <h4>추천 대체자</h4>
            <div style={{ display: 'grid', gap: '10px', marginBottom: '20px' }}>
              {replacementSuggestions.map((suggestion) => (
                <div
                  key={suggestion.employee_id}
                  style={{
                    border: '1px solid #dee2e6',
                    borderRadius: '4px',
                    padding: '10px',
                    backgroundColor: suggestion.suitability_score >= 70 ? '#d4edda' : '#fff3cd'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{suggestion.employee_name}</strong>
                      <span style={{
                        backgroundColor: '#007bff',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        marginLeft: '10px'
                      }}>
                        적합도: {suggestion.suitability_score.toFixed(1)}점
                      </span>
                      <p style={{ margin: '5px 0', fontSize: '14px', color: '#6c757d' }}>
                        {suggestion.role} | {suggestion.employment_type} | 경력 {suggestion.years_experience}년
                      </p>
                      <p style={{ margin: '5px 0', fontSize: '12px', color: '#28a745' }}>
                        장점: {suggestion.suitability_reasons.slice(0, 2).join(', ')}
                      </p>
                      {suggestion.warnings.length > 0 && (
                        <p style={{ margin: '5px 0', fontSize: '12px', color: '#dc3545' }}>
                          주의: {suggestion.warnings.join(', ')}
                        </p>
                      )}
                    </div>
                    <div>
                      <button
                        onClick={() => handleValidateChange(editingAssignment.id, suggestion.employee_id)}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#17a2b8',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          marginRight: '5px',
                          fontSize: '12px'
                        }}
                      >
                        검증
                      </button>
                      <button
                        onClick={() => handleApplyChange(editingAssignment.id, suggestion.employee_id)}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#28a745',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        적용
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 검증 결과 */}
            {validationResult && (
              <div style={{
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                padding: '15px',
                marginBottom: '20px',
                backgroundColor: validationResult.valid ? '#d4edda' : '#f8d7da'
              }}>
                <h4>검증 결과</h4>
                <p><strong>유효성:</strong> {validationResult.valid ? '✅ 통과' : '❌ 실패'}</p>
                <p><strong>패턴 점수:</strong> {validationResult.pattern_score}/100</p>
                
                {validationResult.errors.length > 0 && (
                  <div>
                    <strong>오류:</strong>
                    <ul>
                      {validationResult.errors.map((error, index) => (
                        <li key={index} style={{ color: '#721c24' }}>{error.message}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {validationResult.warnings.length > 0 && (
                  <div>
                    <strong>경고:</strong>
                    <ul>
                      {validationResult.warnings.map((warning, index) => (
                        <li key={index} style={{ color: '#856404' }}>{warning.message}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setEditingAssignment(null);
                  setReplacementSuggestions([]);
                  setValidationResult(null);
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 응급 재배치 모달 */}
      {showEmergencyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            width: '400px'
          }}>
            <h3>🚨 응급 재배치</h3>
            
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>대체 직원 ID</label>
              <input
                type="number"
                value={emergencyData.replacement_employee_id}
                onChange={(e) => setEmergencyData({
                  ...emergencyData,
                  replacement_employee_id: parseInt(e.target.value) || 0
                })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>응급 상황 사유</label>
              <textarea
                value={emergencyData.emergency_reason}
                onChange={(e) => setEmergencyData({
                  ...emergencyData,
                  emergency_reason: e.target.value
                })}
                placeholder="예: 직원 김OO 급성 질환으로 인한 응급실 이송"
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', height: '80px' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowEmergencyModal(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                취소
              </button>
              <button
                onClick={handleEmergencyReassignment}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                응급 재배치 실행
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 새 배정 생성 모달 */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            width: '400px'
          }}>
            <h3>새 근무 배정 생성</h3>
            
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>직원 ID</label>
              <input
                type="number"
                value={newAssignment.employee_id}
                onChange={(e) => setNewAssignment({
                  ...newAssignment,
                  employee_id: parseInt(e.target.value) || 1
                })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>근무 날짜</label>
              <input
                type="date"
                value={newAssignment.shift_date}
                onChange={(e) => setNewAssignment({
                  ...newAssignment,
                  shift_date: e.target.value
                })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>근무 유형</label>
              <select
                value={newAssignment.shift_type}
                onChange={(e) => setNewAssignment({
                  ...newAssignment,
                  shift_type: e.target.value
                })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              >
                <option value="day">Day</option>
                <option value="evening">Evening</option>
                <option value="night">Night</option>
                <option value="long_day">Long Day</option>
              </select>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>
                <input
                  type="checkbox"
                  checked={newAssignment.override}
                  onChange={(e) => setNewAssignment({
                    ...newAssignment,
                    override: e.target.checked
                  })}
                />
                <span style={{ marginLeft: '5px' }}>제약조건 무시 (강제 배정)</span>
              </label>
            </div>

            {newAssignment.override && (
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>오버라이드 사유</label>
                <input
                  type="text"
                  value={newAssignment.override_reason}
                  onChange={(e) => setNewAssignment({
                    ...newAssignment,
                    override_reason: e.target.value
                  })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                취소
              </button>
              <button
                onClick={handleCreateAssignment}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                생성
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManualScheduleEditor;