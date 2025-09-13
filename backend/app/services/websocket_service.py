"""
WebSocket 실시간 알림 서비스
"""
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 연결 관리"""
    
    def __init__(self):
        # 사용자별 활성 연결들
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # 병동별 연결들 (브로드캐스트용)
        self.ward_connections: Dict[int, List[WebSocket]] = {}
        # 역할별 연결들
        self.role_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int, ward_id: Optional[int] = None, role: Optional[str] = None):
        """WebSocket 연결 수락 및 등록"""
        await websocket.accept()
        
        # 사용자별 연결 등록
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # 병동별 연결 등록
        if ward_id:
            if ward_id not in self.ward_connections:
                self.ward_connections[ward_id] = []
            self.ward_connections[ward_id].append(websocket)
        
        # 역할별 연결 등록
        if role:
            if role not in self.role_connections:
                self.role_connections[role] = []
            self.role_connections[role].append(websocket)
        
        logger.info(f"WebSocket 연결: 사용자 {user_id}, 병동 {ward_id}, 역할 {role}")
        
        # 연결 확인 메시지 전송
        await self.send_personal_message({
            "type": "connection_established",
            "message": "실시간 알림 연결이 설정되었습니다",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """WebSocket 연결 해제"""
        # 사용자별 연결에서 제거
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # 병동별 연결에서 제거
        for ward_id, connections in self.ward_connections.items():
            if websocket in connections:
                connections.remove(websocket)
        
        # 역할별 연결에서 제거
        for role, connections in self.role_connections.items():
            if websocket in connections:
                connections.remove(websocket)
        
        logger.info(f"WebSocket 연결 해제: 사용자 {user_id}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """개별 WebSocket으로 메시지 전송"""
        try:
            await websocket.send_text(json.dumps(message, default=str, ensure_ascii=False))
        except Exception as e:
            logger.error(f"개별 메시지 전송 실패: {str(e)}")
    
    async def send_to_user(self, message: Dict, user_id: int):
        """특정 사용자의 모든 연결로 메시지 전송"""
        if user_id in self.active_connections:
            disconnected_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await self.send_personal_message(message, connection)
                except Exception as e:
                    logger.error(f"사용자 {user_id} 메시지 전송 실패: {str(e)}")
                    disconnected_connections.append(connection)
            
            # 연결이 끊어진 WebSocket 정리
            for connection in disconnected_connections:
                self.active_connections[user_id].remove(connection)
    
    async def broadcast_to_ward(self, message: Dict, ward_id: int):
        """병동의 모든 연결로 메시지 브로드캐스트"""
        if ward_id in self.ward_connections:
            disconnected_connections = []
            for connection in self.ward_connections[ward_id]:
                try:
                    await self.send_personal_message(message, connection)
                except Exception as e:
                    logger.error(f"병동 {ward_id} 브로드캐스트 실패: {str(e)}")
                    disconnected_connections.append(connection)
            
            # 연결이 끊어진 WebSocket 정리
            for connection in disconnected_connections:
                self.ward_connections[ward_id].remove(connection)
    
    async def broadcast_to_role(self, message: Dict, role: str):
        """특정 역할의 모든 연결로 메시지 브로드캐스트"""
        if role in self.role_connections:
            disconnected_connections = []
            for connection in self.role_connections[role]:
                try:
                    await self.send_personal_message(message, connection)
                except Exception as e:
                    logger.error(f"역할 {role} 브로드캐스트 실패: {str(e)}")
                    disconnected_connections.append(connection)
            
            # 연결이 끊어진 WebSocket 정리
            for connection in disconnected_connections:
                self.role_connections[role].remove(connection)
    
    async def broadcast_to_all(self, message: Dict):
        """모든 활성 연결로 메시지 브로드캐스트"""
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)
        
        disconnected_connections = []
        for connection in all_connections:
            try:
                await self.send_personal_message(message, connection)
            except Exception as e:
                logger.error(f"전체 브로드캐스트 실패: {str(e)}")
                disconnected_connections.append(connection)
        
        # 연결이 끊어진 WebSocket들 정리
        for connection in disconnected_connections:
            for user_id, connections in self.active_connections.items():
                if connection in connections:
                    connections.remove(connection)
    
    def get_active_users(self) -> List[int]:
        """현재 활성 사용자 목록 반환"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> Dict[str, int]:
        """연결 통계 반환"""
        return {
            "total_users": len(self.active_connections),
            "total_connections": sum(len(connections) for connections in self.active_connections.values()),
            "ward_connections": {ward_id: len(connections) for ward_id, connections in self.ward_connections.items()},
            "role_connections": {role: len(connections) for role, connections in self.role_connections.items()}
        }

# 전역 연결 관리자 인스턴스
manager = ConnectionManager()

class WebSocketNotificationService:
    """WebSocket 기반 실시간 알림 서비스"""
    
    def __init__(self):
        self.manager = manager
    
    async def send_notification(self, user_id: int, notification_data: Dict):
        """사용자에게 실시간 알림 전송"""
        message = {
            "type": "notification",
            "data": notification_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.send_to_user(message, user_id)
        logger.info(f"실시간 알림 전송: 사용자 {user_id}")
    
    async def send_approval_request(self, approver_ids: List[int], approval_data: Dict):
        """승인자들에게 승인 요청 알림"""
        message = {
            "type": "approval_request",
            "data": approval_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for approver_id in approver_ids:
            await self.manager.send_to_user(message, approver_id)
        
        logger.info(f"승인 요청 알림 전송: {len(approver_ids)}명의 승인자")
    
    async def send_emergency_alert(self, ward_id: int, alert_data: Dict, severity: str = "high"):
        """응급 상황 알림 브로드캐스트"""
        message = {
            "type": "emergency_alert",
            "severity": severity,
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 심각도에 따른 알림 범위 결정
        if severity in ["high", "critical"]:
            # 관리자와 수간호사에게 전체 알림
            await self.manager.broadcast_to_role(message, "admin")
            await self.manager.broadcast_to_role(message, "head_nurse")
        
        # 해당 병동에 알림
        await self.manager.broadcast_to_ward(message, ward_id)
        
        logger.info(f"응급 알림 브로드캐스트: 병동 {ward_id}, 심각도 {severity}")
    
    async def send_schedule_update(self, ward_id: int, schedule_data: Dict):
        """스케줄 업데이트 알림"""
        message = {
            "type": "schedule_update",
            "data": schedule_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.broadcast_to_ward(message, ward_id)
        logger.info(f"스케줄 업데이트 알림: 병동 {ward_id}")
    
    async def send_shift_change_notification(self, affected_user_ids: List[int], change_data: Dict):
        """근무 변경 알림"""
        message = {
            "type": "shift_change",
            "data": change_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for user_id in affected_user_ids:
            await self.manager.send_to_user(message, user_id)
        
        logger.info(f"근무 변경 알림: {len(affected_user_ids)}명의 사용자")
    
    async def send_system_maintenance(self, maintenance_data: Dict):
        """시스템 유지보수 알림 전체 브로드캐스트"""
        message = {
            "type": "system_maintenance",
            "data": maintenance_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.broadcast_to_all(message)
        logger.info("시스템 유지보수 알림 전체 브로드캐스트")
    
    def get_connection_stats(self) -> Dict:
        """연결 통계 조회"""
        return self.manager.get_connection_count()

# 전역 WebSocket 알림 서비스 인스턴스
websocket_notification_service = WebSocketNotificationService()