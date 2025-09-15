import React, { useState, useEffect } from 'react';

interface CategoryScore {
  category: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
  violations?: any[];
  compliance_items: any;
  details: {
    explanation: string;
    calculation: string;
    weight_applied: string;
  };
}

interface ImprovementSuggestion {
  category: string;
  current_score: number;
  priority: string;
  suggestions: string[];
  expected_improvement: string;
}

interface BreakdownResult {
  total_score: number;
  category_scores: {
    [key: string]: CategoryScore;
  };
  improvement_suggestions: ImprovementSuggestion[];
  statistics: {
    highest_score_category: string;
    lowest_score_category: string;
    average_score: number;
    score_distribution: {
      excellent: number;
      good: number;
      fair: number;
      poor: number;
    };
  };
  timestamp: string;
}

interface ScheduleInfo {
  ward_id: number;
  ward_name: string;
  year: number;
  month: number;
  status: string;
  created_at: string;
}

interface ScoreBreakdownDialogProps {
  isOpen: boolean;
  onClose: () => void;
  scheduleId: number;
}

const ScoreBreakdownDialog: React.FC<ScoreBreakdownDialogProps> = ({
  isOpen,
  onClose,
  scheduleId
}) => {
  const [breakdownResult, setBreakdownResult] = useState<BreakdownResult | null>(null);
  const [scheduleInfo, setScheduleInfo] = useState<ScheduleInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'details' | 'improvements'>('overview');

  useEffect(() => {
    if (isOpen && scheduleId) {
      fetchBreakdownData();
    }
  }, [isOpen, scheduleId]);

  const fetchBreakdownData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/schedules/breakdown/${scheduleId}`);
      const data = await response.json();

      if (data.success) {
        setBreakdownResult(data.breakdown_result);
        setScheduleInfo(data.schedule_info);
      } else {
        setError('점수 분석 데이터를 가져올 수 없습니다.');
      }
    } catch (err) {
      console.error('Breakdown fetch error:', err);
      setError('서버와의 통신 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const getCategoryIcon = (category: string): string => {
    const iconMap: { [key: string]: string } = {
      '법적 준수': '⚖️',
      '인력 안전': '🛡️',
      '역할 준수': '👥',
      '근무 패턴 품질': '🔄',
      '선호도 충족': '💝',
      '공평성': '⚖️',
      '커버리지 품질': '📊'
    };
    return iconMap[category] || '📋';
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-600 bg-green-100';
    if (score >= 70) return 'text-blue-600 bg-blue-100';
    if (score >= 50) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[85vh] overflow-y-auto m-4">
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">근무표 점수 상세 분석</h2>
              {scheduleInfo && (
                <p className="text-gray-600 mt-1">
                  {scheduleInfo.ward_name} • {scheduleInfo.year}년 {scheduleInfo.month}월
                  • 상태: {scheduleInfo.status}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl font-bold"
            >
              ×
            </button>
          </div>

          {/* 탭 네비게이션 */}
          <div className="flex border-b border-gray-200 mb-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-2 px-4 font-medium ${
                activeTab === 'overview'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              📊 종합 점수
            </button>
            <button
              onClick={() => setActiveTab('details')}
              className={`py-2 px-4 font-medium ${
                activeTab === 'details'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              📋 세부 분석
            </button>
            <button
              onClick={() => setActiveTab('improvements')}
              className={`py-2 px-4 font-medium ${
                activeTab === 'improvements'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              💡 개선 제안
            </button>
          </div>

          {isLoading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">분석 중...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              <p className="font-bold">오류 발생</p>
              <p>{error}</p>
            </div>
          )}

          {breakdownResult && (
            <>
              {/* 종합 점수 탭 */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* 총점 및 요약 */}
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-2xl font-bold text-gray-800">
                          총점: {breakdownResult.total_score.toFixed(0)}점
                        </h3>
                        <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                          <div>최고 카테고리: <span className="font-medium text-green-600">{breakdownResult.statistics.highest_score_category}</span></div>
                          <div>최저 카테고리: <span className="font-medium text-red-600">{breakdownResult.statistics.lowest_score_category}</span></div>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-4xl font-bold text-blue-600">
                          {breakdownResult.statistics.average_score.toFixed(1)}
                        </div>
                        <div className="text-sm text-gray-600">평균 점수</div>
                      </div>
                    </div>
                  </div>

                  {/* 점수 분포 */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-700 mb-3">점수 분포</h4>
                    <div className="grid grid-cols-4 gap-4 text-center">
                      <div className="bg-green-100 p-3 rounded">
                        <div className="text-xl font-bold text-green-600">{breakdownResult.statistics.score_distribution.excellent}</div>
                        <div className="text-sm text-green-700">우수 (90+)</div>
                      </div>
                      <div className="bg-blue-100 p-3 rounded">
                        <div className="text-xl font-bold text-blue-600">{breakdownResult.statistics.score_distribution.good}</div>
                        <div className="text-sm text-blue-700">양호 (70+)</div>
                      </div>
                      <div className="bg-yellow-100 p-3 rounded">
                        <div className="text-xl font-bold text-yellow-600">{breakdownResult.statistics.score_distribution.fair}</div>
                        <div className="text-sm text-yellow-700">보통 (50+)</div>
                      </div>
                      <div className="bg-red-100 p-3 rounded">
                        <div className="text-xl font-bold text-red-600">{breakdownResult.statistics.score_distribution.poor}</div>
                        <div className="text-sm text-red-700">미흡 (50-)</div>
                      </div>
                    </div>
                  </div>

                  {/* 카테고리별 점수 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(breakdownResult.category_scores).map(([key, category]) => (
                      <div key={key} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-xl">{getCategoryIcon(category.category)}</span>
                            <h4 className="font-medium text-gray-800">{category.category}</h4>
                          </div>
                          <div className={`px-2 py-1 rounded-full text-sm font-medium ${getScoreColor(category.raw_score)}`}>
                            {category.raw_score.toFixed(1)}점
                          </div>
                        </div>

                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">기본 점수:</span>
                            <span>{category.raw_score.toFixed(1)}점</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">가중치:</span>
                            <span>×{category.weight}</span>
                          </div>
                          <div className="flex justify-between font-medium">
                            <span className="text-gray-800">가중 점수:</span>
                            <span>{category.weighted_score.toFixed(0)}점</span>
                          </div>
                        </div>

                        {/* 진행바 */}
                        <div className="mt-3">
                          <div className="bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                category.raw_score >= 90 ? 'bg-green-500' :
                                category.raw_score >= 70 ? 'bg-blue-500' :
                                category.raw_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${Math.min(category.raw_score, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 세부 분석 탭 */}
              {activeTab === 'details' && (
                <div className="space-y-6">
                  {Object.entries(breakdownResult.category_scores).map(([key, category]) => (
                    <div key={key} className="border rounded-lg overflow-hidden">
                      <div className="bg-gray-50 p-4 border-b">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="text-xl">{getCategoryIcon(category.category)}</span>
                            <h3 className="text-lg font-semibold text-gray-800">{category.category}</h3>
                          </div>
                          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(category.raw_score)}`}>
                            {category.raw_score.toFixed(1)}점
                          </div>
                        </div>
                      </div>

                      <div className="p-4 space-y-4">
                        {/* 설명 */}
                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">설명</h4>
                          <p className="text-gray-600 text-sm">{category.details.explanation}</p>
                        </div>

                        {/* 계산 과정 */}
                        <div className="bg-blue-50 p-3 rounded">
                          <h4 className="font-medium text-blue-800 mb-2">점수 계산</h4>
                          <div className="text-sm space-y-1">
                            <div>{category.details.calculation}</div>
                            <div className="font-medium">{category.details.weight_applied}</div>
                          </div>
                        </div>

                        {/* 위반사항 */}
                        {category.violations && category.violations.length > 0 && (
                          <div>
                            <h4 className="font-medium text-red-700 mb-2">
                              위반 사항 ({category.violations.length}건)
                            </h4>
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                              {category.violations.slice(0, 5).map((violation, idx) => (
                                <div key={idx} className="bg-red-50 border-l-4 border-red-400 p-2 text-sm">
                                  {typeof violation === 'object' ? (
                                    <div>
                                      <div className="font-medium">{violation.employee_name || violation.rule}</div>
                                      <div className="text-red-600">
                                        {violation.violation || violation.description}
                                      </div>
                                    </div>
                                  ) : (
                                    <div>{violation}</div>
                                  )}
                                </div>
                              ))}
                              {category.violations.length > 5 && (
                                <div className="text-sm text-gray-500 pl-2">
                                  ... 외 {category.violations.length - 5}건 더
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* 준수 항목 */}
                        {category.compliance_items && Object.keys(category.compliance_items).length > 0 && (
                          <div>
                            <h4 className="font-medium text-green-700 mb-2">준수 현황</h4>
                            <div className="bg-green-50 p-3 rounded">
                              <div className="grid grid-cols-2 gap-2 text-sm">
                                {Object.entries(category.compliance_items).map(([itemKey, itemValue]) => (
                                  <div key={itemKey} className="flex justify-between">
                                    <span className="text-gray-600">
                                      {itemKey.replace(/_/g, ' ')}:
                                    </span>
                                    <span className="font-medium">
                                      {typeof itemValue === 'number'
                                        ? itemValue.toFixed(1)
                                        : String(itemValue)
                                      }
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 개선 제안 탭 */}
              {activeTab === 'improvements' && (
                <div className="space-y-4">
                  {breakdownResult.improvement_suggestions.length > 0 ? (
                    breakdownResult.improvement_suggestions.map((suggestion, idx) => (
                      <div key={idx} className="border rounded-lg overflow-hidden">
                        <div className="bg-yellow-50 p-4 border-b">
                          <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-gray-800">
                              💡 {suggestion.category}
                            </h3>
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(suggestion.priority)}`}>
                                {suggestion.priority === 'high' ? '높음' :
                                 suggestion.priority === 'medium' ? '보통' : '낮음'}
                              </span>
                              <span className="text-sm text-gray-600">
                                현재: {suggestion.current_score.toFixed(1)}점
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="p-4">
                          <h4 className="font-medium text-gray-700 mb-3">개선 방안</h4>
                          <ul className="space-y-2">
                            {suggestion.suggestions.map((item, itemIdx) => (
                              <li key={itemIdx} className="flex items-start space-x-2">
                                <span className="text-blue-500 mt-1">•</span>
                                <span className="text-gray-700 text-sm">{item}</span>
                              </li>
                            ))}
                          </ul>

                          <div className="mt-4 bg-green-50 p-3 rounded">
                            <h5 className="font-medium text-green-800 mb-1">예상 효과</h5>
                            <p className="text-green-700 text-sm">{suggestion.expected_improvement}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-6xl mb-4">🎉</div>
                      <h3 className="text-xl font-semibold text-gray-800 mb-2">
                        우수한 근무표입니다!
                      </h3>
                      <p className="text-gray-600">
                        모든 평가 항목에서 양호한 점수를 받아 별도의 개선사항이 없습니다.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* 닫기 버튼 */}
          <div className="flex justify-end pt-6 border-t mt-6">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScoreBreakdownDialog;