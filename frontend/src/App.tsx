import React, { useState } from 'react';
import ComplianceRules from './components/ComplianceRules';
import PreferenceManagement from './components/PreferenceManagement';
import RoleManagement from './components/RoleManagement';
import PatternValidation from './components/PatternValidation';
import ApiTest from './components/ApiTest';
import './App.css';

function App() {
  const [currentTab, setCurrentTab] = useState('compliance');
  const [selectedWardId] = useState<number>(1); // 임시로 병동 ID 1 사용

  return (
    <div className="App">
      <header className="app-header">
        <h1>🏥 간호사 근무표 최적화 시스템</h1>
        <nav className="app-nav">
          <button 
            className={currentTab === 'compliance' ? 'active' : ''}
            onClick={() => setCurrentTab('compliance')}
          >
            근무 규칙 관리
          </button>
          <button 
            className={currentTab === 'preferences' ? 'active' : ''}
            onClick={() => setCurrentTab('preferences')}
          >
            선호도 관리
          </button>
          <button 
            className={currentTab === 'roles' ? 'active' : ''}
            onClick={() => setCurrentTab('roles')}
          >
            역할 관리
          </button>
          <button 
            className={currentTab === 'patterns' ? 'active' : ''}
            onClick={() => setCurrentTab('patterns')}
          >
            패턴 검증
          </button>
          <button 
            className={currentTab === 'schedule' ? 'active' : ''}
            onClick={() => setCurrentTab('schedule')}
          >
            스케줄 관리
          </button>
          <button
            className={currentTab === 'reports' ? 'active' : ''}
            onClick={() => setCurrentTab('reports')}
          >
            리포트
          </button>
          <button
            className={currentTab === 'apitest' ? 'active' : ''}
            onClick={() => setCurrentTab('apitest')}
          >
            API 테스트
          </button>
        </nav>
      </header>

      <main className="app-main">
        {currentTab === 'compliance' && (
          <ComplianceRules wardId={selectedWardId} />
        )}
        {currentTab === 'preferences' && (
          <PreferenceManagement wardId={selectedWardId} />
        )}
        {currentTab === 'roles' && (
          <RoleManagement wardId={selectedWardId} />
        )}
        {currentTab === 'patterns' && (
          <PatternValidation wardId={selectedWardId} />
        )}
        {currentTab === 'schedule' && (
          <div className="coming-soon">
            <h2>📅 스케줄 관리</h2>
            <p>곧 출시될 기능입니다.</p>
          </div>
        )}
        {currentTab === 'reports' && (
          <div className="coming-soon">
            <h2>📊 리포트</h2>
            <p>곧 출시될 기능입니다.</p>
          </div>
        )}
        {currentTab === 'apitest' && (
          <ApiTest />
        )}
      </main>

      <style jsx global>{`
        body {
          margin: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
            'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
            sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
          background-color: #f5f5f5;
        }

        .App {
          min-height: 100vh;
        }

        .app-header {
          background: #2c3e50;
          color: white;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .app-header h1 {
          margin: 0 0 15px 0;
          font-size: 24px;
        }

        .app-nav {
          display: flex;
          gap: 10px;
        }

        .app-nav button {
          background: transparent;
          color: #bdc3c7;
          border: 1px solid #34495e;
          padding: 10px 20px;
          border-radius: 5px;
          cursor: pointer;
          transition: all 0.3s;
        }

        .app-nav button.active,
        .app-nav button:hover {
          background: #3498db;
          color: white;
          border-color: #3498db;
        }

        .app-main {
          min-height: calc(100vh - 120px);
          padding: 20px;
        }

        .coming-soon {
          text-align: center;
          padding: 60px 20px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .coming-soon h2 {
          color: #2c3e50;
          margin-bottom: 10px;
        }

        .coming-soon p {
          color: #7f8c8d;
        }
      `}</style>
    </div>
  );
}

export default App;
