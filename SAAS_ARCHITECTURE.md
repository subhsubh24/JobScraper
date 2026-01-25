# Career Operator: SaaS Architecture

## 🎯 Product Vision

**"Stop applying to jobs. Let AI run your career like a business operation."**

Career Operator is a premium AI-powered job search platform that automates discovery, scoring, prep, outreach, and coaching. Built for data-driven professionals who want to treat their career like a strategic operation.

---

## 💰 Monetization Strategy

### Pricing Tiers

**Free - "Starter"** ($0/month)
- 5 active jobs tracked
- Basic AI scoring
- 1 AI prep pack/month
- Community support
- **Goal**: Acquisition funnel, show value

**Pro - "Career Operator"** ($19/month or $190/year)
- 50 active jobs
- Unlimited AI scoring
- 10 AI prep packs/month
- AI Career Coach (20 messages/month)
- CRM + Outreach templates
- Email notifications
- Chrome extension
- Priority support
- **Target**: Active job seekers (3-6 month retention)

**Elite - "Executive Operator"** ($49/month or $490/year)
- Unlimited everything
- Unlimited AI prep packs
- Unlimited AI Career Coach
- Salary negotiation scripts
- Network mapping
- Advanced analytics
- Early access to features
- **Target**: Senior+ professionals

### Year 1 Revenue Goal: $10K ARR
- 50 Pro users × $19 = $950/month = $11,400/year ✅
- 10 Elite users × $49 = $490/month = $5,880/year ✅
- **Total**: $1,440/month = $17,280 ARR (exceeds goal!)

---

## 🏗️ Technical Architecture

### Database Schema (Multi-Tenant SaaS)

#### New Tables Added

**`user`** - User accounts and subscriptions
```sql
- user_id (PK)
- email (unique, indexed)
- password_hash (NULL for OAuth)
- full_name
- google_id, linkedin_id (OAuth)
- subscription_tier (free, pro, elite)
- subscription_status (active, canceled, past_due)
- stripe_customer_id, stripe_subscription_id
- prep_packs_used_this_month, ai_messages_used_this_month
- usage_reset_date
- resume_text, resume_embedding
- target_salary_min, target_locations, target_role_families
- trading_mode_enabled
- is_active, is_verified, verification_token
- created_at, updated_at, last_login
```

**`subscription`** - Subscription history and billing
```sql
- subscription_id (PK)
- user_id (FK)
- tier, status
- stripe_subscription_id, stripe_price_id, stripe_invoice_id
- amount_cents, currency, billing_interval
- trial_start, trial_end
- current_period_start, current_period_end
- canceled_at, ended_at
```

**`chat_message`** - AI Career Coach conversations
```sql
- message_id (PK)
- user_id (FK)
- role (user, assistant, system)
- content
- job_pk (optional context)
- context_type (general, job_search, interview_prep, negotiation)
- model_used, tokens_used, cost_cents
- created_at
```

#### Modified Tables (Multi-Tenant)

**All existing tables now have `user_id` foreign key:**
- `job_posting` → user_id (each user has their own job pipeline)
- `contact` → user_id
- `application` → user_id

**Benefits:**
- Complete data isolation between users
- Efficient queries with user_id indexes
- Easy to implement usage limits
- Can delete user data cleanly (GDPR compliance)

---

## 🔐 Authentication System

### Features

**Email/Password Authentication**
- Secure password hashing (werkzeug)
- Email verification tokens
- Password reset flow
- Session management

**OAuth Integration** (Google, LinkedIn)
- No password required
- Auto-verified accounts
- Link existing accounts

**JWT Tokens**
- 24-hour expiry
- Used for API authentication
- Payload includes user_id, email, tier

### Implementation

**AuthService** (`src/auth/auth_service.py`):
- `create_user()` - Register with email/password
- `create_oauth_user()` - Register via OAuth
- `authenticate_user()` - Login
- `generate_token()` - Create JWT
- `verify_token()` - Validate JWT
- `verify_email()` - Confirm email
- `request_password_reset()` - Forgot password
- `reset_password()` - Complete reset
- `update_subscription()` - Change tier
- `increment_prep_pack_usage()` - Track usage
- `increment_ai_message_usage()` - Track AI chat

