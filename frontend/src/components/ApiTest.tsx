import React, { useState } from 'react';
import { complianceAPI } from '../services/api';

const ApiTest: React.FC = () => {
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testApiConnection = async () => {
    setLoading(true);
    setResult('테스트 중...');

    try {
      console.log('API 호출 시작...');
      const response = await complianceAPI.getRules(1);
      console.log('API 응답:', response);
      setResult(`성공: ${JSON.stringify(response.data, null, 2)}`);
    } catch (error: any) {
      console.error('API 오류:', error);
      setResult(`오류: ${error.message || error}`);

      if (error.response) {
        setResult(`오류: ${error.response.status} - ${error.response.data}`);
      } else if (error.request) {
        setResult('네트워크 오류: 서버에 연결할 수 없습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  const testBasicApi = async () => {
    setLoading(true);
    setResult('기본 API 테스트 중...');

    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setResult(`기본 API 성공: ${JSON.stringify(data, null, 2)}`);
    } catch (error) {
      setResult(`기본 API 오류: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#f5f5f5', margin: '20px', borderRadius: '8px' }}>
      <h3>🔧 API 연결 테스트</h3>

      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={testBasicApi}
          disabled={loading}
          style={{
            padding: '10px 20px',
            marginRight: '10px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? '테스트 중...' : '기본 API 테스트'}
        </button>

        <button
          onClick={testApiConnection}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? '테스트 중...' : '규칙 API 테스트'}
        </button>
      </div>

      <div style={{
        backgroundColor: '#fff',
        padding: '15px',
        borderRadius: '4px',
        border: '1px solid #ddd',
        whiteSpace: 'pre-wrap',
        fontFamily: 'monospace',
        minHeight: '100px'
      }}>
        {result || '테스트 버튼을 클릭하세요.'}
      </div>

      <div style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
        <p>💡 팁: 브라우저 개발자 도구(F12) → Network 탭을 열고 테스트해보세요.</p>
      </div>
    </div>
  );
};

export default ApiTest;