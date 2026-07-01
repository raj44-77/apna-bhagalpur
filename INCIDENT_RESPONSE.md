# 🚨 Apna Bhagalpur — Incident Response Plan

## Emergency Contacts
| Role | Name | Phone | Email |
|------|------|-------|-------|
| Developer | Kumar Raj | +91-XXXXXXXXXX | rajkr2240@gmail.com |
| Backup | - | - | - |

---

## 🔴 Severity Levels

| Level | Example | Response Time |
|-------|---------|---------------|
| **P0 - Critical** | Site completely down, all clinics affected | 15 minutes |
| **P1 - High** | Booking not working, queue broken | 30 minutes |
| **P2 - Medium** | Analytics slow, minor UI issues | 2 hours |
| **P3 - Low** | Typo, cosmetic issue | 24 hours |

---

## 🛠️ Quick Recovery Commands

### Database Backup Restore
```bash
# 1. Download latest backup from GitHub Actions
# https://github.com/raj44-77/apna-bhagalpur/actions

# 2. Restore to Railway
mysql --host=zephyr.proxy.rlwy.net --port=22481 --user=root --password=MPZEuwCdbNknxDetgLbaQUCWrVjgZbdn railway < backup.sql

### Render Restart
1. Go to https://dashboard.render.com
2. Click apna-bhagalpur-api
3. Manual Deploy → Deploy latest commit

### Rollback to Previous Version
```bash
git log --oneline -5
git revert <commit-hash>
git push
# Render auto-deploys