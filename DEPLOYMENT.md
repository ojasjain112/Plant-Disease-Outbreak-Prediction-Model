# 🚀 Deploying to Render

This guide will help you deploy the Weather-Driven Plant Disease Outbreak Predictor to Render.

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com) (free tier available)

## Deployment Files Created

The following files have been added for Render deployment:

- **render.yaml** - Render service configuration (Infrastructure as Code)
- **Procfile** - Defines how to start the web service
- **runtime.txt** - Specifies Python version
- **build.sh** - Build script to set up the environment
- **requirements.txt** - Updated with `gunicorn` for production

## Step-by-Step Deployment

### Step 1: Prepare Your Code

**1. Clean up for GitHub (if not done already):**

```powershell
# Remove virtual environment and cache
Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Remove-Item -Path "cache\*" -Force -ErrorAction SilentlyContinue
```

**2. Initialize Git repository (if not already done):**

```powershell
git init
git add .
git commit -m "Initial commit: Weather-Driven Plant Disease Predictor"
```

**3. Create GitHub repository:**

- Go to [github.com](https://github.com) → New Repository
- Name: `plant-disease-predictor` (or your choice)
- Don't initialize with README (you already have one)
- Click "Create repository"

**4. Push to GitHub:**

```powershell
git remote add origin https://github.com/YOUR_USERNAME/plant-disease-predictor.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy to Render

#### Option A: Using render.yaml (Recommended - Infrastructure as Code)

1. **Go to Render Dashboard**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Sign up/Login

2. **Create New Blueprint**
   - Click "New" → "Blueprint"
   - Connect your GitHub account if not already connected
   - Select your repository: `plant-disease-predictor`
   - Render will automatically detect `render.yaml`

3. **Review and Deploy**
   - Click "Apply"
   - Render will automatically:
     - Install dependencies
     - Generate training data
     - Train ML models
     - Start the application
   
4. **Wait for Deployment**
   - First deployment takes 5-10 minutes
   - Watch the build logs for progress

5. **Access Your App**
   - Once deployed, you'll get a URL like: `https://disease-outbreak-predictor.onrender.com`

---

#### Option B: Manual Setup (Alternative)

1. **Go to Render Dashboard**
   - Click "New" → "Web Service"

2. **Connect Repository**
   - Select your GitHub repository
   - Click "Connect"

3. **Configure Service**
   - **Name:** `disease-outbreak-predictor`
   - **Region:** Oregon (US West) - or nearest to you
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python scripts/data_ingest.py --samples 1000 && python scripts/train_models.py
     ```
   - **Start Command:**
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
     ```

4. **Environment Variables** (Optional)
   - Click "Advanced" → "Add Environment Variable"
   - Add:
     - `PYTHON_VERSION` = `3.10.0`
     - `DEBUG` = `false`

5. **Instance Type**
   - Select **Free** tier (512MB RAM, enough for this app)

6. **Create Web Service**
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment

---

### Step 3: Verify Deployment

1. **Check Build Logs**
   - In Render dashboard → Your service → "Logs" tab
   - Look for:
     ```
     Installing dependencies...
     Generating training data...
     Training models...
     Starting gunicorn...
     Application initialized successfully
     ```

2. **Test Your App**
   - Click the provided URL (e.g., `https://disease-outbreak-predictor.onrender.com`)
   - You should see the main interface
   - Try making a prediction to verify it works

3. **Common First-Time Issues**
   - **Build timeout:** First build may take 10+ minutes due to ML libraries
   - **Memory issues:** Free tier has 512MB - models are optimized to fit
   - **Cold starts:** Free tier sleeps after inactivity, takes ~30s to wake up

---

## Configuration Details

### render.yaml Explained

```yaml
services:
  - type: web                 # Web service type
    name: disease-outbreak-predictor
    env: python              # Python runtime
    region: oregon           # US West region (closest to Open-Meteo servers)
    plan: free               # Free tier (upgrade to paid for better performance)
    branch: main             # Git branch to deploy
    buildCommand: |          # Commands run during build
      pip install -r requirements.txt &&
      python scripts/data_ingest.py --samples 1000 &&
      python scripts/train_models.py
    startCommand: gunicorn app:app  # Start the app with gunicorn
    envVars:
      - key: PORT
        value: 10000         # Render provides this automatically
```

### Procfile Explained

```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

- **gunicorn** - Production WSGI server (replaces Flask dev server)
- **app:app** - Module:application (app.py:app object)
- **--workers 2** - Two worker processes (good for free tier)
- **--timeout 120** - 2 minute timeout for long predictions

---

## Performance Optimization

### Free Tier Limitations

- **512MB RAM** - Enough for our models
- **Sleeps after 15 min inactivity** - First request after sleep takes ~30s
- **750 hours/month** - Effectively 24/7 for one service

### Upgrade Options (if needed)

**Starter Plan ($7/month):**
- 512MB RAM
- No sleep
- Custom domains
- Faster builds

**Standard Plan ($25/month):**
- 2GB RAM
- Better performance
- Multiple workers

---

## Monitoring & Maintenance

### View Logs

```bash
# In Render dashboard
Logs tab → Real-time logs
```

### Redeploy

**Option 1: Auto-deploy (recommended)**
- Enable "Auto-Deploy" in Render settings
- Every git push automatically deploys

**Option 2: Manual deploy**
- In Render dashboard → "Manual Deploy" → "Deploy latest commit"

### Update Code

```powershell
# Make changes locally
git add .
git commit -m "Update: description of changes"
git push origin main

# If auto-deploy is enabled, Render will automatically deploy
# Otherwise, click "Manual Deploy" in Render dashboard
```

---

## Troubleshooting

### Build Fails

**Problem:** Build times out or fails

**Solutions:**
1. Check logs for specific error
2. Ensure `requirements.txt` is correct
3. Verify Python version matches (3.10.0)
4. Try reducing `--samples` in build command to 500

### App Won't Start

**Problem:** Build succeeds but app doesn't start

**Solutions:**
1. Check start command is correct: `gunicorn app:app`
2. Verify `app.py` has `app = Flask(__name__)`
3. Check logs for Python errors

### Prediction Fails

**Problem:** App loads but predictions error

**Solutions:**
1. Ensure models were trained during build
2. Check `models/` directory exists and has .pkl/.json files
3. Verify Open-Meteo API is accessible (check logs)

### Slow Performance

**Problem:** App is slow or times out

**Solutions:**
1. Upgrade from free tier
2. Reduce feature engineering windows in `config.py`
3. Add caching (already implemented)
4. Use fewer `--samples` during training

---

## Environment Variables (Advanced)

If you need to add secrets or configuration:

**In Render Dashboard:**
1. Go to your service → "Environment" tab
2. Add variables:
   - `SECRET_KEY` - Flask secret key (random string)
   - `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR
   - `CACHE_DURATION_SECONDS` - Cache timeout (default 3600)

**In render.yaml:**
```yaml
envVars:
  - key: SECRET_KEY
    generateValue: true  # Auto-generate secure key
  - key: LOG_LEVEL
    value: INFO
```

---

## Custom Domain (Optional)

**Free Tier:** `https://disease-outbreak-predictor.onrender.com`

**Custom Domain (Starter plan+):**
1. Render dashboard → Your service → "Settings"
2. "Custom Domain" → Add your domain
3. Update DNS records as instructed by Render
4. SSL certificate automatically provisioned

---

## Cost Estimate

**Free Tier:**
- ✅ $0/month
- ✅ 750 hours (enough for 1 service 24/7)
- ⚠️ Sleeps after 15min inactivity
- ⚠️ 512MB RAM

**Starter Tier ($7/month):**
- ✅ No sleep
- ✅ Custom domains
- ✅ 512MB RAM
- ✅ Faster builds

**For this project:** Free tier is sufficient for demonstration/portfolio!

---

## Next Steps After Deployment

1. **Test thoroughly** - Make predictions for different locations
2. **Share the URL** - Add to your resume/portfolio
3. **Monitor usage** - Check Render dashboard for metrics
4. **Add to README** - Update README with live demo link:
   ```markdown
   ## 🌐 Live Demo
   
   Try the live application: [https://disease-outbreak-predictor.onrender.com](https://disease-outbreak-predictor.onrender.com)
   ```

5. **Set up monitoring** - Use Render's built-in metrics
6. **Enable auto-deploy** - Automatic deployment on git push

---

## Security Notes

✅ **Already configured:**
- Secret key for Flask sessions
- HTTPS automatically enabled by Render
- No sensitive data in repository

⚠️ **Best practices:**
- Don't commit `.env` files with secrets
- Use Render's environment variables for sensitive config
- Keep dependencies updated (`pip list --outdated`)

---

## Support

**Render Documentation:** [render.com/docs](https://render.com/docs)  
**Render Community:** [community.render.com](https://community.render.com)  
**Project Issues:** Open an issue in your GitHub repo

---

## Summary Checklist

- [x] Create Render account
- [x] Push code to GitHub
- [x] Deploy via render.yaml or manual setup
- [x] Wait for build (5-10 minutes)
- [x] Test the live URL
- [x] Share your deployed app!

**Your app will be live at:** `https://disease-outbreak-predictor.onrender.com` 🎉

---

*Deployment files created on: November 29, 2025*
