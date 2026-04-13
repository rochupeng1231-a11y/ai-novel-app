#!/bin/bash
# AI写小说应用启动脚本
# 用法: ./start.sh

APP_DIR="/root/.openclaw/agents/team-leader/workspace/ai-novel-app"
PID_FILE="/tmp/ai-novel-uvicorn.pid"

start() {
    echo "启动 uvicorn..."
    cd "$APP_DIR"
    nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
    echo $! > "$PID_FILE"
    echo "uvicorn 已启动 (PID: $(cat $PID_FILE))"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "停止 uvicorn (PID: $PID)..."
        kill "$PID" 2>/dev/null
        rm -f "$PID_FILE"
    else
        echo "未找到 PID 文件"
    fi
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "uvicorn 运行中 (PID: $PID)"
        else
            echo "uvicorn 未运行"
        fi
    else
        echo "uvicorn 未运行"
    fi
}

case "$1" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    *) echo "用法: $0 {start|stop|restart|status}" ;;
esac
