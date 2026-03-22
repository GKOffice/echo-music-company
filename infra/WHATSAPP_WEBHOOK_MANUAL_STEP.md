# WhatsApp Webhook Registration — Manual Step Required

## Status
- Webhook endpoint: VERIFIED (returns challenge correctly)
- Subscription: NOT YET REGISTERED (requires app access token)

## Why Manual?
Meta's Graph API requires an **app access token** (`client_id` + `client_secret`) to register webhook subscriptions. The WhatsApp API token (system/user token) cannot be used for this endpoint.

No `FACEBOOK_APP_SECRET` or `WHATSAPP_APP_SECRET` was found in `.env`.

## Steps to Complete

### 1. Get your App Secret
- Go to https://developers.facebook.com/apps/1642376483426457/settings/basic/
- Copy the **App Secret**

### 2. Get an App Access Token
```bash
curl -s "https://graph.facebook.com/oauth/access_token?client_id=1642376483426457&client_secret=YOUR_APP_SECRET&grant_type=client_credentials" | python3 -m json.tool
```
This returns: `{"access_token": "APP_ACCESS_TOKEN", "token_type": "bearer"}`

### 3. Register the Webhook Subscription
```bash
curl -s -X POST "https://graph.facebook.com/v18.0/1642376483426457/subscriptions" \
  -d "object=whatsapp_business_account" \
  -d "callback_url=https://api-production-14b6.up.railway.app/api/v1/whatsapp/webhook" \
  -d "verify_token=melodio_webhook_2026" \
  -d "fields=messages" \
  -d "access_token=APP_ACCESS_TOKEN" | python3 -m json.tool
```
Expected response: `{"success": true}`

### 4. Verify the Subscription
```bash
curl -s "https://graph.facebook.com/v18.0/1642376483426457/subscriptions?access_token=APP_ACCESS_TOKEN" | python3 -m json.tool
```

### 5. Save the App Secret to .env
Add to `/Users/bm-007/projects/echo/.env`:
```
WHATSAPP_APP_SECRET=YOUR_APP_SECRET
```

## Configuration Reference
| Key | Value |
|-----|-------|
| App ID | 1642376483426457 |
| Phone Number ID | 1086543297868419 |
| Webhook URL | https://api-production-14b6.up.railway.app/api/v1/whatsapp/webhook |
| Verify Token | melodio_webhook_2026 |
| Subscribed Fields | messages |
