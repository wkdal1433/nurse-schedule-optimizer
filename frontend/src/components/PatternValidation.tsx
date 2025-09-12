import React, { useState, useEffect } from 'react';
import { 
  ShiftPattern, 
  PatternViolation, 
  PatternValidationResult, 
  FatigueAnalysis,
  patternsAPI 
} from '../services/api';

interface PatternValidationProps {
  wardId: number;
}

const PatternValidation: React.FC<PatternValidationProps> = ({ wardId }) => {
  const [activeTab, setActiveTab] = useState('patterns');
  const [patterns, setPatterns] = useState<ShiftPattern[]>([]);
  const [violations, setViolations] = useState<PatternViolation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 패턴 규칙 관리 상태
  const [showPatternForm, setShowPatternForm] = useState(false);
  const [editingPattern, setEditingPattern] = useState<ShiftPattern | null>(null);
  const [patternForm, setPatternForm] = useState({
    pattern_name: '',
    pattern_type: 'forbidden' as 'forbidden' | 'discouraged' | 'preferred',
    description: '',
    sequence_length: 2,
    pattern_definition: {},
    penalty_score: 0,
    severity: 'medium' as 'low' | 'medium' | 'high' | 'critical',
    ward_id: wardId,
    role_specific: [] as string[]
  });

  // 패턴 검증 상태
  const [validationEmployeeId, setValidationEmployeeId] = useState<number>(1);
  const [validationResult, setValidationResult] = useState<PatternValidationResult | null>(null);
  const [scheduleId, setScheduleId] = useState<number>(1);
  
  // 피로도 분석 상태
  const [fatigueEmployeeId, setFatigueEmployeeId] = useState<number>(1);
  const [fatigueResult, setFatigueResult] = useState<FatigueAnalysis | null>(null);
  const [analysisPeriod, setAnalysisPeriod] = useState({
    start: '2024-01-01',
    end: '2024-01-31'
  });

  useEffect(() => {
    loadPatterns();
  }, [wardId]);

  const loadPatterns = async () => {
    try {
      setLoading(true);
      const response = await patternsAPI.getPatterns(wardId);
      setPatterns(response.data);
    } catch (err: any) {
      setError('패턴 로딩 중 오류가 발생했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDefaultPatterns = async () => {
    try {
      setLoading(true);
      await patternsAPI.createDefaultPatterns(wardId);
      alert('기본 패턴이 성공적으로 생성되었습니다!');
      loadPatterns();
    } catch (err: any) {
      alert('기본 패턴 생성 중 오류가 발생했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSavePattern = async () => {
    try {
      setLoading(true);
      if (editingPattern) {
        await patternsAPI.updatePattern(editingPattern.id!, patternForm);
        alert('패턴이 성공적으로 수정되었습니다!');
      } else {
        await patternsAPI.createPattern(patternForm);
        alert('패턴이 성공적으로 생성되었습니다!');
      }
      
      setShowPatternForm(false);
      setEditingPattern(null);
      resetPatternForm();
      loadPatterns();
    } catch (err: any) {
      alert('패턴 저장 중 오류가 발생했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePattern = async (patternId: number) => {
    if (!confirm('정말로 이 패턴을 삭제하시겠습니까?')) return;
    
    try {
      setLoading(true);
      await patternsAPI.deletePattern(patternId);
      alert('패턴이 성공적으로 삭제되었습니다!');
      loadPatterns();
    } catch (err: any) {
      alert('패턴 삭제 중 오류가 발생했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleEditPattern = (pattern: ShiftPattern) => {
    setEditingPattern(pattern);
    setPatternForm({
      pattern_name: pattern.pattern_name,
      pattern_type: pattern.pattern_type,
      description: pattern.description || '',
      sequence_length: pattern.sequence_length,
      pattern_definition: pattern.pattern_definition,
      penalty_score: pattern.penalty_score,
      severity: pattern.severity,
      ward_id: pattern.ward_id || wardId,
      role_specific: pattern.role_specific || []
    });
    setShowPatternForm(true);
  };

  const resetPatternForm = () => {
    setPatternForm({
      pattern_name: '',
      pattern_type: 'forbidden',
      description: '',
      sequence_length: 2,
      pattern_definition: {},
      penalty_score: 0,
      severity: 'medium',
      ward_id: wardId,
      role_specific: []
    });
  };

  const handleValidateSchedule = async () => {
    try {
      setLoading(true);
      const response = await patternsAPI.validateSchedulePatterns(scheduleId);
      setValidationResult(response.data);
    } catch (err: any) {
      alert('스케줄 검증 중 오류가 발생했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeFatigue = async () => {
    try {
      setLoading(true);
      const response = await patternsAPI.analyzeFatigue(
        fatigueEmployeeId, 
        analysisPeriod.start, 
        analysisPeriod.end
      );
      setFatigueResult(response.data);
    } catch (err: any) {
      alert('피로도 분석 중 오류가 발생했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const loadViolations = async () => {
    try {
      setLoading(true);
      const response = await patternsAPI.getPatternViolations(scheduleId);
      setViolations(response.data.violations);
    } catch (err: any) {
      setError('위반사항 로딩 중 오류가 발생했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'forbidden': return '#dc3545';
      case 'discouraged': return '#ffc107';
      case 'preferred': return '#28a745';
      default: return '#6c757d';
    }
  };

  if (loading && patterns.length === 0) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>로딩 중...</div>;
  }

  return (
    <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>🔍 근무 패턴 검증 시스템</h2>
        <button
          onClick={handleCreateDefaultPatterns}
          style={{
            padding: '8px 16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          기본 패턴 생성
        </button>
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
          { id: 'patterns', label: '📋 패턴 규칙' },
          { id: 'validation', label: '✅ 패턴 검증' },
          { id: 'violations', label: '⚠️ 위반사항' },
          { id: 'fatigue', label: '😴 피로도 분석' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
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

      {/* 패턴 규칙 관리 탭 */}
      {activeTab === 'patterns' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3>패턴 규칙 관리</h3>
            <button
              onClick={() => setShowPatternForm(true)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              새 패턴 추가
            </button>
          </div>

          {/* 패턴 목록 */}
          <div style={{ display: 'grid', gap: '10px' }}>
            {patterns.map((pattern) => (
              <div
                key={pattern.id}
                style={{
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  padding: '15px',
                  backgroundColor: '#f8f9fa'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h4 style={{ margin: '0 0 5px 0' }}>
                      {pattern.pattern_name}
                      <span 
                        style={{ 
                          backgroundColor: getTypeColor(pattern.pattern_type),
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          marginLeft: '10px'
                        }}
                      >
                        {pattern.pattern_type}
                      </span>
                      <span 
                        style={{ 
                          backgroundColor: getSeverityColor(pattern.severity),
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          marginLeft: '5px'
                        }}
                      >
                        {pattern.severity}
                      </span>
                    </h4>
                    <p style={{ margin: '5px 0', color: '#6c757d' }}>{pattern.description}</p>
                    <div style={{ fontSize: '14px', color: '#868e96' }}>
                      <span>패널티 점수: {pattern.penalty_score}</span>
                      <span style={{ marginLeft: '15px' }}>시퀀스 길이: {pattern.sequence_length}</span>
                    </div>
                  </div>
                  <div>
                    <button
                      onClick={() => handleEditPattern(pattern)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#ffc107',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        marginRight: '5px',
                        fontSize: '12px'
                      }}
                    >
                      수정
                    </button>
                    <button
                      onClick={() => handleDeletePattern(pattern.id!)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#dc3545',
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
                </div>
              </div>
            ))}
          </div>

          {/* 패턴 생성/수정 폼 */}
          {showPatternForm && (
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
                width: '500px',
                maxHeight: '80vh',
                overflow: 'auto'
              }}>
                <h3>{editingPattern ? '패턴 수정' : '새 패턴 추가'}</h3>
                
                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px' }}>패턴 이름</label>
                  <input
                    type="text"
                    value={patternForm.pattern_name}
                    onChange={(e) => setPatternForm({...patternForm, pattern_name: e.target.value})}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                </div>

                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px' }}>패턴 유형</label>
                  <select
                    value={patternForm.pattern_type}
                    onChange={(e) => setPatternForm({...patternForm, pattern_type: e.target.value as any})}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  >
                    <option value="forbidden">금지 패턴</option>
                    <option value="discouraged">지양 패턴</option>
                    <option value="preferred">선호 패턴</option>
                  </select>
                </div>

                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px' }}>설명</label>
                  <textarea
                    value={patternForm.description}
                    onChange={(e) => setPatternForm({...patternForm, description: e.target.value})}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', height: '80px' }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>패널티 점수</label>
                    <input
                      type="number"
                      value={patternForm.penalty_score}
                      onChange={(e) => setPatternForm({...patternForm, penalty_score: parseFloat(e.target.value) || 0})}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>심각도</label>
                    <select
                      value={patternForm.severity}
                      onChange={(e) => setPatternForm({...patternForm, severity: e.target.value as any})}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="low">낮음</option>
                      <option value="medium">보통</option>
                      <option value="high">높음</option>
                      <option value="critical">위험</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => {
                      setShowPatternForm(false);
                      setEditingPattern(null);
                      resetPatternForm();
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
                    취소
                  </button>
                  <button
                    onClick={handleSavePattern}
                    disabled={!patternForm.pattern_name}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#007bff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: patternForm.pattern_name ? 'pointer' : 'not-allowed',
                      opacity: patternForm.pattern_name ? 1 : 0.5
                    }}
                  >
                    저장
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 패턴 검증 탭 */}
      {activeTab === 'validation' && (
        <div>
          <h3>패턴 검증</h3>
          
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', alignItems: 'end' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px' }}>스케줄 ID</label>
              <input
                type="number"
                value={scheduleId}
                onChange={(e) => setScheduleId(parseInt(e.target.value) || 1)}
                style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <button
              onClick={handleValidateSchedule}
              style={{
                padding: '8px 16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              스케줄 검증
            </button>
          </div>

          {validationResult && (
            <div style={{ 
              border: '1px solid #dee2e6', 
              borderRadius: '4px', 
              padding: '15px',
              backgroundColor: validationResult.is_valid ? '#d4edda' : '#f8d7da'
            }}>
              <h4>검증 결과</h4>
              <p><strong>전체 점수:</strong> {validationResult.overall_score}/100</p>
              <p><strong>총 위반사항:</strong> {validationResult.total_violations}개</p>
              <p><strong>상태:</strong> {validationResult.is_valid ? '✅ 안전함' : '⚠️ 개선 필요'}</p>
              <p><strong>요약:</strong> {validationResult.summary}</p>
            </div>
          )}
        </div>
      )}

      {/* 위반사항 탭 */}
      {activeTab === 'violations' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3>패턴 위반사항</h3>
            <button
              onClick={loadViolations}
              style={{
                padding: '8px 16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              위반사항 조회
            </button>
          </div>

          <div style={{ display: 'grid', gap: '10px' }}>
            {violations.map((violation) => (
              <div
                key={violation.id}
                style={{
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  padding: '15px',
                  backgroundColor: violation.is_resolved ? '#d4edda' : '#fff3cd'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h4 style={{ margin: '0 0 5px 0' }}>
                      {violation.pattern_name}
                      <span 
                        style={{ 
                          backgroundColor: getSeverityColor(violation.severity),
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          marginLeft: '10px'
                        }}
                      >
                        {violation.severity}
                      </span>
                    </h4>
                    <p style={{ margin: '5px 0', color: '#6c757d' }}>{violation.description}</p>
                    <div style={{ fontSize: '14px', color: '#868e96' }}>
                      <span>직원 ID: {violation.employee_id}</span>
                      <span style={{ marginLeft: '15px' }}>기간: {violation.violation_date_start} ~ {violation.violation_date_end}</span>
                      <span style={{ marginLeft: '15px' }}>패널티: {violation.penalty_score}</span>
                    </div>
                  </div>
                  <div>
                    {violation.is_resolved ? (
                      <span style={{ color: '#28a745', fontWeight: 'bold' }}>✅ 해결됨</span>
                    ) : (
                      <span style={{ color: '#ffc107', fontWeight: 'bold' }}>⚠️ 미해결</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {violations.length === 0 && (
            <p style={{ textAlign: 'center', color: '#6c757d', padding: '40px' }}>
              위반사항이 없습니다.
            </p>
          )}
        </div>
      )}

      {/* 피로도 분석 탭 */}
      {activeTab === 'fatigue' && (
        <div>
          <h3>피로도 분석</h3>
          
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', alignItems: 'end' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px' }}>직원 ID</label>
              <input
                type="number"
                value={fatigueEmployeeId}
                onChange={(e) => setFatigueEmployeeId(parseInt(e.target.value) || 1)}
                style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px' }}>시작일</label>
              <input
                type="date"
                value={analysisPeriod.start}
                onChange={(e) => setAnalysisPeriod({...analysisPeriod, start: e.target.value})}
                style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px' }}>종료일</label>
              <input
                type="date"
                value={analysisPeriod.end}
                onChange={(e) => setAnalysisPeriod({...analysisPeriod, end: e.target.value})}
                style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <button
              onClick={handleAnalyzeFatigue}
              style={{
                padding: '8px 16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              피로도 분석
            </button>
          </div>

          {fatigueResult && (
            <div style={{ 
              border: '1px solid #dee2e6', 
              borderRadius: '4px', 
              padding: '15px',
              backgroundColor: '#f8f9fa'
            }}>
              <h4>피로도 분석 결과</h4>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
                <strong>피로도 점수: {fatigueResult.total_fatigue_score}/100</strong>
                <span 
                  style={{ 
                    backgroundColor: getSeverityColor(fatigueResult.risk_level),
                    color: 'white',
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '14px',
                    marginLeft: '15px'
                  }}
                >
                  위험도: {fatigueResult.risk_level}
                </span>
              </div>
              <p><strong>권장 휴게일:</strong> {fatigueResult.rest_days_needed}일</p>
              
              <div style={{ marginTop: '15px' }}>
                <strong>권장사항:</strong>
                <ul style={{ marginTop: '5px' }}>
                  {fatigueResult.recommendations.map((rec, index) => (
                    <li key={index} style={{ margin: '5px 0' }}>{rec}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PatternValidation;