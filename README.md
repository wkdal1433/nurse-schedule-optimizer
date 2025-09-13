# 간호사 근무표 자동 생성 시스템

## 개요
Hybrid Metaheuristic 알고리즘을 활용한 병원 간호사 근무표 최적화 시스템

## 핵심 기능
- 🤖 **자동 근무표 생성**: Simulated Annealing + Local Search 기반 최적화
- 👥 **사용자 관리**: 병동 관리자/간호사 권한 구분
- ⚙️ **근무 규칙 설정**: 병동별 맞춤 규칙 및 제약조건
- 📱 **모바일 최적화**: React Native 기반 직관적 UI/UX
- ⚡ **실시간 최적화**: Incremental Rescheduling으로 즉시 반영

## 프로젝트 구조
```
nurse-schedule-optimizer/
├── backend/          # FastAPI 기반 백엔드
├── frontend/         # React Native 프론트엔드
├── docs/            # 프로젝트 문서
└── README.md        # 프로젝트 개요
```

## 개발 환경
- Backend: Python 3.8+, FastAPI, PostgreSQL, NumPy
- Frontend: React TypeScript, Material-UI, react-dnd
- Algorithm: Enhanced Hybrid Metaheuristic (SA + Tabu Search + Multi-neighborhood LS)

## 개발 진행 상황

**최근 업데이트**: 2024-12-09 - Enhanced 최적화 알고리즘 구현 완료

### 📋 기능 구현 체크리스트
- [x] **근무 규칙 & 법적 준수 시스템** ✅
  - [x] 최대 연속 야간근무 제한 (2-3일)
  - [x] 최대 연속 근무일 제한 (5일)
  - [x] 주간 휴식 보장 (주 1회 이상)
  - [x] 법정 근무시간 준수 (주 40시간)
  - [x] 관리자 규칙 설정 기능

- [x] **개인 선호도 & 요청 관리** ✅
  - [x] 휴가/연차 요청 시스템
  - [x] 근무 회피 선호도 설정
  - [x] 선호 근무 패턴 관리
  - [x] 사전 스케줄링 요청 폼

- [x] **역할 기반 & 고용형태 배치** ✅ 완료
  - [x] 수간호사/일반간호사/신입간호사 역할 구분
  - [x] 신입간호사-선임간호사 페어링
  - [x] 정규직/시간제 근무 제약

- [x] **근무 패턴 검증** ✅ 완료
  - [x] 비합리적 근무 순서 방지 (Day→Night 등)
  - [x] 피로도 감소 점수 시스템
  - [x] 연속 야간근무 패턴 제한

- [x] **수동 편집 & 응급 처리** ✅ 고도화 완료
  - [x] 드래그앤드롭 스케줄 편집 (ManualScheduleEditor 구현)
  - [x] 실시간 최적화 점수 재계산 (validation API 구현)
  - [x] 응급 근무 재배치 모드 (emergency_reassignment API 구현)
  - [x] **AI 기반 대체 근무자 추천 (정교화 완료)**
    - [x] 선호도 기반 평가 (과거 패턴 + 명시적 선호도)
    - [x] 피로도 및 워크로드 분석 (연속근무, 야간빈도, 총 근무시간)
    - [x] 팀 균형 및 협업 고려 (역할 균형, 경험 분포, 숙련도)
  - [x] **권한 기반 접근 제어 시스템**
    - [x] 5단계 권한 레벨 (신입간호사 → 관리자)
    - [x] 기능별 최소 권한 요구사항 정의
    - [x] 병동별 권한 분리 및 대상 직원 권한 검사
    - [x] 권한 확인 API 엔드포인트 (permissions/)

- [ ] **알림 & 공유 기능**
  - [ ] PDF/이미지 내보내기
  - [ ] 카카오톡/이메일 공유
  - [ ] 스케줄 업데이트 푸시 알림
  - [ ] 개인별 맞춤 스케줄 뷰

