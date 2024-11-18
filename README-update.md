# Simple update steps

First, ssh to the server

`ssh -l root -i [path-to-pem-file-from-vault] linkedtrust.us`

Once connected, do the following:

```
 cd /linkedtrust
 cd site*
 git pull
 . .venv/bin/activate
 cd New*
 python manage.py collectstatic
 supervisorctl restart linkedtrust
```
