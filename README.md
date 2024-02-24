# VidWebServer
crypto graphs and buy &amp; sell signals

Generate self signed cert
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

nginx flask config from
https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https

## To start server enter following line in command line

```
sudo apt install gunicorn
sudo apt install certbot python3-certbot-nginx
```

`gunicorn --certfile cert.pem --keyfile key.pem -b 127.0.0.1:8000 app:app`


## nginx.conf

Install nginx.com by `sudo apt install nginx certbot python3-certbot-nginx`
Below is sample nginx.conf, you can edit it on linux by

`sudo nano /etc/nginx.conf`

```
server {
    listen 443 ssl http2;
    server_name crypto.kz.com;
    ssl_certificate /home/kz/git/VidWebServer/cert.pem;
    ssl_certificate_key /home/kz/git/VidWebServer/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Prefix /;
    }
}

server {
    listen 80;
    server_name example.com;
    location / {
        return 301 https://$host$request_uri;
    }
}
```


# certbot and nginx

from
`https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04`

`sudo certbot --nginx -d crypto.zhivko.eu -d zhivko.eu`