- [ ] **인력 안전 검증**
  - [ ] 병동별/근무별 최소 인력 기준
  - [ ] 자동 검증 및 경고 메시지
  - [ ] 중환자실 등 특수 병동 규칙

- [ ] **통계 & 리포팅**
  - [ ] 월별 근무 유형별 집계
  - [ ] 야간근무 공평성 분석
  - [ ] 연차 사용 현황 리포트
  - [ ] 관리용 내보내기 기능

### 🔧 기술적 구현 체크리스트
- [x] **Enhanced Hybrid Metaheuristic 최적화 알고리즘** ✅ 고도화 완료
  - [x] CSP 기반 스마트 초기화 시스템
  - [x] Enhanced Simulated Annealing with Adaptive Reheating
  - [x] Tabu Search for intensive local optimization
  - [x] Multi-neighborhood Variable Local Search
  - [x] 가중치 기반 제약조건 시스템 (Hard/Soft Constraints)
  - [x] 실시간 제약조건 위반 검증 및 보고서
  - [x] 7단계 적합도 함수 (법적준수/안전/역할/패턴/선호도/공평성/커버리지)

- [x] **UI/UX 구현** ✅ 기본 구현 완료
  - [x] 드래그앤드롭 스케줄 에디터 (react-dnd 기반)
  - [x] 반응형 캘린더 뷰 (Material-UI 기반)
  - [x] 모바일 최적화 인터페이스 (responsive design)

- [x] **백엔드 시스템 안정화** ✅ 완료
  - [x] 수동 편집 서비스 인스턴스화 문제 해결
  - [x] SQLAlchemy 메타데이터 Base 통합 (중복 제거)
  - [x] Schedule 클래스 중복 정의 제거 (models.py에서 제거 완료)
  - [x] 모든 파일의 Schedule import 경로 수정 (→ scheduling_models)
  - [x] SQLAlchemy relationship 참조 수정 (models.py)
  - [x] 백엔드 서버 시작 검증 완료 (Uvicorn 정상 구동)

- [ ] **내보내기 & 공유**
  - [ ] PDF 생성 엔진
  - [ ] 이미지 렌더링
  - [ ] 개인별 스케줄 뷰 생성

## 🧠 Enhanced 최적화 알고리즘 특징

### 4단계 Hybrid Metaheuristic 최적화
1. **CSP 기반 스마트 초기화**: 제약조건을 만족하는 초기 해 생성
2. **Enhanced Simulated Annealing**: Adaptive Reheating으로 지역 최적해 탈출
3. **Tabu Search**: 집중적 지역 탐색으로 해의 품질 향상
4. **Multi-neighborhood Variable Local Search**: 4가지 이웃해 전략 동시 적용

### 7단계 적합도 평가 시스템
- **Hard Constraints**: 법적 준수 (연속근무 제한, 주휴 보장)
- **Safety Constraints**: 인력 안전 (최소 인력 확보)
- **Role Compliance**: 역할 기반 (신입-선임 페어링, 고용형태 제약)
- **Pattern Quality**: 피로도 관리 (야근→주간 금지 등)
- **Preference Satisfaction**: 개인 선호도 반영
- **Fairness**: 야간근무 공평 분배
- **Coverage Quality**: 시프트별 적정 인력 배치

### 고급 제약조건 검증
- 실시간 위반사항 검출 및 보고서 생성
- 사양서 기준 가중치 시스템 적용
- 제약조건별 세분화된 페널티/보너스 점수

## 시작하기
1. 백엔드 실행: `cd backend && python -m uvicorn main:app --reload`
2. 프론트엔드 실행: `cd frontend && npm start`
3. 알고리즘 테스트: `cd backend && python test_enhanced_algorithm.py`

## 관련 문서
- [상세 기능 명세서 v3](./docs/functional-algorithm-spec-v3.md)

## 라이선스
MIT License