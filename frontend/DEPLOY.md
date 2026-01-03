# Frontend Deployment to Vercel

This is a static HTML frontend for the Lenskart AI Fitter.

## Project Structure

```
frontend/
├── index.html    # Main application
└── vercel.json   # Vercel configuration
```

## Deploy to Vercel

### Step 1: Update the API URL

**IMPORTANT**: Before deploying, edit `index.html` and update the API URL:

```javascript
// Find this line in index.html (around line 613):
const API_BASE_URL = 'https://YOUR-BACKEND.vercel.app';

// Replace with your actual backend URL:
const API_BASE_URL = 'https://lenskart-ai-backend.vercel.app';
```

### Step 2: Install Vercel CLI (if not already installed)

```bash
npm i -g vercel
```

### Step 3: Login to Vercel

```bash
vercel login
```

### Step 4: Deploy the Frontend

Navigate to the frontend folder and deploy:

```bash
cd frontend
vercel
```

Follow the prompts:
- Set up and deploy: **Yes**
- Which scope: Select your account
- Link to existing project: **No** (for first time)
- What's your project's name: `lenskart-ai-fitter` (or your preferred name)
- In which directory is your code located: `./`
- Want to modify these settings: **No**

### Step 5: Deploy to Production

```bash
vercel --prod
```

## Your Live Site

After deployment, your site will be available at:
```
https://lenskart-ai-fitter.vercel.app
```

## Custom Domain (Optional)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to Settings > Domains
4. Add your custom domain

## Deployment Order

1. **Deploy Backend First** → Get the backend URL
2. **Update Frontend** → Set the backend URL in `index.html`
3. **Deploy Frontend** → Your app is live!

## Troubleshooting

### CORS Errors
If you see CORS errors, make sure:
- The backend is deployed and running
- The backend URL in frontend is correct
- The backend has CORS enabled (it does by default)

### Camera Not Working
- Ensure you're accessing the site via HTTPS
- Grant camera permissions when prompted
- Some browsers require user interaction before accessing the camera
