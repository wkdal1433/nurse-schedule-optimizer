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
- Backend: Python 3.8+, FastAPI, PostgreSQL
- Frontend: React Native, Expo
- Algorithm: Hybrid Metaheuristic (SA + Local Search)

## 시작하기
1. 백엔드 실행: `cd backend && python -m uvicorn main:app --reload`
2. 프론트엔드 실행: `cd frontend && npm start`

## 라이선스
MIT License