#!/bin/bash

case "$1" in
    start)
        sudo supervisorctl start linkedtrust
        ;;
    stop)
        sudo supervisorctl stop linkedtrust
        ;;
    restart)
        sudo supervisorctl restart linkedtrust
        ;;
    status)
        sudo supervisorctl status linkedtrust
        ;;
    logs)
        sudo tail -f /var/log/supervisor/linkedtrust.log
        ;;
    errors)
        sudo tail -f /var/log/supervisor/linkedtrust.err.log
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|errors}"
        exit 1
        ;;
esac
