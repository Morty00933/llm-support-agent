#!/bin/sh
# Replace backend hostname in nginx config if BACKEND_HOST is set
if [ -n "$BACKEND_HOST" ]; then
  sed -i "s|http://backend:8000|http://${BACKEND_HOST}:8000|g" /etc/nginx/conf.d/default.conf
fi
exec nginx -g 'daemon off;'
