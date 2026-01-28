#!/bin/bash

# Configuration
SERVICE_DIR="/etc/systemd/system"
FILES_SERVICE="gpt-sovits-files.service"
TRAINING_SERVICE="gpt-sovits-training.service"
WORK_DIR="/opt/GPT-SoVITS"

# Colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

function install() {
    echo -e "${GREEN}Installing services...${NC}"
    
    # Check if service files exist in current directory
    if [ ! -f "$FILES_SERVICE" ] || [ ! -f "$TRAINING_SERVICE" ]; then
        echo "Error: Service files not found in current directory."
        exit 1
    fi

    # Copy to systemd directory
    cp "$FILES_SERVICE" "$SERVICE_DIR/"
    cp "$TRAINING_SERVICE" "$SERVICE_DIR/"
    
    # Reload daemon
    systemctl daemon-reload
    
    # Enable services
    systemctl enable "$FILES_SERVICE"
    systemctl enable "$TRAINING_SERVICE"
    
    echo -e "${GREEN}Services installed and enabled successfully!${NC}"
    echo "You can now run './service_manager.sh start'"
}

function start() {
    echo -e "${GREEN}Starting services...${NC}"
    systemctl start "$FILES_SERVICE"
    systemctl start "$TRAINING_SERVICE"
    echo "Services started."
}

function stop() {
    echo -e "${GREEN}Stopping services...${NC}"
    systemctl stop "$FILES_SERVICE"
    systemctl stop "$TRAINING_SERVICE"
    echo "Services stopped."
}

function restart() {
    echo -e "${GREEN}Restarting services...${NC}"
    systemctl restart "$FILES_SERVICE"
    systemctl restart "$TRAINING_SERVICE"
    echo "Services restarted."
}

function status() {
    echo -e "${GREEN}Checking status...${NC}"
    systemctl status "$FILES_SERVICE" "$TRAINING_SERVICE" --no-pager
}

function logs() {
    echo -e "${GREEN}Showing logs (Ctrl+C to exit)...${NC}"
    journalctl -u "$FILES_SERVICE" -u "$TRAINING_SERVICE" -f
}

# Main logic
case "$1" in
    install)
        install
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs}"
        exit 1
        ;;
esac
