import React, { useState, useEffect } from "react";
import axios from "axios";

const API_BASE = "http://localhost:8000/api";

interface Ward {
  id: number;
  name: string;
  description: string;
}

interface Employee {
  id: number;
  employee_number: string;
  skill_level: number;
}

interface Schedule {
  id: number;
  ward_id: number;
  month: number;
  year: number;
  total_score: number;
  status: string;
}

function App() {
  const [wards, setWards] = useState<Ward[]>([]);
  const [selectedWard, setSelectedWard] = useState<number | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    loadWards();
    loadSchedules();
  }, []);

  useEffect(() => {
    if (selectedWard) {
      loadEmployees(selectedWard);
    }
  }, [selectedWard]);

  const loadWards = async () => {
    try {
      const response = await axios.get(`${API_BASE}/wards/`);
      setWards(response.data);
    } catch (error) {
      console.error("병동 목록 로드 실패:", error);
    }
  };

  const loadEmployees = async (wardId: number) => {
    try {
      const response = await axios.get(`${API_BASE}/employees/?ward_id=${wardId}`);
      setEmployees(response.data);
    } catch (error) {
      console.error("직원 목록 로드 실패:", error);
    }
  };

  const loadSchedules = async () => {
    try {
      const response = await axios.get(`${API_BASE}/schedules/`);
      setSchedules(response.data);
    } catch (error) {
      console.error("근무표 목록 로드 실패:", error);
    }
  };

  const generateSchedule = async () => {
    if (!selectedWard) {
      alert("병동을 먼저 선택해주세요.");
      return;
    }
    if (employees.length < 3) {
      alert("최소 3명 이상의 직원이 필요합니다.");
      return;
    }

    setIsGenerating(true);
    try {
      const response = await axios.post(`${API_BASE}/schedules/generate`, {
        ward_id: selectedWard,
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
        constraints: {}
      });

      alert(`근무표 생성 완료!\n점수: ${response.data.total_score.toFixed(1)}`);
      loadSchedules();
    } catch (error: any) {
      alert(`근무표 생성 실패: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const createSampleEmployees = async () => {
    if (!selectedWard) {
      alert("병동을 먼저 선택해주세요.");
      return;
    }
    try {
      const response = await axios.post(`${API_BASE}/employees/bulk-create?ward_id=${selectedWard}&count=6`);
      alert(`샘플 직원 ${response.data.employee_numbers.length}명 생성 완료!`);
      loadEmployees(selectedWard);
    } catch (error: any) {
      alert(`샘플 직원 생성 실패: ${error.response?.data?.detail || error.message}`);
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <header style={{ textAlign: "center", marginBottom: "30px", color: "#007bff" }}>
        <h1>🏥 간호사 근무표 최적화 시스템</h1>
        <p>Hybrid Metaheuristic 알고리즘 기반 자동 근무표 생성</p>
      </header>

      <main style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <section style={{ marginBottom: "30px" }}>
          <h2>📋 병동 관리</h2>
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            {wards.map(ward => (
              <button
                key={ward.id}
                onClick={() => setSelectedWard(ward.id)}
                style={{
                  padding: "10px 20px",
                  backgroundColor: selectedWard === ward.id ? "#007bff" : "#f8f9fa",
                  color: selectedWard === ward.id ? "white" : "black",
                  border: "1px solid #ddd",
                  borderRadius: "5px",
                  cursor: "pointer"
                }}
              >
                {ward.name}
              </button>
            ))}
          </div>
          
          {selectedWard && (
            <div style={{ marginTop: "10px", padding: "10px", backgroundColor: "#e9ecef", borderRadius: "5px" }}>
              <strong>선택된 병동:</strong> {wards.find(w => w.id === selectedWard)?.name}
            </div>
          )}
        </section>

        {selectedWard && (
          <section style={{ marginBottom: "30px" }}>
            <h2>👥 직원 관리 ({employees.length}명)</h2>
            <button 
              onClick={createSampleEmployees}
              style={{
                padding: "10px 20px",
                backgroundColor: "#28a745",
                color: "white",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
                marginBottom: "15px"
              }}
            >
              샘플 직원 6명 생성
            </button>
            
            {employees.length > 0 && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "10px" }}>
                {employees.map(emp => (
                  <div key={emp.id} style={{ 
                    padding: "10px", 
                    border: "1px solid #ddd", 
                    borderRadius: "5px",
                    backgroundColor: "#f8f9fa"
                  }}>
                    <strong>{emp.employee_number}</strong>
                    <br />스킬: {emp.skill_level}/5 ⭐
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        <section style={{ marginBottom: "30px" }}>
          <h2>🤖 근무표 자동 생성</h2>
          <button 
            onClick={generateSchedule}
            disabled={!selectedWard || employees.length < 3 || isGenerating}
            style={{
              padding: "15px 30px",
              backgroundColor: isGenerating ? "#6c757d" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: isGenerating ? "not-allowed" : "pointer",
              fontSize: "16px",
              fontWeight: "bold"
            }}
          >
            {isGenerating ? "생성 중..." : "근무표 생성"}
          </button>
          
          {!selectedWard && (
            <p style={{ color: "#dc3545", marginTop: "10px" }}>⚠️ 병동을 먼저 선택해주세요.</p>
          )}
          {selectedWard && employees.length < 3 && (
            <p style={{ color: "#dc3545", marginTop: "10px" }}>⚠️ 최소 3명 이상의 직원이 필요합니다.</p>
          )}
        </section>

        <section>
          <h2>📅 생성된 근무표 목록</h2>
          {schedules.length === 0 ? (
            <p>생성된 근무표가 없습니다.</p>
          ) : (
            <div style={{ display: "grid", gap: "10px" }}>
              {schedules.map(schedule => (
                <div key={schedule.id} style={{
                  padding: "15px",
                  border: "1px solid #ddd",
                  borderRadius: "5px",
                  backgroundColor: "#ffffff",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center"
                }}>
                  <div>
                    <strong>{wards.find(w => w.id === schedule.ward_id)?.name} - {schedule.year}년 {schedule.month}월</strong>
                    <br />점수: {schedule.total_score.toFixed(1)} | 상태: {schedule.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;