import React, { useState } from 'react';

interface Nurse {
  id: number;
  name: string;
  role: string;
  employment_type: string;
  experience_level: number;
}

interface EmergencyOverrideProps {
  scheduleId: number;
  selectedDate: string;
  selectedShift: string;
  nurses: Nurse[];
  onClose: () => void;
  onSuccess: (result: any) => void;
}

interface Recommendation {
  employee_id: number;
  employee_name: string;
  employee_role: string;
  employment_type: string;
  experience_level: number;
  suitability_score: number;
  reasons: string[];
  estimated_impact: {
    score_improvement: number;
    constraint_satisfaction: string;
  };
}

const EmergencyOverride: React.FC<EmergencyOverrideProps> = ({
  scheduleId,
  selectedDate,
  selectedShift,
  nurses,
  onClose,
  onSuccess
}) => {
  const [overrideType, setOverrideType] = useState<'emergency' | 'admin' | 'urgent'>('emergency');
  const [reason, setReason] = useState('');
  const [removeEmployeeId, setRemoveEmployeeId] = useState<number | null>(null);
  const [addEmployeeId, setAddEmployeeId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAIRecommendations, setShowAIRecommendations] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [alternatives, setAlternatives] = useState<any[]>([]);

  const handleEmergencyOverride = async () => {
    if (!reason.trim()) {
      alert('긴급상황 사유를 입력해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`/api/schedules/${scheduleId}/emergency-override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schedule_id: scheduleId,
          date: selectedDate,
          shift: selectedShift,
          remove_employee_id: removeEmployeeId,
          add_employee_id: addEmployeeId,
          reason: reason,
          override_type: overrideType
        })
      });

      const result = await response.json();

      if (result.success) {
        onSuccess(result);
        onClose();
      } else {
        alert('긴급 오버라이드 실패: ' + result.message);
      }
    } catch (error) {
      console.error('Emergency override error:', error);
      alert('긴급 오버라이드 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const getAIRecommendations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/schedules/${scheduleId}/ai-recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schedule_id: scheduleId,
          date: selectedDate,
          shift: selectedShift,
          issue_type: 'missing_staff',
          include_alternatives: true
        })
      });

      const result = await response.json();

      if (result.success) {
        setRecommendations(result.recommendations || []);
        setAlternatives(result.alternatives || []);
        setShowAIRecommendations(true);
      } else {
        alert('AI 추천 조회 실패');
      }
    } catch (error) {
      console.error('AI recommendation error:', error);
      alert('AI 추천 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const selectRecommendation = (recommendation: Recommendation) => {
    setAddEmployeeId(recommendation.employee_id);
    setReason(`AI 추천: ${recommendation.employee_name} (${recommendation.reasons.join(', ')})`);
    setShowAIRecommendations(false);
  };

  return (
    <div className="emergency-override-modal">
      <div className="modal-backdrop" onClick={onClose}></div>
      <div className="modal-content">
        <div className="modal-header">
          <h2>🚨 긴급 오버라이드</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="override-info">
          <div className="info-item">
            <span className="label">날짜:</span>
            <span className="value">{selectedDate}</span>
          </div>
          <div className="info-item">
            <span className="label">교대:</span>
            <span className="value">{selectedShift}</span>
          </div>
        </div>

        {!showAIRecommendations ? (
          <div className="override-form">
            <div className="form-group">
              <label>오버라이드 유형</label>
              <select
                value={overrideType}
                onChange={(e) => setOverrideType(e.target.value as any)}
              >
                <option value="emergency">긴급상황</option>
                <option value="admin">관리자 결정</option>
                <option value="urgent">긴급 업무</option>
              </select>
            </div>

            <div className="form-group">
              <label>제거할 간호사</label>
              <select
                value={removeEmployeeId || ''}
                onChange={(e) => setRemoveEmployeeId(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">선택하지 않음</option>
                {nurses.map(nurse => (
                  <option key={nurse.id} value={nurse.id}>
                    {nurse.name} ({nurse.role})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>추가할 간호사</label>
              <select
                value={addEmployeeId || ''}
                onChange={(e) => setAddEmployeeId(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">선택하지 않음</option>
                {nurses.map(nurse => (
                  <option key={nurse.id} value={nurse.id}>
                    {nurse.name} ({nurse.role})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>긴급상황 사유 *</label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="긴급상황의 구체적인 사유를 입력해주세요..."
                rows={3}
                required
              />
            </div>

            <div className="action-buttons">
              <button
                className="ai-recommend-button"
                onClick={getAIRecommendations}
                disabled={isLoading}
              >
                🤖 AI 추천 받기
              </button>

              <button
                className="override-button emergency"
                onClick={handleEmergencyOverride}
                disabled={isLoading || !reason.trim()}
              >
                {isLoading ? '처리중...' : '긴급 오버라이드 실행'}
              </button>
            </div>

            <div className="warning-notice">
              ⚠️ 긴급 오버라이드는 모든 제약조건을 무시하고 강제 적용됩니다.
              <br />
              긴급상황 해결 후 반드시 수동 검토가 필요합니다.
            </div>
          </div>
        ) : (
          <div className="ai-recommendations">
            <div className="recommendations-header">
              <h3>🤖 AI 추천 간호사</h3>
              <button
                className="back-button"
                onClick={() => setShowAIRecommendations(false)}
              >
                ← 돌아가기
              </button>
            </div>

            <div className="recommendations-list">
              {recommendations.map((rec, index) => (
                <div
                  key={rec.employee_id}
                  className="recommendation-card"
                  onClick={() => selectRecommendation(rec)}
                >
                  <div className="rec-header">
                    <span className="rec-rank">#{index + 1}</span>
                    <span className="rec-name">{rec.employee_name}</span>
                    <span className="rec-score">{Math.round(rec.suitability_score * 100)}%</span>
                  </div>

                  <div className="rec-details">
                    <div className="rec-info">
                      <span>{rec.employee_role}</span>
                      <span>{rec.employment_type}</span>
                      <span>경력 {rec.experience_level}년</span>
                    </div>

                    <div className="rec-reasons">
                      {rec.reasons.map((reason, idx) => (
                        <span key={idx} className="reason-tag">{reason}</span>
                      ))}
                    </div>

                    <div className="rec-impact">
                      점수 개선: +{rec.estimated_impact.score_improvement.toFixed(1)}
                      <span className={`constraint-level ${rec.estimated_impact.constraint_satisfaction}`}>
                        {rec.estimated_impact.constraint_satisfaction}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {alternatives.length > 0 && (
              <div className="alternatives-section">
                <h4>대안 시나리오</h4>
                <div className="alternatives-list">
                  {alternatives.map((alt, index) => (
                    <div key={index} className="alternative-card">
                      <div className="alt-name">{alt.scenario_name}</div>
                      <div className="alt-description">{alt.description}</div>
                      <div className="alt-details">
                        <span className={`feasibility ${alt.feasibility}`}>
                          실현가능성: {alt.feasibility}
                        </span>
                        <span>비용영향: {alt.cost_impact}</span>
                        <span>소요시간: {alt.time_to_implement}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        .emergency-override-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .modal-backdrop {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          width: 90%;
          max-width: 600px;
          max-height: 80vh;
          overflow-y: auto;
          position: relative;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .modal-header h2 {
          margin: 0;
          color: #dc2626;
          font-size: 18px;
        }

        .close-button {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #6b7280;
        }

        .override-info {
          padding: 16px 20px;
          background: #fef2f2;
          border-bottom: 1px solid #fecaca;
        }

        .info-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        .info-item:last-child {
          margin-bottom: 0;
        }

        .label {
          font-weight: 600;
          color: #374151;
        }

        .value {
          color: #dc2626;
          font-weight: 500;
        }

        .override-form {
          padding: 20px;
        }

        .form-group {
          margin-bottom: 16px;
        }

        .form-group label {
          display: block;
          font-weight: 600;
          margin-bottom: 4px;
          color: #374151;
        }

        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
          font-family: inherit;
        }

        .form-group textarea {
          resize: vertical;
          min-height: 80px;
        }

        .action-buttons {
          display: flex;
          gap: 12px;
          margin-top: 20px;
        }

        .ai-recommend-button {
          flex: 1;
          padding: 10px 16px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }

        .ai-recommend-button:hover {
          background: #2563eb;
        }

        .override-button {
          flex: 2;
          padding: 10px 16px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
        }

        .override-button.emergency {
          background: #dc2626;
          color: white;
        }

        .override-button.emergency:hover {
          background: #b91c1c;
        }

        .override-button:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }

        .warning-notice {
          margin-top: 16px;
          padding: 12px;
          background: #fef3c7;
          border: 1px solid #f59e0b;
          border-radius: 6px;
          font-size: 13px;
          color: #92400e;
        }

        .ai-recommendations {
          padding: 20px;
        }

        .recommendations-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .recommendations-header h3 {
          margin: 0;
          color: #374151;
        }

        .back-button {
          background: #e5e7eb;
          border: none;
          padding: 6px 12px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .recommendations-list {
          max-height: 300px;
          overflow-y: auto;
        }

        .recommendation-card {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .recommendation-card:hover {
          border-color: #3b82f6;
          background: #f8fafc;
        }

        .rec-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .rec-rank {
          background: #3b82f6;
          color: white;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
        }

        .rec-name {
          font-weight: 600;
          color: #374151;
        }

        .rec-score {
          background: #10b981;
          color: white;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
        }

        .rec-details {
          font-size: 13px;
        }

        .rec-info {
          display: flex;
          gap: 8px;
          margin-bottom: 6px;
          color: #6b7280;
        }

        .rec-reasons {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-bottom: 6px;
        }

        .reason-tag {
          background: #e0e7ff;
          color: #3730a3;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 11px;
        }

        .rec-impact {
          display: flex;
          justify-content: space-between;
          align-items: center;
          color: #059669;
          font-weight: 500;
        }

        .constraint-level {
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
        }

        .constraint-level.high {
          background: #d1fae5;
          color: #065f46;
        }

        .constraint-level.medium {
          background: #fef3c7;
          color: #92400e;
        }

        .constraint-level.low {
          background: #fee2e2;
          color: #991b1b;
        }

        .alternatives-section {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid #e5e7eb;
        }

        .alternatives-section h4 {
          margin: 0 0 12px 0;
          color: #374151;
        }

        .alternative-card {
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          padding: 10px;
          margin-bottom: 8px;
        }

        .alt-name {
          font-weight: 600;
          color: #374151;
          margin-bottom: 4px;
        }

        .alt-description {
          font-size: 13px;
          color: #6b7280;
          margin-bottom: 6px;
        }

        .alt-details {
          display: flex;
          gap: 8px;
          font-size: 12px;
        }

        .alt-details span {
          padding: 2px 6px;
          border-radius: 4px;
          background: #f3f4f6;
          color: #374151;
        }

        .feasibility.high {
          background: #d1fae5;
          color: #065f46;
        }

        .feasibility.medium {
          background: #fef3c7;
          color: #92400e;
        }

        .feasibility.low {
          background: #fee2e2;
          color: #991b1b;
        }
      `}</style>
    </div>
  );
};

export default EmergencyOverride;