**Decorators** (`src/auth/decorators.py`):
```python
@login_required
def protected_route():
    # g.user and g.db available
    pass

@subscription_required('pro')
def pro_feature():
    # Only pro+ users can access
    pass

@usage_limit_check('prep_pack')
def generate_prep():
    # Check if user has credits
    pass
```

---

## 💳 Stripe Integration

### Payment Flow

1. **User clicks "Upgrade to Pro"**
2. **Create Checkout Session**
   ```python
   StripeService.create_checkout_session(
       user=user,
       price_id='price_pro_monthly',
       success_url='/checkout/success',
       cancel_url='/pricing'
   )
   ```
3. **Redirect to Stripe Checkout** (handles payment)
4. **Webhook: `checkout.session.completed`**
   - Update user.subscription_tier = 'pro'
   - Create Subscription record
   - Reset usage counters
5. **User redirected to `/checkout/success`**

### Stripe Webhooks

**Handled Events:**
- `checkout.session.completed` → Activate subscription
- `customer.subscription.created` → Log subscription start
- `customer.subscription.updated` → Handle status changes
- `customer.subscription.deleted` → Downgrade to free
- `invoice.payment_succeeded` → Update billing record
- `invoice.payment_failed` → Mark as past_due

**Implementation:**
```python
@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    event = stripe.Webhook.construct_event(
        payload, sig_header, STRIPE_WEBHOOK_SECRET
    )

    StripeService.handle_webhook(
        db=get_session(),
        event_type=event['type'],
        event_data=event['data']['object']
    )

    return jsonify({'success': True})
```

### Customer Portal

Users can manage subscriptions via Stripe Customer Portal:
```python
StripeService.create_portal_session(
    user=user,
    return_url='/settings'
)
```

Features:
- Update payment method
- View invoices
- Cancel subscription
- Reactivate subscription

---

## 🤖 AI Career Coach

### The Premium Feature

**What makes it valuable:**
- Context-aware (knows your pipeline, resume, targets)
- Strategic, not generic (like a consultant, not chatbot)
- Actionable insights (specific next steps)
- Personalized to your goals

**Use Cases:**
1. **Strategy** - "How should I prioritize these 10 jobs?"
2. **Preparation** - "What should I focus on for my Google interview?"
3. **Negotiation** - "I have 2 offers, help me compare"
4. **Networking** - "How do I get a referral at Stripe?"
5. **Resume** - "Why am I not getting interviews?"

### Implementation

**CareerCoach** (`src/ai_coach/career_coach.py`):

```python
coach = CareerCoach()

# Chat with context
response = coach.chat(
    db=session,
    user=user,
    message="How should I prepare for my Citadel interview?",
    context_type='interview_prep',
    job_pk='abc-123'  # Links to specific job
)

# Get suggested questions based on pipeline stage
suggestions = coach.get_suggested_questions(user, db)
# ["How should I negotiate this offer?", ...]

# Get AI-generated insights
insights = coach.get_career_insights(user, db)
# {"stage": "interviewing", "insights": [...], "metrics": {...}}
```

**System Prompt:**
- Personalized with user's targets, salary, locations
- Expert positioning (career coach + strategist)
- Personality: Direct, actionable, data-driven
- Uses frameworks (STAR, MECE)
- References actual pipeline data

**Conversation Storage:**
- All messages saved to `chat_message` table
- Last 10 messages included in context
- Can reference specific jobs
- Tracks tokens and cost per message

**Usage Limits:**
- Free: 0 messages/month (teaser only)
- Pro: 20 messages/month
- Elite: Unlimited

---

## 📊 Usage Tracking & Limits

### How It Works

**User Model Methods:**
```python
user.can_generate_prep_pack()  # Check limit
user.can_send_ai_message()     # Check limit
```

**Enforcement via Decorators:**
```python
@usage_limit_check('prep_pack')
def generate_prep_pack(job_pk):
    # Only runs if user has credits
    AuthService.increment_prep_pack_usage(g.db, g.user.user_id)
    # ... generate prep pack
```

**Monthly Reset:**
- Each user has `usage_reset_date` (30 days from subscription start)
- When generating prep pack or sending message:
  - Check if `datetime.now() > usage_reset_date`
  - If yes, reset counters to 0 and set new reset date
  - Then increment usage

