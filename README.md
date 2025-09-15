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

**최근 업데이트**: 2025-09-16 - SOLID 원칙 기반 대규모 코드 리팩토링 완료

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

- [x] **알림 & 공유 기능** ✅ 핵심 구현 완료
  - [x] 실시간 WebSocket 푸시 알림 시스템
  - [x] 응급 상황 브로드캐스트 알림
  - [x] 승인 워크플로우 알림
  - [x] 근무 변경 실시간 통지
  - [ ] PDF/이미지 내보내기
  - [ ] 카카오톡/이메일 공유
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

- [x] **SOLID 원칙 기반 대규모 리팩토링** ✅ 2025-09-16 완료
  - [x] **Backend 리팩토링**:
    - [x] `scheduler.py` (1197줄 → 5개 파일) - 스케줄링 로직 분리
    - [x] `manual_editing_service.py` (1158줄 → 6개 파일) - 수동 편집 기능 분리
  - [x] **Frontend 리팩토링**:
    - [x] `NurseScheduleApp.tsx` (1258줄 → 9개 파일) - 메인 애플리케이션 분리
    - [x] `RoleManagement.tsx` (1256줄 → 13개 파일) - 역할 관리 시스템 분리
  - [x] **아키텍처 개선**:
    - [x] Single Responsibility: 각 컴포넌트/모듈의 단일 책임 보장
    - [x] Open/Closed: 새 기능 추가 시 기존 코드 수정 없이 확장 가능
    - [x] Interface Segregation: 필요한 인터페이스만 의존하도록 분리
    - [x] Dependency Inversion: 추상화에 의존하는 구조로 변경
  - [x] **유지보수성 향상**:
    - [x] 기능별 독립적 테스트 가능
    - [x] 코드 가독성 및 이해도 증대
    - [x] 새 개발자 온보딩 용이성 확보

- [x] **알림 & 워크플로우 시스템** ✅ 완전 구현
  - [x] 포괄적 알림 모델 (Notification, ApprovalWorkflow, EmergencyAlert)
  - [x] 실시간 WebSocket 통신 서비스
  - [x] 승인 워크플로우 관리 (요청/승인/거부 프로세스)
  - [x] 응급 상황 알림 브로드캐스트 시스템
  - [x] 알림 큐 및 다중 채널 발송 (WebSocket, Email, SMS)
  - [x] 권한 기반 알림 라우팅
  - [x] Manual editing과 통합된 실시간 알림

- [ ] **내보내기 & 공유**
  - [ ] PDF 생성 엔진
  - [ ] 이미지 렌더링
  - [ ] 개인별 스케줄 뷰 생성

## 🏗️ SOLID 원칙 기반 아키텍처 리팩토링

### 📋 리팩토링 개요
대규모 코드베이스의 유지보수성과 확장성 향상을 위해 SOLID 원칙을 적용한 전면적인 리팩토링을 수행했습니다.

### 🔧 주요 리팩토링 결과

#### Backend 구조 개선
```
# Before: 거대한 단일 파일들
├── scheduler.py (1,197줄)
├── manual_editing_service.py (1,158줄)

# After: 기능별 분리된 모듈들
├── algorithms/scheduling/
│   ├── entities.py              # 도메인 엔티티
│   ├── constraint_processor.py  # 제약조건 처리
│   ├── fitness_calculator.py    # 적합도 계산
│   ├── main_scheduler.py        # 메인 오케스트레이터
│   └── optimizers/
│       └── simulated_annealing.py
└── services/manual_editing/
    ├── entities.py              # 편집 도메인 엔티티
    ├── validation_engine.py     # 검증 로직
    ├── change_applier.py        # 변경 적용
    ├── audit_logger.py          # 감사 로깅
    ├── notification_manager.py  # 알림 관리
    └── manual_editing_service.py # 통합 서비스
```

#### Frontend 구조 개선
```
# Before: 거대한 단일 컴포넌트들
├── NurseScheduleApp.tsx (1,258줄)
├── RoleManagement.tsx (1,256줄)

# After: 기능별 분리된 컴포넌트들
├── nurse-schedule/
│   ├── NurseScheduleAppNew.tsx  # 메인 오케스트레이터 (179줄)
│   ├── types.ts                 # 타입 정의
│   ├── hooks/
│   │   └── useNurseSchedule.ts  # 비즈니스 로직
│   ├── views/                   # UI 컴포넌트들
│   │   ├── SetupView.tsx
│   │   ├── CalendarView.tsx
│   │   └── SettingsView.tsx
│   └── index.ts
└── role-management/
    ├── RoleManagementNew.tsx    # 메인 오케스트레이터 (356줄)
    ├── types/index.ts           # 타입 정의
    ├── hooks/                   # 도메인별 훅들
    │   ├── useEmployees.ts
    │   ├── useConstraints.ts
    │   ├── useSupervision.ts
    │   └── useEmployment.ts
    ├── components/              # 도메인별 UI
    │   ├── EmployeeManagement.tsx
    │   ├── ConstraintManagement.tsx
    │   ├── SupervisionManagement.tsx
    │   └── EmploymentManagement.tsx
    └── index.ts
```

### 🎯 SOLID 원칙 적용 상세

#### Single Responsibility Principle (SRP)
- **Before**: 한 파일에서 여러 책임 (UI, 비즈니스 로직, 상태 관리)
- **After**: 각 모듈/컴포넌트가 단일 책임만 담당
  - `entities.py`: 도메인 모델 정의만
  - `validation_engine.py`: 검증 로직만
  - `useNurseSchedule.ts`: 스케줄링 비즈니스 로직만

#### Open/Closed Principle (OCP)
- **Before**: 새 기능 추가 시 기존 코드 수정 필요
- **After**: 인터페이스 기반 확장 가능한 구조
  - 새로운 최적화 알고리즘을 추가할 때 기존 코드 수정 없음
  - 새로운 UI 뷰를 추가할 때 기존 컴포넌트 영향 없음

#### Liskov Substitution Principle (LSP)
- **Before**: 타입 안정성 부족
- **After**: TypeScript 인터페이스로 대체 가능성 보장
  - 모든 hook이 동일한 패턴으로 대체 가능
  - 컴포넌트 Props 인터페이스 일관성

#### Interface Segregation Principle (ISP)
- **Before**: 거대한 Props와 의존성
- **After**: 필요한 인터페이스만 의존
  - 각 컴포넌트가 필요한 Props만 받음
  - 도메인별 분리된 Hook 인터페이스

#### Dependency Inversion Principle (DIP)
- **Before**: 구체적인 구현에 의존
- **After**: 추상화에 의존하는 구조
  - Repository 패턴으로 데이터 계층 추상화
  - Hook을 통한 비즈니스 로직 추상화

### 📈 리팩토링 효과

#### 개발 생산성 향상
- **코드 가독성**: 평균 파일 크기 70% 감소 (1000+줄 → 300줄 이하)
- **개발 효율**: 기능별 독립적 개발 가능
- **테스트 용이성**: 각 모듈의 독립적 테스트 가능

#### 유지보수성 개선
- **버그 격리**: 문제 발생 시 영향 범위 최소화
- **코드 탐색**: 기능별 명확한 파일 구조
- **신규 개발자 온보딩**: 직관적인 코드 구조

#### 확장성 확보
- **새 기능 추가**: 기존 코드 수정 없이 확장
- **성능 최적화**: 모듈별 최적화 가능
- **재사용성**: 컴포넌트와 Hook의 다른 프로젝트 재사용

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