import json
from fastapi import FastAPI, WebSocket
import asyncio
import httpx
import requests

app = FastAPI()

# 클라이언트의 WebSocket 객체를 저장하는 딕셔너리
client_connections = {}

# 웹 소켓 연결을 처리하는 핸들러
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # 클라이언트의 WebSocket 객체를 저장
        client_connections[id(websocket)] = websocket

        # 클라이언트로부터 메시지를 수신하는 루프
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()

            # 클라이언트로부터 'send' 메시지를 수신했을 때마다 백그라운드 작업 시작
            if data == "send":
                await send_progress_until_done(websocket)
    except Exception as e:
        print(e)
    finally:
        # 연결이 종료되면 해당 WebSocket 객체를 딕셔너리에서 제거
        del client_connections[id(websocket)]

# 백그라운드 작업: 클라이언트에게 진행 상황을 보냄
async def send_progress_until_done(websocket: WebSocket):
    while True:
        progress_info = await get_progress_from_gpu_server()
        await websocket.send_text(progress_info)
#    if progress_info["progress"] == 100:
#        await websocket.close()


#async def get_progress_from_gpu_server():
 #   progress = 0
  #  elapsed_time = 0
   # while progress <= 100:
    #    # 경과 시간 증가, 남은 시간 감소
     #   elapsed_time += 2
      #  remain_time = 100 - progress
       # progress_info = {
        #    "progress": progress,
         #   "elapsed_time": elapsed_time,
          #  "remain_time": remain_time
#        }
#        progress += 10
#        yield json.dumps(progress_info)  # JSON 형식으로 직렬화하여 반환
#        await asyncio.sleep(2)

async def get_progress_from_gpu_server():
    response = requests.get("http://163.180.117.43:9003/api/proginfo")
    progress_info = response.text  # JSON 형식의 응답을 파싱하여 진행 정보 추출
    print(progress_info)
    await asyncio.sleep(10)
    return progress_info
