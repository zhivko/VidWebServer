# VidWebServer
crypto graphs and buy &amp; sell signals

Generate self signed cert
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

nginx flask config from
https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https

## To start server enter following line in command line

```
sudo apt install locales-all
sudo apt install gunicorn
sudo apt install certbot python3-certbot-nginx
```

`gunicorn --certfile cert.pem --keyfile key.pem -b 127.0.0.1:8000 app:app`
`gunicorn -b 127.0.0.1:8000 app:app`


## nginx.conf

Install nginx.com by `sudo apt install nginx certbot python3-certbot-nginx`
Below is sample nginx.conf, you can edit it on linux by

`sudo nano /etc/nginx.conf`

`sudo systemctl restart nginx`

```
server {
    listen 443 ssl http2;
    server_name crypto.zhivko.eu;
    ssl_certificate /etc/letsencrypt/live/crypto.zhivko.eu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/crypto.zhivko.eu/privkey.pem;

	 rewrite ^/(.*)/favicon.info$ $1/static/favicon.info last;
	 
    location ~* /index.html | /deleteline | /addline | /scroll {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Prefix /;
        proxy_set_header Host $host;
        allow all;
    }

   location / {
       deny all;
   }
}
```


# certbot and nginx

from
`https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04`

`sudo certbot --nginx -d crypto.zhivko.eu`


#using gunicorn

`gunicorn app:app`


# creating ubuntu service

Edit file with

`sudo nano /etc/systemd/system/myproject.service`

paste following:

```
[Unit]
Description=My Gunicorn project description
After=network.target

[Service]
User=klemen
Group=www-data
WorkingDirectory=/home/klemen/git/VidWebServer
ExecStart=/usr/bin/gunicorn --bind 127.0.0.1:8000 app:app --access-logfile ./log/access.log --error-logfile ./log/log.log --capture-output --log-level debug

[Install]
WantedBy=multi-user.target
After=network-online.target
Wants=network-online.target
```

Restart daemon with:

`sudo systemctl daemon-reload`

Start with:

`sudo systemctl restart myproject.service`

# for renewing cert

`sudo certbot renew -- nginx`
