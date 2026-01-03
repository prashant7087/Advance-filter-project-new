# Backend Deployment to Vercel

This Flask backend uses MediaPipe and OpenCV for facial analysis.

## Project Structure

```
backend/
├── api/
│   └── index.py          # Vercel serverless function
├── measurement_logic.py  # Core measurement logic
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── Dockerfile           # For Docker-based deployments (Cloud Run, etc.)
```

## Deploy to Vercel

### Step 1: Install Vercel CLI

```bash
npm i -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Deploy the Backend

Navigate to the backend folder and deploy:

```bash
cd backend
vercel
```

Follow the prompts:
- Set up and deploy: **Yes**
- Which scope: Select your account
- Link to existing project: **No** (for first time)
- What's your project's name: `lenskart-ai-backend` (or your preferred name)
- In which directory is your code located: `./`
- Want to modify these settings: **No**

### Step 4: Get Your Production URL

After deployment, Vercel will give you a URL like:
```
https://lenskart-ai-backend.vercel.app
```

**Note this URL - you'll need it for the frontend!**

### Step 5: Deploy to Production

```bash
vercel --prod
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/process_image` | POST | Analyze image for optical measurements |

## Testing the API

```bash
curl https://YOUR-URL.vercel.app/health
```

Expected response:
```json
{"message": "API is working fine on Vercel!"}
```

## Important Notes

> ⚠️ **MediaPipe Dependencies**: If deployment fails due to native dependencies, consider using:
> - Google Cloud Run (Dockerfile included)
> - Railway.app
> - Render.com
>
> These platforms support Docker and can handle native C++ dependencies.

## Environment Variables (Optional)

If you need to add environment variables:

```bash
vercel env add VARIABLE_NAME
```

Or set them in the Vercel Dashboard under Project Settings > Environment Variables.
