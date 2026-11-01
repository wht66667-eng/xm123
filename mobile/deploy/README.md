# Aliyun deployment preparation

Target provided by user: jouxyfwglzx.cn, resolved to 112.124.48.246 on 2026-11-01.
Deployment has NOT been performed. Local corresponding SSH key was rejected.

After obtaining working SSH access:
1. Inspect existing services, port use, domain/TLS configuration and website routes.
2. Choose a nonconflicting host or route with the user if the root hosts an existing site.
3. Install Python venv support, create service user fox-safety, upload app to /opt/fox-safety.
4. Create /opt/fox-safety/.venv; install requirements.txt and gunicorn. Set application files root-owned, allow service user to write upstream/database.db and its directory only.
5. Install fox-safety.service and start it; check local /api/library before exposing it.
6. Merge the nginx location into the proper HTTPS server block, run nginx -t then reload.
7. Verify public HTTPS library, session/captcha behavior and APK connectivity. Do not submit real exams during deployment checks.

Use exactly one Gunicorn worker because platform sessions are in process memory. Private signing keys are outside this project and are excluded from artifacts.
