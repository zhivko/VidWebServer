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

`sudo nano /etc/nginx/sites-enabled/default`

`sudo nginx -t`


`sudo systemctl restart nginx`

```
server {
        index index.html;
        server_name crypto.zhivko.eu; # managed by Certbot


        location ~* /index.html|/scroll {
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded-Prefix /;
                proxy_set_header Host $host;
                allow all;
        }

        location ~* /deleteline|/addline {
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded-Prefix /;
                proxy_set_header Host $host;
                allow 89.233.122.140;
                deny all;
        }


        location / {
                deny all;
        }

        listen [::]:443 ssl ipv6only=on; # managed by Certbot
        listen 443 ssl; # managed by Certbot
        ssl_certificate /etc/letsencrypt/live/crypto.zhivko.eu/fullchain.pem; # managed by Certbot
        ssl_certificate_key /etc/letsencrypt/live/crypto.zhivko.eu/privkey.pem; # managed by Certbot
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

        error_log    /var/log/nginx/crypto.zhivko.eu.log debug;
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
After=network-online.target
Wants=network-online.target
Requires=redis-server.service

[Service]
User=klemen
Group=www-data
WorkingDirectory=/home/klemen/git/VidWebServer
#ExecStart=/usr/bin/gunicorn --bind 127.0.0.1:8000 app:app --access-logfile ./log/access.log --error-logfil>
ExecStart=/usr/bin/gunicorn --config gunicorn.conf.py app:app
TimeoutStopSec=2s

[Install]
WantedBy=multi-user.target
```

Restart daemon with:

`sudo systemctl daemon-reload`

Start with:

`sudo systemctl restart myproject.service`

# for renewing cert

`sudo certbot renew -- nginx`