**Limits by Tier:**
```python
LIMITS = {
    'free': {'prep_packs': 1, 'ai_messages': 0, 'jobs': 5},
    'pro': {'prep_packs': 10, 'ai_messages': 20, 'jobs': 50},
    'elite': {'prep_packs': 999999, 'ai_messages': 999999, 'jobs': 999999}
}
```

### Upgrade Prompts

When limit hit:
```json
{
  "error": "Usage limit reached",
  "resource": "prep_pack",
  "current_tier": "free",
  "limit": 1,
  "used": 1,
  "upgrade_url": "/pricing"
}
```

---

## 🚀 Production Deployment

### Stack Recommendations

**Option 1: Railway (Easiest)**
- One-click deploy from GitHub
- Automatic PostgreSQL, Redis
- Environment variables in dashboard
- $5-20/month for starter traffic
- Built-in monitoring and logs

**Option 2: Render (Good balance)**
- Free PostgreSQL (1GB)
- Free Redis (25MB)
- Web service: $7/month
- Background workers: $7/month
- Total: ~$14/month

**Option 3: AWS (Most scalable)**
- RDS PostgreSQL
- ElastiCache Redis
- EC2 or ECS
- More complex but cheaper at scale
- ~$30-50/month to start

### Environment Variables (.env)

```bash
# App
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Database
DATABASE_URL=postgresql://user:pass@host:5432/career_operator

# Redis (for Celery)
REDIS_URL=redis://host:6379/0

# OpenAI
OPENAI_API_KEY=sk-...
AI_COACH_MODEL=gpt-4o

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_PRO_YEARLY=price_...
STRIPE_PRICE_ELITE_MONTHLY=price_...
STRIPE_PRICE_ELITE_YEARLY=price_...

# Email (SendGrid)
SENDGRID_API_KEY=SG....
FROM_EMAIL=noreply@careeroperator.com

# OAuth (optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
```

### Docker Setup

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/career_operator
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: career_operator
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  celery:
    build: .
    command: celery -A tasks worker -l info
    depends_on:
      - db
      - redis

volumes:
  pgdata:
```

### Migration from SQLite to PostgreSQL

```bash
# 1. Export from SQLite
python -c "
from src.db import get_session
from src.db.models import Base
# ... export logic
"

# 2. Update DATABASE_URL in .env

# 3. Create PostgreSQL schema
python -c "
from src.db.models import Base
from sqlalchemy import create_engine
import os

engine = create_engine(os.getenv('DATABASE_URL'))
Base.metadata.create_all(engine)
"

# 4. Import data

