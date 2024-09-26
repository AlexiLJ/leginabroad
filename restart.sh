systemctl restart gunicorn
systemctl daemon-reload
systemctl restart gunicorn.socket gunicorn.service
nginx -t && sudo systemctl restart nginx
