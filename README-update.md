# Simple update steps

```
 cd /linkedtrust
 cd site*
 git pull
 . .venv/bin/activate
 cd New*
 python manage.py collectstatic
 supervisorctl restart linkedtrust
```
