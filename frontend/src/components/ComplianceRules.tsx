import React, { useState, useEffect } from 'react';
import { complianceAPI, ShiftRule } from '../services/api';

interface ComplianceRulesProps {
  wardId?: number;
}

const ComplianceRules: React.FC<ComplianceRulesProps> = ({ wardId }) => {
  const [rules, setRules] = useState<ShiftRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingRule, setEditingRule] = useState<ShiftRule | null>(null);
  const [showForm, setShowForm] = useState(false);

  const defaultRule: Omit<ShiftRule, 'id'> = {
    ward_id: wardId,
    rule_name: '',
    rule_type: 'hard',
    category: 'consecutive',
    max_consecutive_nights: 3,
    max_consecutive_days: 5,
    min_rest_days_per_week: 1,
    max_hours_per_week: 40,
    forbidden_patterns: [],
    penalty_weight: 1.0,
  };

  const [formData, setFormData] = useState<Omit<ShiftRule, 'id'>>(defaultRule);

  useEffect(() => {
    fetchRules();
  }, [wardId]);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const response = await complianceAPI.getRules(wardId);
      setRules(response.data);
    } catch (error) {
      console.error('규칙 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (editingRule) {
        await complianceAPI.updateRule(editingRule.id!, formData);
      } else {
        await complianceAPI.createRule(formData);
      }
      
      fetchRules();
      resetForm();
    } catch (error) {
      console.error('규칙 저장 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (rule: ShiftRule) => {
    setEditingRule(rule);
    setFormData({ ...rule });
    setShowForm(true);
  };

  const handleDelete = async (ruleId: number) => {
    if (!window.confirm('이 규칙을 삭제하시겠습니까?')) return;
    
    setLoading(true);
    try {
      await complianceAPI.deleteRule(ruleId);
      fetchRules();
    } catch (error) {
      console.error('규칙 삭제 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const createDefaultRules = async () => {
    if (!wardId || !window.confirm('기본 규칙을 생성하시겠습니까?')) return;
    
    setLoading(true);
    try {
      await complianceAPI.createDefaultRules(wardId);
      fetchRules();
    } catch (error) {
      console.error('기본 규칙 생성 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData(defaultRule);
    setEditingRule(null);
    setShowForm(false);
  };

  const updateForbiddenPatterns = (patterns: string) => {
    const patternArray = patterns.split(',').map(p => p.trim()).filter(p => p);
    setFormData({ ...formData, forbidden_patterns: patternArray });
  };

  return (
    <div className="compliance-rules">
      <div className="rules-header">
        <h2>근무 규칙 관리</h2>
        <div className="header-actions">
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            {showForm ? '취소' : '새 규칙 추가'}
          </button>
          {wardId && (
            <button onClick={createDefaultRules} className="btn-secondary">
              기본 규칙 생성
            </button>
          )}
        </div>
      </div>

      {showForm && (
        <div className="rule-form">
          <h3>{editingRule ? '규칙 수정' : '새 규칙 추가'}</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>규칙 이름</label>
                <input
                  type="text"
                  value={formData.rule_name}
                  onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>규칙 유형</label>
                <select
                  value={formData.rule_type}
                  onChange={(e) => setFormData({ ...formData, rule_type: e.target.value as 'hard' | 'soft' })}
                >
                  <option value="hard">Hard (필수)</option>
                  <option value="soft">Soft (권장)</option>
                </select>
              </div>

              <div className="form-group">
                <label>카테고리</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value as any })}
                >
                  <option value="consecutive">연속 근무</option>
                  <option value="weekly">주간 제한</option>
                  <option value="legal">법정 시간</option>
                  <option value="pattern">근무 패턴</option>
                </select>
              </div>

              <div className="form-group">
                <label>최대 연속 야간근무 (일)</label>
                <input
                  type="number"
                  min="1"
                  max="7"
                  value={formData.max_consecutive_nights}
                  onChange={(e) => setFormData({ ...formData, max_consecutive_nights: parseInt(e.target.value) })}
                />
              </div>

              <div className="form-group">
                <label>최대 연속 근무일 (일)</label>
                <input
                  type="number"
                  min="1"
                  max="14"
                  value={formData.max_consecutive_days}
                  onChange={(e) => setFormData({ ...formData, max_consecutive_days: parseInt(e.target.value) })}
                />
              </div>

              <div className="form-group">
                <label>주간 최소 휴무일</label>
                <input
                  type="number"
                  min="0"
                  max="7"
                  value={formData.min_rest_days_per_week}
                  onChange={(e) => setFormData({ ...formData, min_rest_days_per_week: parseInt(e.target.value) })}
                />
              </div>

              <div className="form-group">
                <label>주간 최대 근무시간</label>
                <input
                  type="number"
                  min="0"
                  max="60"
                  value={formData.max_hours_per_week}
                  onChange={(e) => setFormData({ ...formData, max_hours_per_week: parseInt(e.target.value) })}
                />
              </div>

              <div className="form-group">
                <label>금지 패턴 (콤마로 구분)</label>
                <input
                  type="text"
                  placeholder="day->night, night->day"
                  value={formData.forbidden_patterns.join(', ')}
                  onChange={(e) => updateForbiddenPatterns(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>패널티 가중치</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="5"
                  value={formData.penalty_weight}
                  onChange={(e) => setFormData({ ...formData, penalty_weight: parseFloat(e.target.value) })}
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" disabled={loading} className="btn-primary">
                {loading ? '저장 중...' : editingRule ? '수정' : '생성'}
              </button>
              <button type="button" onClick={resetForm} className="btn-secondary">
                취소
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="rules-list">
        <h3>현재 규칙 ({rules.length}개)</h3>
        {loading ? (
          <div className="loading">로딩 중...</div>
        ) : (
          <div className="rules-grid">
            {rules.map((rule) => (
              <div key={rule.id} className="rule-card">
                <div className="rule-header">
                  <h4>{rule.rule_name}</h4>
                  <div className="rule-badges">
                    <span className={`badge ${rule.rule_type}`}>{rule.rule_type}</span>
                    <span className={`badge ${rule.category}`}>{rule.category}</span>
                  </div>
                </div>
                
                <div className="rule-details">
                  <div className="detail-row">
                    <span>최대 연속 야간:</span>
                    <strong>{rule.max_consecutive_nights}일</strong>
                  </div>
                  <div className="detail-row">
                    <span>최대 연속 근무:</span>
                    <strong>{rule.max_consecutive_days}일</strong>
                  </div>
                  <div className="detail-row">
                    <span>주간 최소 휴무:</span>
                    <strong>{rule.min_rest_days_per_week}일</strong>
                  </div>
                  <div className="detail-row">
                    <span>주간 최대 시간:</span>
                    <strong>{rule.max_hours_per_week}시간</strong>
                  </div>
                  {rule.forbidden_patterns && rule.forbidden_patterns.length > 0 && (
                    <div className="detail-row">
                      <span>금지 패턴:</span>
                      <strong>{rule.forbidden_patterns.join(', ')}</strong>
                    </div>
                  )}
                </div>

                <div className="rule-actions">
                  <button onClick={() => handleEdit(rule)} className="btn-edit">
                    수정
                  </button>
                  <button onClick={() => handleDelete(rule.id!)} className="btn-delete">
                    삭제
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .compliance-rules {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .rules-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .header-actions {
          display: flex;
          gap: 10px;
        }

        .rule-form {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 30px;
        }

        .form-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
        }

        .form-group input,
        .form-group select {
          width: 100%;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .form-actions {
          display: flex;
          gap: 10px;
        }

        .rules-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 20px;
        }

        .rule-card {
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 20px;
        }

        .rule-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 15px;
        }

        .rule-badges {
          display: flex;
          gap: 5px;
        }

        .badge {
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .badge.hard {
          background: #ff6b6b;
          color: white;
        }

        .badge.soft {
          background: #4ecdc4;
          color: white;
        }

        .rule-details {
          margin-bottom: 15px;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        .rule-actions {
          display: flex;
          gap: 10px;
        }

        .btn-primary {
          background: #007bff;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn-secondary {
          background: #6c757d;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn-edit {
          background: #28a745;
          color: white;
          border: none;
          padding: 6px 12px;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn-delete {
          background: #dc3545;
          color: white;
          border: none;
          padding: 6px 12px;
          border-radius: 4px;
          cursor: pointer;
        }

        .loading {
          text-align: center;
          padding: 20px;
        }
      `}</style>
    </div>
  );
};

export default ComplianceRules;