# GitHub 레포지토리 설정 가이드

## 1단계: GitHub에서 새 레포지토리 생성

1. https://github.com 접속
2. 우상단 '+' 버튼 클릭 → 'New repository' 선택
3. **Repository name**: `nurse-schedule-optimizer`
4. **Description**: `🏥 AI-powered nurse scheduling system with Hybrid Metaheuristic algorithm`
5. **Public** 또는 **Private** 선택
6. **Don't initialize** with README, .gitignore, license (이미 우리가 생성했으므로)
7. **'Create repository'** 클릭

## 2단계: 로컬 레포지토리와 연결

GitHub에서 레포지토리 생성 후, 아래 명령어들을 **순서대로** 실행하세요:

### YOUR_GITHUB_USERNAME을 실제 GitHub 사용자명으로 바꿔주세요!

```bash
# 1. 프로젝트 디렉토리로 이동
cd /c/Users/wkdal/nurse-schedule-optimizer

# 2. GitHub 레포지토리 연결 (YOUR_GITHUB_USERNAME을 실제 사용자명으로!)
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/nurse-schedule-optimizer.git

# 3. 메인 브랜치 설정
git branch -M main

# 4. 푸시 실행
git push -u origin main
```

## 프로젝트 구조 요약

```
nurse-schedule-optimizer/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── algorithms/      # 스케줄링 알고리즘
│   │   ├── api/            # REST API 엔드포인트
│   │   ├── models/         # 데이터베이스 모델
│   │   └── database/       # DB 연결
│   ├── main.py             # FastAPI 앱 진입점
│   └── requirements.txt    # Python 의존성
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── SimpleApp.tsx   # 메인 React 컴포넌트
│   │   └── index.tsx
│   └── package.json        # Node.js 의존성
├── docs/                   # 프로젝트 문서
└── README.md              # 프로젝트 설명
```

## 🎯 주요 기능

- **Hybrid Metaheuristic 알고리즘**: Simulated Annealing + Local Search
- **실시간 근무표 생성**: 31일간 자동 최적화 스케줄링
- **제약조건 처리**: 최소 인원, 연속 근무 제한, 개인 선호도
- **웹 인터페이스**: React 기반 직관적인 UI
- **완전한 시스템**: 데이터베이스 + API + 웹앱

## 🚀 실행 방법

### 백엔드 실행
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 실행
```bash
cd frontend
npm start
```

- **백엔드**: http://localhost:8000 (API 문서: /docs)
- **프론트엔드**: http://localhost:3000

## 📊 현재 상태: 완전히 작동하는 시스템 ✅

모든 기능이 구현되고 테스트되었습니다!