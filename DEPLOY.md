# Deploying LivelyBorg AI

One small Linux server runs everything with Docker Compose:

```
Internet ──HTTPS──> Caddy ──/api/*──> api  (FastAPI + scheduler, SQLite on a volume)
                          └─ else ───> web  (Next.js)
```

- **Cost: ₦0** with Oracle Cloud's Always Free tier and a free DuckDNS address. A proper domain (.com / .ng) is optional, about $10–15 a year.
- The API must run **24/7**: the scheduler locks every prediction before kickoff. Downtime leaves permanent gaps in the public track record.
- Why not Render/Vercel free tiers: Render's free plan sleeps when idle and has no persistent disk, which would stop the scheduler and erase the track record. Vercel's free plan doesn't allow commercial use.

---

## Alternative: Railway (about $5/month, no server to manage)

Two services built from this repo, no Caddy. The web service forwards `/api/*` to the API over Railway's private network, so there is one public address and no CORS setup.

| Service | Dockerfile (`RAILWAY_DOCKERFILE_PATH`) | Volume | Variables |
|---|---|---|---|
| `api` | `apps/api/Dockerfile` | `/app/data` | `PORT=8000`, `RAILWAY_RUN_UID=0` (volumes mount as root), `ADMIN_TOKEN`, `FOOTBALL_DATA_KEY`, `GOOGLE_CLIENT_ID` (for sign-in), `ADMIN_EMAILS` (optional), `GEMINI_API_KEY` (optional) |
| `web` | `apps/web/Dockerfile` | none | `API_INTERNAL_URL=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:8000` |

Give only `web` a public domain.

**Sign in with Google (accounts, saved fixtures, admin reports).** In [Google Cloud Console](https://console.cloud.google.com/apis/credentials) create an OAuth client ID of type *Web application*, add the site's public address under *Authorized JavaScript origins*, and put the client ID in the `api` service's `GOOGLE_CLIENT_ID`. Until it is set, the site hides sign-in. Admins are the emails in `ADMIN_EMAILS` (default `devtonicllc@gmail.com`); they must sign in with a Google-verified address, and the role is checked on the server for every request. Set the `api` health check path to `/api/v1/health`. Keep the API at one replica, because the scheduler runs inside it.

---

## 1. Create the server (Oracle Cloud Always Free)

1. Sign up at <https://www.oracle.com/cloud/free/>. A card is required for identity checks; Always Free resources are not charged.
   Pick your **home region** carefully, because it can't be changed later. Johannesburg is closest to Lagos. If it has no free capacity, London or Frankfurt work well.
2. Create an instance with these settings:
   - Image: **Ubuntu 24.04**.
   - Shape: **VM.Standard.A1.Flex** (Ampere), **2 OCPU / 12 GB**, which is within the free allowance.
   - SSH key: add your public key, or let Oracle generate one and download it.
3. In the instance's **Virtual Cloud Network → Security List**, add ingress rules for TCP **80** and **443** from `0.0.0.0/0`.
4. SSH in (`ssh ubuntu@<public-ip>`), then open the same ports in Ubuntu's own firewall. Oracle's images block them by default:
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

## 2. Get a web address

- **Free:** sign in at <https://www.duckdns.org>, create a subdomain (e.g. `livelyborg`), and set its IP to the server's public IP. Your address is then `livelyborg.duckdns.org`.
- **Later:** buy a domain and add an **A record** pointing to the server IP. Then change `SITE_ADDRESS` (step 4) and restart Caddy.

## 3. Install Docker on the server

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
```

## 4. Copy the code and configure it

Copy the project to the server, either with `git clone` from your private GitHub repo or with `scp`. Leave out `node_modules`, `.venv`, `.next` and `data`, which are rebuilt. Then create `.env` from the example:

```bash
cd lively-borg
cp .env.example .env
openssl rand -hex 32   # use the output as ADMIN_TOKEN
nano .env
```

| Setting | Value |
|---|---|
| `SITE_ADDRESS` | `livelyborg.duckdns.org` (your address) |
| `ALLOWED_ORIGINS` | `https://livelyborg.duckdns.org` |
| `ADMIN_TOKEN` | the random value from `openssl` |
| `FOOTBALL_DATA_KEY` | your football-data.org key |
| `GEMINI_API_KEY` | optional (a working key from aistudio.google.com) |

## 5. Start it

```bash
docker compose up -d --build
docker compose logs -f api      # watch the first start
```

On an empty server the API **sets itself up automatically**. It downloads 10 seasons of results (about 2 minutes) and trains the model (about 5 minutes), before locking any prediction. Then open `https://<your address>`. Caddy obtains the HTTPS certificate on the first visit.

### Optional: keep the predictions already locked on your PC

Doing this keeps the track record continuous and skips the first-start setup. Do it **before** the first `up`:

```bash
docker compose create api
docker compose cp ./data/livelyborg.db api:/app/data/livelyborg.db   # copy data/ from your PC first
docker compose cp ./data/models api:/app/data/models
docker compose run --rm -u root --entrypoint chown api -R app:app /app/data
docker compose up -d --build
```

After that, **turn off the scheduler on your PC** (`LIVELYBORG_AUTO_REFRESH=0` in its `.env`). There must be only one official ledger.

## 6. Check it is healthy

- `https://<address>/api/v1/health` shows `model_loaded: true`.
- `https://<address>/api/v1/data/status` shows the history loaded, fixtures, locked predictions and last cycle.
- `https://<address>/api/v1/track-record/verify` shows `valid: true`.
- Run the pipeline immediately:
  ```bash
  curl -X POST -H "X-Admin-Token: <ADMIN_TOKEN>" https://<address>/api/v1/jobs/run
  ```
- Free uptime alerts: add the health URL at <https://uptimerobot.com>.

## 7. Day-to-day

| Task | Command |
|---|---|
| Deploy new code | copy/pull the code, then `docker compose up -d --build` (data is kept) |
| Logs | `docker compose logs -f api` |
| Retrain now | `docker compose exec api python -m apps.api.app.jobs --retrain` |
| Download backups | `docker compose cp api:/app/data/backups ./backups`, then `scp` them to your PC |

- **Backups:** the API writes a daily database backup to `/app/data/backups` and keeps 14. They sit on the same disk, so **copy them off the server regularly**. The prediction ledger can't be recreated if lost.
- **Automatic jobs:** the scheduler runs every 3 hours and retrains weekly. Keep the API at **one worker**; the Dockerfile already does this.

## Before going public

- Legal: get advice on Lagos State Lottery and Gaming Authority and national rules for tipster/prediction services.
- Add a privacy policy and terms of use. The site stores no personal data; the 18+ confirmation and theme are kept in the visitor's browser only.
- Apply to SportyBet and Bet9ja affiliate programmes for real booking codes and income.
