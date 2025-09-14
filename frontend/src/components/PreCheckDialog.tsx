import React, { useState, useEffect } from 'react';

interface PreCheckError {
  message: string;
  category: string;
  severity: string;
}

interface PreCheckWarning {
  message: string;
  category: string;
  severity: string;
}

interface PreCheckResult {
  is_valid: boolean;
  can_generate: boolean;
  total_errors: number;
  total_warnings: number;
  errors: PreCheckError[];
  warnings: PreCheckWarning[];
  staff_analysis: any;
  recommendations: string[];
  timestamp: string;
}

interface PreCheckDialogProps {
  isOpen: boolean;
  onClose: () => void;
  wardId: number;
  year: number;
  month: number;
  onProceed?: (forceGenerate?: boolean) => void;
}

const PreCheckDialog: React.FC<PreCheckDialogProps> = ({
  isOpen,
  onClose,
  wardId,
  year,
  month,
  onProceed
}) => {
  const [preCheckResult, setPreCheckResult] = useState<PreCheckResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && wardId) {
      performPreCheck();
    }
  }, [isOpen, wardId, year, month]);

  const performPreCheck = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/schedules/precheck/${wardId}/${year}/${month}`);
      const data = await response.json();

      if (data.success) {
        setPreCheckResult(data.precheck_result);
      } else {
        setError('Pre-check 수행 중 오류가 발생했습니다.');
      }
    } catch (err) {
      console.error('Pre-check error:', err);
      setError('서버와의 통신 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProceed = (forceGenerate: boolean = false) => {
    if (onProceed) {
      onProceed(forceGenerate);
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto m-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900">
              근무표 생성 사전 검증 ({year}년 {month}월)
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl font-bold"
            >
              ×
            </button>
          </div>

          {isLoading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">검증 중...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              <p className="font-bold">오류 발생</p>
              <p>{error}</p>
            </div>
          )}

          {preCheckResult && (
            <div className="space-y-6">
              {/* 검증 결과 요약 */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className={`text-2xl font-bold ${preCheckResult.can_generate ? 'text-green-600' : 'text-red-600'}`}>
                      {preCheckResult.can_generate ? '✓' : '✗'}
                    </div>
                    <div className="text-sm text-gray-600">
                      {preCheckResult.can_generate ? '생성 가능' : '생성 차단'}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {preCheckResult.total_errors}
                    </div>
                    <div className="text-sm text-gray-600">오류</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {preCheckResult.total_warnings}
                    </div>
                    <div className="text-sm text-gray-600">경고</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {preCheckResult.recommendations.length}
                    </div>
                    <div className="text-sm text-gray-600">권고사항</div>
                  </div>
                </div>
              </div>

              {/* 오류 목록 */}
              {preCheckResult.errors.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-red-700 mb-3">
                    🚨 심각한 오류 ({preCheckResult.total_errors}건)
                  </h3>
                  <div className="space-y-2">
                    {preCheckResult.errors.map((error, index) => (
                      <div key={index} className="bg-red-50 border-l-4 border-red-400 p-3">
                        <div className="flex">
                          <div className="ml-3">
                            <p className="text-sm text-red-700 font-medium">
                              [{error.category}] {error.message}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 경고 목록 */}
              {preCheckResult.warnings.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-yellow-700 mb-3">
                    ⚠️ 주의사항 ({preCheckResult.total_warnings}건)
                  </h3>
                  <div className="space-y-2">
                    {preCheckResult.warnings.map((warning, index) => (
                      <div key={index} className="bg-yellow-50 border-l-4 border-yellow-400 p-3">
                        <div className="flex">
                          <div className="ml-3">
                            <p className="text-sm text-yellow-700 font-medium">
                              [{warning.category}] {warning.message}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 인력 분석 */}
              {preCheckResult.staff_analysis && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-3">
                    📊 인력 분석
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* 시프트별 요구사항 */}
                    {preCheckResult.staff_analysis.shift_requirements && (
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <h4 className="font-medium text-blue-800 mb-2">시프트별 인력 요구사항</h4>
                        <div className="space-y-1 text-sm">
                          <div>주간: {preCheckResult.staff_analysis.shift_requirements.day_shift?.required || 0}명 필요</div>
                          <div>저녁: {preCheckResult.staff_analysis.shift_requirements.evening_shift?.required || 0}명 필요</div>
                          <div>야간: {preCheckResult.staff_analysis.shift_requirements.night_shift?.required || 0}명 필요</div>
                          <div className="font-medium">
                            총 인력: {preCheckResult.staff_analysis.shift_requirements.total_available || 0}명
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 역할별 분포 */}
                    {preCheckResult.staff_analysis.role_distribution && (
                      <div className="bg-green-50 p-4 rounded-lg">
                        <h4 className="font-medium text-green-800 mb-2">역할별 인력 분포</h4>
                        <div className="space-y-1 text-sm">
                          {Object.entries(preCheckResult.staff_analysis.role_distribution.by_skill || {}).map(([skill, count]) => (
                            <div key={skill}>{skill}: {count as number}명</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 권고사항 */}
              {preCheckResult.recommendations.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-blue-700 mb-3">
                    💡 개선 권고사항
                  </h3>
                  <div className="space-y-2">
                    {preCheckResult.recommendations.map((recommendation, index) => (
                      <div key={index} className="bg-blue-50 border-l-4 border-blue-400 p-3">
                        <p className="text-sm text-blue-700">{recommendation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 액션 버튼 */}
              <div className="flex justify-between pt-4 border-t">
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                >
                  취소
                </button>

                <div className="space-x-2">
                  {preCheckResult.can_generate ? (
                    <button
                      onClick={() => handleProceed(false)}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      근무표 생성하기
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => handleProceed(true)}
                        className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                      >
                        강제 생성
                      </button>
                      <span className="text-sm text-gray-500">
                        (오류가 있지만 생성을 진행합니다)
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PreCheckDialog;