# 5. Test
```

---

## 📱 Progressive Web App (PWA)

### Why PWA Instead of Native App?

**Pros:**
- Single codebase (web app works everywhere)
- No App Store approval delays
- No 30% Apple/Google tax
- Instant updates (no app store review)
- Users can "install" on home screen
- Works offline with service workers
- Push notifications supported

**Cons:**
- Slightly less native feel
- Limited access to some device features
- Not discoverable in App Store

**Verdict for Year 1:** PWA is perfect. Build web app, make it installable. If you hit $50K ARR, consider native apps.

### Implementation

**manifest.json:**
```json
{
  "name": "Career Operator",
  "short_name": "CareerOp",
  "description": "AI-powered job search platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#4F46E5",
  "icons": [
    {
      "src": "/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Service Worker** (basic caching):
```javascript
// static/sw.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('career-operator-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/static/css/style.css',
        '/static/js/app.js'
      ]);
    })
  );
});
```

**Install prompt** (in base.html):
```javascript
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  // Show install button
  document.getElementById('install-button').style.display = 'block';
});

document.getElementById('install-button').addEventListener('click', async () => {
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`User response: ${outcome}`);
  deferredPrompt = null;
});
```

---

## 🎨 Next Steps: MVP Features

### Phase 1: Authentication & Payments (Week 1-2)
- [ ] Add auth routes to app.py
- [ ] Create login, signup, password reset pages
- [ ] Integrate Stripe checkout
- [ ] Add webhook endpoint
- [ ] Create pricing page
- [ ] Test full payment flow

### Phase 2: AI Career Coach UI (Week 3)
- [ ] Create chat interface page
- [ ] Add message history display
- [ ] Implement suggested questions
- [ ] Show usage limits
- [ ] Add "Upgrade to Pro" prompts

### Phase 3: User Dashboard (Week 4)
- [ ] Personalized homepage with insights
- [ ] Usage stats (prep packs, AI messages)
- [ ] Quick actions
- [ ] Recent activity feed

### Phase 4: Marketing & Launch (Week 5-6)
- [ ] Landing page with value prop
- [ ] Demo video
- [ ] Pricing page with comparison
- [ ] Blog post: "How I built this"
- [ ] ProductHunt launch
- [ ] Twitter/LinkedIn promotion

---

## 💡 Growth Hacks

### 1. Freemium with Clear Value
- Give 1 free prep pack → they see the quality
- Show AI Coach teaser → "Upgrade to ask unlimited questions"
- Email: "You have 4 unused prep pack credits" (FOMO)

### 2. Viral Loops
- "Share your prep pack" → generates unique link
- Friend signs up via link → both get +1 free prep pack
- Leaderboard: "Top users this month" (gamification)

### 3. Content Marketing
- Blog: "I analyzed 1,000 Data Science job postings - here's what I found"
- Twitter threads: Job search tips with screenshots of Career Operator
- YouTube: "How to use AI to get a $200k job in 2026"

### 4. Partnerships
- Partner with bootcamps (offer to their students)
- Partner with career coaches (white label version)
- Partner with job boards (embed Career Operator)

### 5. Retention Tactics
- Weekly email: "Your pipeline needs attention" (pull users back)
- Push notifications: "New job match: 92/100 score"
- Success stories: "John got 3 offers using Career Operator"

---

## 📈 Key Metrics to Track

**Acquisition:**
- Signups/week
- Signup source (organic, paid, referral)
- Signup → Activation rate (uploaded resume + added 1 job)

**Activation:**
- Free → Pro conversion rate
- Time to first prep pack generation
- Time to first AI Coach message

**Revenue:**
- MRR (Monthly Recurring Revenue)
- Churn rate (% cancel each month)
- LTV (Lifetime Value) = Avg subscription length × monthly price
- CAC (Customer Acquisition Cost) = Marketing spend / New customers

**Engagement:**
- DAU/MAU (Daily Active / Monthly Active)
- Prep packs generated/user/month
- AI messages sent/user/month
- Jobs applied to/user/month

**Retention:**
- 30-day retention
- 90-day retention
- Reactivation rate (canceled → resubscribed)

**Goals for Year 1:**
- 1,000 signups
- 5% free → paid conversion = 50 paid users
- $20 average monthly revenue = $1,000 MRR
- 3 month avg retention = $60 LTV
- <$30 CAC via organic + content marketing

---

## 🎯 Your First 10 Customers

**How to get them:**

1. **Personal Network** (0-3 customers)
   - Post on LinkedIn: "I built an AI job search tool, looking for beta testers"
   - DM friends who are job searching
   - Offer free Pro for 3 months in exchange for feedback

2. **Reddit** (3-6 customers)
   - r/datascience, r/cscareerquestions
   - Post: "I built a tool that scores jobs and generates interview prep packs"
   - Offer early adopter discount (50% off first 3 months)

3. **Twitter** (6-8 customers)
   - Share screenshots of features
   - Thread: "How I'm using AI to optimize my job search"
   - Include link in profile

4. **Indiehackers/ProductHunt** (8-10 customers)
   - Launch on ProductHunt with demo video
   - Post on Indiehackers with your journey
   - Offer "lifetime Pro" to first 100 users

Once you have 10 paying customers:
- Interview them (what do they love? what's missing?)
- Get testimonials
- Ask for referrals
- Double down on what's working

---

## 🚀 Ready to Build?

You now have:
- ✅ Multi-tenant database schema
- ✅ Authentication system (email + OAuth)
- ✅ Stripe payment integration
- ✅ AI Career Coach
- ✅ Usage tracking and limits
- ✅ Deployment architecture

**Next: Integrate these into app.py and build the UI!**
