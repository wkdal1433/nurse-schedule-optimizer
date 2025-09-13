"""
WebSocket 실시간 알림 엔드포인트
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import json
import logging
from typing import Optional

from app.database import get_db
from app.models.models import User, Employee
from app.services.websocket_service import manager, websocket_notification_service

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_user_info(db: Session, user_id: int):
    """사용자 정보 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    return {
        "user_id": user_id,
        "ward_id": employee.ward_id if employee else None,
        "role": employee.role if employee else None
    }

@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db)
):
    """사용자별 실시간 알림 WebSocket 엔드포인트"""
    try:
        # 사용자 정보 조회
        user_info = await get_user_info(db, user_id)
        if not user_info:
            await websocket.close(code=4004, reason="User not found")
            return
        
        # WebSocket 연결 수락 및 등록
        await manager.connect(
            websocket, 
            user_id, 
            ward_id=user_info.get("ward_id"),
            role=user_info.get("role")
        )
        
        logger.info(f"WebSocket 연결 설정: 사용자 {user_id}")
        
        try:
            while True:
                # 클라이언트로부터 메시지 수신 대기
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, user_id, message, db)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": None
                    }))
                except Exception as e:
                    logger.error(f"메시지 처리 중 오류: {str(e)}")
                    await websocket.send_text(json.dumps({
                        "type": "error", 
                        "message": "Message processing error",
                        "timestamp": None
                    }))
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket 연결 해제: 사용자 {user_id}")
        except Exception as e:
            logger.error(f"WebSocket 오류: {str(e)}")
        finally:
            manager.disconnect(websocket, user_id)
            
    except Exception as e:
        logger.error(f"WebSocket 엔드포인트 오류: {str(e)}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass

async def handle_client_message(websocket: WebSocket, user_id: int, message: dict, db: Session):
    """클라이언트 메시지 처리"""
    message_type = message.get("type")
    
    if message_type == "ping":
        # 연결 상태 확인
        await manager.send_personal_message({
            "type": "pong",
            "message": "Connection alive",
            "timestamp": None
        }, websocket)
        
    elif message_type == "mark_notification_read":
        # 알림 읽음 처리 (실제 구현에서는 NotificationService 사용)
        notification_id = message.get("notification_id")
        if notification_id:
            try:
                # TODO: NotificationService를 통한 읽음 처리
                await manager.send_personal_message({
                    "type": "notification_read_success",
                    "notification_id": notification_id,
                    "timestamp": None
                }, websocket)
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Failed to mark notification as read: {str(e)}",
                    "timestamp": None
                }, websocket)
    
    elif message_type == "get_connection_stats":
        # 연결 통계 요청 (관리자만)
        user_info = await get_user_info(db, user_id)
        if user_info and user_info.get("role") in ["admin", "head_nurse"]:
            stats = websocket_notification_service.get_connection_stats()
            await manager.send_personal_message({
                "type": "connection_stats",
                "data": stats,
                "timestamp": None
            }, websocket)
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": "Insufficient permissions for connection stats",
                "timestamp": None
            }, websocket)
    
    elif message_type == "subscribe_ward":
        # 병동별 알림 구독 (추가 구현 가능)
        ward_id = message.get("ward_id")
        await manager.send_personal_message({
            "type": "subscription_success",
            "message": f"Subscribed to ward {ward_id}",
            "timestamp": None
        }, websocket)
    
    else:
        # 알 수 없는 메시지 타입
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": None
        }, websocket)

@router.get("/ws/stats")
async def get_websocket_stats():
    """WebSocket 연결 통계 조회 (HTTP 엔드포인트)"""
    return websocket_notification_service.get_connection_stats()

@router.post("/ws/test-notification/{user_id}")
async def send_test_notification(
    user_id: int,
    message: str = "테스트 알림입니다"
):
    """테스트 알림 전송 (개발용)"""
    try:
        await websocket_notification_service.send_notification(
            user_id=user_id,
            notification_data={
                "id": 999,
                "title": "테스트 알림",
                "message": message,
                "type": "test",
                "priority": "medium"
            }
        )
        return {"message": f"테스트 알림이 사용자 {user_id}에게 전송되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 전송 실패: {str(e)}")

@router.post("/ws/test-emergency/{ward_id}")
async def send_test_emergency(
    ward_id: int,
    message: str = "테스트 응급상황입니다"
):
    """테스트 응급 상황 알림 (개발용)"""
    try:
        await websocket_notification_service.send_emergency_alert(
            ward_id=ward_id,
            alert_data={
                "id": 999,
                "title": "테스트 응급상황",
                "description": message,
                "severity": "medium"
            },
            severity="medium"
        )
        return {"message": f"테스트 응급 알림이 병동 {ward_id}에 전송되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"응급 알림 전송 실패: {str(e)}")

@router.post("/ws/broadcast")
async def broadcast_message(
    message: str,
    message_type: str = "system_announcement"
):
    """시스템 전체 브로드캐스트 (관리자용)"""
    try:
        await websocket_notification_service.send_system_maintenance({
            "title": "시스템 공지",
            "message": message,
            "type": message_type
        })
        return {"message": "전체 브로드캐스트가 전송되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"브로드캐스트 실패: {str(e)}")