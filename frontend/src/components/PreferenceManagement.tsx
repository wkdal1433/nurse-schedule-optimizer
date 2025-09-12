import React, { useState, useEffect } from 'react';
import { preferencesAPI, PreferenceTemplate, ShiftRequest } from '../services/api';

interface PreferenceManagementProps {
  wardId?: number;
  currentUserId?: number;
}

const PreferenceManagement: React.FC<PreferenceManagementProps> = ({ 
  wardId, 
  currentUserId = 1 // 임시 사용자 ID
}) => {
  const [activeTab, setActiveTab] = useState<'preferences' | 'requests' | 'dashboard'>('preferences');
  const [loading, setLoading] = useState(false);
  
  // 선호도 관련 상태
  const [currentEmployeeId, setCurrentEmployeeId] = useState<number>(1);
  const [preferences, setPreferences] = useState<PreferenceTemplate | null>(null);
  const [editingPreferences, setEditingPreferences] = useState<boolean>(false);

  // 요청 관련 상태
  const [pendingRequests, setPendingRequests] = useState<ShiftRequest[]>([]);
  const [myRequests, setMyRequests] = useState<ShiftRequest[]>([]);
  const [showRequestForm, setShowRequestForm] = useState<boolean>(false);

  // 대시보드 상태
  const [dashboardData, setDashboardData] = useState<any>(null);

  const defaultPreferences: Omit<PreferenceTemplate, 'id' | 'employee_id'> = {
    preferred_shifts: ['day', 'evening'],
    avoided_shifts: ['night'],
    max_night_shifts_per_month: 8,
    max_weekend_shifts_per_month: 6,
    preferred_patterns: ['day->off', 'evening->off'],
    avoided_patterns: ['night->day', 'day->night'],
    max_consecutive_days: 3,
    min_days_off_after_nights: 1,
    cannot_work_alone: false,
    needs_senior_support: false,
  };

  const [preferencesForm, setPreferencesForm] = useState(defaultPreferences);

  const defaultRequest: Omit<ShiftRequest, 'id' | 'employee_id'> = {
    start_date: '',
    end_date: '',
    request_type: 'vacation',
    priority: 'normal',
    shift_type: '',
    reason: '',
    medical_reason: false,
    is_recurring: false,
    flexibility_level: 1,
    alternative_acceptable: true,
  };

  const [requestForm, setRequestForm] = useState(defaultRequest);

  useEffect(() => {
    if (activeTab === 'preferences') {
      loadPreferences();
    } else if (activeTab === 'requests') {
      loadRequests();
    } else if (activeTab === 'dashboard' && wardId) {
      loadDashboard();
    }
  }, [activeTab, currentEmployeeId, wardId]);

  const loadPreferences = async () => {
    setLoading(true);
    try {
      const response = await preferencesAPI.getPreferences(currentEmployeeId);
      if (response.data) {
        setPreferences(response.data);
        setPreferencesForm({
          preferred_shifts: response.data.preferred_shifts,
          avoided_shifts: response.data.avoided_shifts,
          max_night_shifts_per_month: response.data.max_night_shifts_per_month,
          max_weekend_shifts_per_month: response.data.max_weekend_shifts_per_month,
          preferred_patterns: response.data.preferred_patterns,
          avoided_patterns: response.data.avoided_patterns,
          max_consecutive_days: response.data.max_consecutive_days,
          min_days_off_after_nights: response.data.min_days_off_after_nights,
          cannot_work_alone: response.data.cannot_work_alone,
          needs_senior_support: response.data.needs_senior_support,
        });
      }
    } catch (error) {
      console.error('선호도 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRequests = async () => {
    setLoading(true);
    try {
      const [pendingResponse, myResponse] = await Promise.all([
        preferencesAPI.getPendingRequests(wardId),
        preferencesAPI.getEmployeeRequests(currentEmployeeId)
      ]);
      
      setPendingRequests(pendingResponse.data);
      setMyRequests(myResponse.data);
    } catch (error) {
      console.error('요청 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async () => {
    if (!wardId) return;
    
    setLoading(true);
    try {
      const response = await preferencesAPI.getDashboard(wardId);
      setDashboardData(response.data);
    } catch (error) {
      console.error('대시보드 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePreferences = async () => {
    setLoading(true);
    try {
      await preferencesAPI.createPreferences(currentEmployeeId, preferencesForm);
      await loadPreferences();
      setEditingPreferences(false);
      alert('선호도가 저장되었습니다.');
    } catch (error) {
      console.error('선호도 저장 실패:', error);
      alert('선호도 저장에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitRequest = async () => {
    setLoading(true);
    try {
      await preferencesAPI.submitRequest(currentEmployeeId, requestForm);
      await loadRequests();
      setShowRequestForm(false);
      setRequestForm(defaultRequest);
      alert('요청이 제출되었습니다.');
    } catch (error) {
      console.error('요청 제출 실패:', error);
      alert('요청 제출에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewRequest = async (requestId: number, status: string, adminNotes: string = '') => {
    setLoading(true);
    try {
      await preferencesAPI.reviewRequest(requestId, currentUserId, status, adminNotes);
      await loadRequests();
      alert('요청이 처리되었습니다.');
    } catch (error) {
      console.error('요청 처리 실패:', error);
      alert('요청 처리에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const updateArrayField = (field: keyof typeof preferencesForm, value: string) => {
    const array = value.split(',').map(s => s.trim()).filter(s => s);
    setPreferencesForm({ ...preferencesForm, [field]: array });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'normal': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return '#28a745';
      case 'denied': return '#dc3545';
      case 'partially_approved': return '#fd7e14';
      default: return '#6c757d';
    }
  };

  return (
    <div className="preference-management">
      <div className="tabs">
        <button
          className={activeTab === 'preferences' ? 'active' : ''}
          onClick={() => setActiveTab('preferences')}
        >
          📝 개인 선호도
        </button>
        <button
          className={activeTab === 'requests' ? 'active' : ''}
          onClick={() => setActiveTab('requests')}
        >
          📋 근무 요청
        </button>
        {wardId && (
          <button
            className={activeTab === 'dashboard' ? 'active' : ''}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 관리 대시보드
          </button>
        )}
      </div>

      {loading && <div className="loading">로딩 중...</div>}

      {activeTab === 'preferences' && (
        <div className="preferences-section">
          <div className="section-header">
            <h2>개인 선호도 설정</h2>
            <div className="header-controls">
              <select
                value={currentEmployeeId}
                onChange={(e) => setCurrentEmployeeId(Number(e.target.value))}
              >
                <option value={1}>간호사 1</option>
                <option value={2}>간호사 2</option>
                <option value={3}>간호사 3</option>
              </select>
              <button
                onClick={() => setEditingPreferences(!editingPreferences)}
                className="btn-primary"
              >
                {editingPreferences ? '취소' : '편집'}
              </button>
            </div>
          </div>

          {editingPreferences ? (
            <div className="preferences-form">
              <div className="form-section">
                <h3>근무 선호도</h3>
                <div className="form-group">
                  <label>선호하는 근무 (콤마로 구분)</label>
                  <input
                    type="text"
                    value={preferencesForm.preferred_shifts.join(', ')}
                    onChange={(e) => updateArrayField('preferred_shifts', e.target.value)}
                    placeholder="day, evening"
                  />
                </div>
                <div className="form-group">
                  <label>피하고 싶은 근무</label>
                  <input
                    type="text"
                    value={preferencesForm.avoided_shifts.join(', ')}
                    onChange={(e) => updateArrayField('avoided_shifts', e.target.value)}
                    placeholder="night"
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>월 최대 야간근무</label>
                    <input
                      type="number"
                      min="0"
                      max="31"
                      value={preferencesForm.max_night_shifts_per_month}
                      onChange={(e) => setPreferencesForm({
                        ...preferencesForm,
                        max_night_shifts_per_month: Number(e.target.value)
                      })}
                    />
                  </div>
                  <div className="form-group">
                    <label>월 최대 주말근무</label>
                    <input
                      type="number"
                      min="0"
                      max="10"
                      value={preferencesForm.max_weekend_shifts_per_month}
                      onChange={(e) => setPreferencesForm({
                        ...preferencesForm,
                        max_weekend_shifts_per_month: Number(e.target.value)
                      })}
                    />
                  </div>
                </div>
              </div>

              <div className="form-section">
                <h3>근무 패턴 선호도</h3>
                <div className="form-group">
                  <label>선호하는 패턴</label>
                  <input
                    type="text"
                    value={preferencesForm.preferred_patterns.join(', ')}
                    onChange={(e) => updateArrayField('preferred_patterns', e.target.value)}
                    placeholder="day->off, evening->off"
                  />
                </div>
                <div className="form-group">
                  <label>피하고 싶은 패턴</label>
                  <input
                    type="text"
                    value={preferencesForm.avoided_patterns.join(', ')}
                    onChange={(e) => updateArrayField('avoided_patterns', e.target.value)}
                    placeholder="night->day, day->night"
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>최대 연속 근무일</label>
                    <input
                      type="number"
                      min="1"
                      max="7"
                      value={preferencesForm.max_consecutive_days}
                      onChange={(e) => setPreferencesForm({
                        ...preferencesForm,
                        max_consecutive_days: Number(e.target.value)
                      })}
                    />
                  </div>
                  <div className="form-group">
                    <label>야간근무 후 최소 휴무</label>
                    <input
                      type="number"
                      min="0"
                      max="3"
                      value={preferencesForm.min_days_off_after_nights}
                      onChange={(e) => setPreferencesForm({
                        ...preferencesForm,
                        min_days_off_after_nights: Number(e.target.value)
                      })}
                    />
                  </div>
                </div>
              </div>

              <div className="form-section">
                <h3>기타 제약사항</h3>
                <div className="checkbox-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={preferencesForm.cannot_work_alone}
                      onChange={(e) => setPreferencesForm({
                        ...preferencesForm,
                        cannot_work_alone: e.target.checked
                      })}
                    />
                    단독 근무 불가
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={preferencesForm.needs_senior_support}
                      onChange={(e) => setPreferencesForm({
                        ...preferencesForm,
                        needs_senior_support: e.target.checked
                      })}
                    />
                    선임 지원 필요
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button onClick={handleSavePreferences} className="btn-primary" disabled={loading}>
                  {loading ? '저장 중...' : '저장'}
                </button>
                <button onClick={() => setEditingPreferences(false)} className="btn-secondary">
                  취소
                </button>
              </div>
            </div>
          ) : (
            <div className="preferences-display">
              {preferences ? (
                <div className="preferences-cards">
                  <div className="preference-card">
                    <h3>근무 선호도</h3>
                    <div className="preference-item">
                      <strong>선호하는 근무:</strong> {preferences.preferred_shifts.join(', ') || '없음'}
                    </div>
                    <div className="preference-item">
                      <strong>피하는 근무:</strong> {preferences.avoided_shifts.join(', ') || '없음'}
                    </div>
                    <div className="preference-item">
                      <strong>월 최대 야간근무:</strong> {preferences.max_night_shifts_per_month}일
                    </div>
                    <div className="preference-item">
                      <strong>월 최대 주말근무:</strong> {preferences.max_weekend_shifts_per_month}일
                    </div>
                  </div>
                  
                  <div className="preference-card">
                    <h3>근무 패턴</h3>
                    <div className="preference-item">
                      <strong>선호 패턴:</strong> {preferences.preferred_patterns.join(', ') || '없음'}
                    </div>
                    <div className="preference-item">
                      <strong>피하는 패턴:</strong> {preferences.avoided_patterns.join(', ') || '없음'}
                    </div>
                    <div className="preference-item">
                      <strong>최대 연속 근무:</strong> {preferences.max_consecutive_days}일
                    </div>
                    <div className="preference-item">
                      <strong>야간근무 후 최소 휴무:</strong> {preferences.min_days_off_after_nights}일
                    </div>
                  </div>

                  <div className="preference-card">
                    <h3>기타 제약사항</h3>
                    <div className="preference-item">
                      <strong>단독 근무:</strong> {preferences.cannot_work_alone ? '불가' : '가능'}
                    </div>
                    <div className="preference-item">
                      <strong>선임 지원:</strong> {preferences.needs_senior_support ? '필요' : '불필요'}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="no-preferences">
                  <p>설정된 선호도가 없습니다.</p>
                  <button onClick={() => setEditingPreferences(true)} className="btn-primary">
                    선호도 설정하기
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'requests' && (
        <div className="requests-section">
          <div className="section-header">
            <h2>근무 요청 관리</h2>
            <button
              onClick={() => setShowRequestForm(!showRequestForm)}
              className="btn-primary"
            >
              {showRequestForm ? '취소' : '새 요청'}
            </button>
          </div>

          {showRequestForm && (
            <div className="request-form">
              <h3>새 근무 요청</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>시작 날짜</label>
                  <input
                    type="date"
                    value={requestForm.start_date}
                    onChange={(e) => setRequestForm({ ...requestForm, start_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>종료 날짜</label>
                  <input
                    type="date"
                    value={requestForm.end_date}
                    onChange={(e) => setRequestForm({ ...requestForm, end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>요청 유형</label>
                  <select
                    value={requestForm.request_type}
                    onChange={(e) => setRequestForm({ 
                      ...requestForm, 
                      request_type: e.target.value as any 
                    })}
                  >
                    <option value="vacation">휴가</option>
                    <option value="shift_preference">근무 선호</option>
                    <option value="avoid">근무 회피</option>
                    <option value="pattern_request">패턴 요청</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>우선순위</label>
                  <select
                    value={requestForm.priority}
                    onChange={(e) => setRequestForm({ 
                      ...requestForm, 
                      priority: e.target.value as any 
                    })}
                  >
                    <option value="low">낮음</option>
                    <option value="normal">보통</option>
                    <option value="high">높음</option>
                    <option value="urgent">긴급</option>
                  </select>
                </div>
              </div>

              {requestForm.request_type === 'shift_preference' && (
                <div className="form-group">
                  <label>희망 근무</label>
                  <select
                    value={requestForm.shift_type || ''}
                    onChange={(e) => setRequestForm({ ...requestForm, shift_type: e.target.value })}
                  >
                    <option value="">선택하세요</option>
                    <option value="day">주간</option>
                    <option value="evening">저녁</option>
                    <option value="night">야간</option>
                    <option value="off">휴무</option>
                  </select>
                </div>
              )}

              <div className="form-group">
                <label>요청 사유</label>
                <textarea
                  value={requestForm.reason}
                  onChange={(e) => setRequestForm({ ...requestForm, reason: e.target.value })}
                  rows={3}
                  placeholder="요청 사유를 입력하세요"
                />
              </div>

              <div className="form-row">
                <div className="checkbox-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={requestForm.medical_reason}
                      onChange={(e) => setRequestForm({ 
                        ...requestForm, 
                        medical_reason: e.target.checked 
                      })}
                    />
                    의료적 사유
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={requestForm.alternative_acceptable}
                      onChange={(e) => setRequestForm({ 
                        ...requestForm, 
                        alternative_acceptable: e.target.checked 
                      })}
                    />
                    대안 수용 가능
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label>유연성 수준: {requestForm.flexibility_level}</label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={requestForm.flexibility_level}
                  onChange={(e) => setRequestForm({ 
                    ...requestForm, 
                    flexibility_level: Number(e.target.value) 
                  })}
                />
                <div className="range-labels">
                  <span>매우 엄격</span>
                  <span>매우 유연</span>
                </div>
              </div>

              <div className="form-actions">
                <button onClick={handleSubmitRequest} className="btn-primary" disabled={loading}>
                  {loading ? '제출 중...' : '요청 제출'}
                </button>
                <button 
                  onClick={() => setShowRequestForm(false)} 
                  className="btn-secondary"
                >
                  취소
                </button>
              </div>
            </div>
          )}

          <div className="requests-lists">
            <div className="my-requests">
              <h3>내 요청 ({myRequests.length})</h3>
              {myRequests.length > 0 ? (
                <div className="requests-grid">
                  {myRequests.map((request) => (
                    <div key={request.id} className="request-card">
                      <div className="request-header">
                        <span className="request-type">{request.request_type}</span>
                        <span 
                          className="priority-badge"
                          style={{ backgroundColor: getPriorityColor(request.priority) }}
                        >
                          {request.priority}
                        </span>
                      </div>
                      <div className="request-dates">
                        {formatDate(request.start_date)} ~ {formatDate(request.end_date)}
                      </div>
                      {request.shift_type && (
                        <div className="shift-type">희망 근무: {request.shift_type}</div>
                      )}
                      <div className="request-reason">{request.reason}</div>
                      <div className="request-status">
                        <span 
                          className="status-badge"
                          style={{ backgroundColor: getStatusColor(request.status || 'pending') }}
                        >
                          {request.status || 'pending'}
                        </span>
                        {request.admin_notes && (
                          <div className="admin-notes">관리자 메모: {request.admin_notes}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-requests">요청이 없습니다.</div>
              )}
            </div>

            {wardId && (
              <div className="pending-requests">
                <h3>대기 중인 요청 ({pendingRequests.length})</h3>
                {pendingRequests.length > 0 ? (
                  <div className="requests-grid">
                    {pendingRequests.map((request) => (
                      <div key={request.id} className="request-card">
                        <div className="request-header">
                          <span className="employee-name">{request.employee_name}</span>
                          <span 
                            className="priority-badge"
                            style={{ backgroundColor: getPriorityColor(request.priority) }}
                          >
                            {request.priority}
                          </span>
                        </div>
                        <div className="request-type">{request.request_type}</div>
                        <div className="request-dates">
                          {formatDate(request.start_date)} ~ {formatDate(request.end_date)}
                        </div>
                        {request.shift_type && (
                          <div className="shift-type">희망 근무: {request.shift_type}</div>
                        )}
                        <div className="request-reason">{request.reason}</div>
                        {request.medical_reason && (
                          <div className="medical-badge">🏥 의료적 사유</div>
                        )}
                        <div className="request-actions">
                          <button
                            onClick={() => handleReviewRequest(request.id!, 'approved')}
                            className="btn-approve"
                            disabled={loading}
                          >
                            승인
                          </button>
                          <button
                            onClick={() => handleReviewRequest(request.id!, 'partially_approved', '부분 승인')}
                            className="btn-partial"
                            disabled={loading}
                          >
                            부분승인
                          </button>
                          <button
                            onClick={() => handleReviewRequest(request.id!, 'denied', '거부')}
                            className="btn-deny"
                            disabled={loading}
                          >
                            거부
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-requests">대기 중인 요청이 없습니다.</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'dashboard' && wardId && (
        <div className="dashboard-section">
          <h2>선호도 관리 대시보드</h2>
          {dashboardData ? (
            <div className="dashboard-cards">
              <div className="stat-card">
                <h3>직원 현황</h3>
                <div className="stat-number">{dashboardData.total_employees}</div>
                <div className="stat-label">총 직원 수</div>
              </div>
              <div className="stat-card">
                <h3>선호도 설정률</h3>
                <div className="stat-number">{dashboardData.preferences_set_rate.toFixed(1)}%</div>
                <div className="stat-label">{dashboardData.preferences_set_count}/{dashboardData.total_employees} 명 설정 완료</div>
              </div>
              <div className="stat-card">
                <h3>대기 중인 요청</h3>
                <div className="stat-number">{dashboardData.pending_requests}</div>
                <div className="stat-label">처리 대기</div>
              </div>
              <div className="stat-card">
                <h3>긴급 요청</h3>
                <div className="stat-number urgent">{dashboardData.urgent_requests}</div>
                <div className="stat-label">즉시 처리 필요</div>
              </div>
              <div className="stat-card">
                <h3>의료적 요청</h3>
                <div className="stat-number medical">{dashboardData.medical_requests}</div>
                <div className="stat-label">의료 사유</div>
              </div>
            </div>
          ) : (
            <div className="loading">대시보드 데이터를 불러오는 중...</div>
          )}
        </div>
      )}

      <style jsx>{`
        .preference-management {
          padding: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .tabs {
          display: flex;
          gap: 10px;
          margin-bottom: 30px;
          border-bottom: 2px solid #e0e0e0;
        }

        .tabs button {
          padding: 12px 24px;
          border: none;
          background: transparent;
          border-bottom: 3px solid transparent;
          cursor: pointer;
          font-size: 16px;
          transition: all 0.3s;
        }

        .tabs button.active {
          border-bottom-color: #3498db;
          color: #3498db;
          font-weight: 600;
        }

        .section-header {
          display: flex;
          justify-content: between;
          align-items: center;
          margin-bottom: 20px;
        }

        .header-controls {
          display: flex;
          gap: 10px;
        }

        .preferences-form {
          background: #f8f9fa;
          padding: 25px;
          border-radius: 10px;
          margin-bottom: 20px;
        }

        .form-section {
          margin-bottom: 25px;
        }

        .form-section h3 {
          margin-bottom: 15px;
          color: #2c3e50;
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 15px;
        }

        .form-group {
          margin-bottom: 15px;
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

        .checkbox-group {
          display: flex;
          gap: 20px;
        }

        .checkbox-group label {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .form-actions {
          display: flex;
          gap: 10px;
          justify-content: flex-end;
        }

        .preferences-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 20px;
        }

        .preference-card {
          background: white;
          padding: 20px;
          border-radius: 8px;
          border: 1px solid #e0e0e0;
        }

        .preference-card h3 {
          margin-bottom: 15px;
          color: #2c3e50;
        }

        .preference-item {
          margin-bottom: 10px;
          padding-bottom: 10px;
          border-bottom: 1px solid #f0f0f0;
        }

        .no-preferences {
          text-align: center;
          padding: 40px;
          background: #f8f9fa;
          border-radius: 8px;
        }

        .request-form {
          background: #f8f9fa;
          padding: 25px;
          border-radius: 10px;
          margin-bottom: 30px;
        }

        .range-labels {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: #666;
        }

        .requests-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 20px;
        }

        .request-card {
          background: white;
          padding: 20px;
          border-radius: 8px;
          border: 1px solid #e0e0e0;
        }

        .request-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .priority-badge,
        .status-badge {
          padding: 4px 8px;
          border-radius: 12px;
          color: white;
          font-size: 12px;
          font-weight: 500;
        }

        .request-actions {
          display: flex;
          gap: 8px;
          margin-top: 15px;
        }

        .btn-approve { background: #28a745; color: white; }
        .btn-partial { background: #fd7e14; color: white; }
        .btn-deny { background: #dc3545; color: white; }

        .dashboard-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
        }

        .stat-card {
          background: white;
          padding: 25px;
          border-radius: 10px;
          text-align: center;
          border: 1px solid #e0e0e0;
        }

        .stat-number {
          font-size: 2.5em;
          font-weight: bold;
          color: #3498db;
        }

        .stat-number.urgent {
          color: #e74c3c;
        }

        .stat-number.medical {
          color: #f39c12;
        }

        .stat-label {
          margin-top: 10px;
          color: #7f8c8d;
          font-size: 14px;
        }

        .btn-primary {
          background: #3498db;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 5px;
          cursor: pointer;
        }

        .btn-secondary {
          background: #95a5a6;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 5px;
          cursor: pointer;
        }

        .loading {
          text-align: center;
          padding: 20px;
          color: #666;
        }

        .no-requests {
          text-align: center;
          padding: 20px;
          color: #666;
          background: #f8f9fa;
          border-radius: 8px;
        }

        .medical-badge {
          background: #fff3cd;
          color: #856404;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          margin-top: 8px;
          display: inline-block;
        }

        .admin-notes {
          background: #e9ecef;
          padding: 8px;
          border-radius: 4px;
          margin-top: 8px;
          font-size: 12px;
        }
      `}</style>
    </div>
  );
};

export default PreferenceManagement;