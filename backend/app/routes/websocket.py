from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()

# Store active connections by clinic_id
active_connections = {}


@router.websocket("/ws/{clinic_id}")
async def websocket_endpoint(websocket: WebSocket, clinic_id: int):
    await websocket.accept()
    
    if clinic_id not in active_connections:
        active_connections[clinic_id] = []
    active_connections[clinic_id].append(websocket)
    print(f"🟢 Client connected to clinic {clinic_id}. Total: {len(active_connections[clinic_id])}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "queue_update":
                await broadcast(clinic_id, message)
                
    except WebSocketDisconnect:
        if clinic_id in active_connections:
            active_connections[clinic_id].remove(websocket)
            print(f"🔴 Client disconnected from clinic {clinic_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")


async def broadcast(clinic_id: int, data: dict):
    if clinic_id in active_connections:
        msg = json.dumps({"type": "queue_update", "data": data})
        dead = []
        for ws in active_connections[clinic_id]:
            try:
                await ws.send_text(msg)
            except:
                dead.append(ws)
        for ws in dead:
            active_connections[clinic_id].remove(ws)