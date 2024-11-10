sudo systemctl restart gunicorn
sudo systemctl daemon-reload  # reload the systemd manager configuration
sudo systemctl restart gunicorn.socket gunicorn.service
sudo nginx -t && sudo systemctl restart nginx
