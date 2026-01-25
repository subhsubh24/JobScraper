# Career Operator: Launch Checklist

## 🚀 Phase 1: Backend Deployment (Week 1)

### Day 1: Railway Setup
- [ ] Create Railway account (railway.app)
- [ ] Connect GitHub repo
- [ ] Add PostgreSQL database
- [ ] Set environment variables:
  ```
  DATABASE_URL=<from Railway PostgreSQL>
  OPENAI_API_KEY=sk-...
  SECRET_KEY=<random 32-char string>
  ```
- [ ] Deploy API
- [ ] Test endpoint: `https://your-app.railway.app/health`

### Day 2: Database Setup
- [ ] Run migrations:
  ```bash
  railway run python -c "from src.db.models import Base; from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL')); Base.metadata.create_all(engine)"
  ```
- [ ] Test user registration: `POST /api/auth/register`
- [ ] Test job creation: `POST /api/jobs`

### Day 3: API Testing
- [ ] Create Postman collection
- [ ] Test all endpoints:
  - [ ] Auth (register, login)
  - [ ] Jobs (create, list, update)
  - [ ] Prep packs (generate)
  - [ ] Coach (chat, suggestions)
  - [ ] Analytics (pipeline stats)
- [ ] Document any bugs
- [ ] Fix critical issues

---

## 📱 Phase 2: Mobile App (Week 2-4)

### Choose Your Path:

**Option A: Flutter (Recommended for MVP)**

#### Week 2: Setup
- [ ] Install Flutter SDK (flutter.dev)
- [ ] Create new Flutter project:
  ```bash
  flutter create career_operator
  cd career_operator
  ```
- [ ] Add dependencies (pubspec.yaml):
  ```yaml
  dependencies:
    flutter:
      sdk: flutter
    http: ^1.1.0
    shared_preferences: ^2.2.2
    provider: ^6.1.1
    fl_chart: ^0.66.0
  ```
- [ ] Run on simulator: `flutter run`

#### Week 3: Core Features
- [ ] Build screens:
  - [ ] Onboarding (role selection, salary, location)
  - [ ] Login/Register
  - [ ] Job list (with scores)
  - [ ] Job detail
  - [ ] Pipeline (Kanban board)
  - [ ] Add job form
- [ ] Connect to API:
  ```dart
  class ApiService {
    static const baseUrl = 'https://your-app.railway.app/api';

    Future<List<Job>> getJobs(String token) async {
      final response = await http.get(
        Uri.parse('$baseUrl/jobs'),
        headers: {'Authorization': 'Bearer $token'},
      );
      // ... parse response
    }
  }
  ```
- [ ] Implement authentication flow
- [ ] Save JWT token locally

#### Week 4: Polish & Submit
- [ ] Add dark mode
- [ ] Add animations
- [ ] Test on real devices (iOS + Android)
- [ ] Generate app icons (1024x1024 for App Store)
- [ ] Take screenshots (all required sizes)
- [ ] Build release versions:
  ```bash
  flutter build ipa  # iOS
  flutter build appbundle  # Android
  ```

**Option B: Native iOS (Swift)**

#### Week 2-3: Build App
- [ ] Open Xcode, create new project
- [ ] Set up SwiftUI views
- [ ] Implement networking layer
- [ ] Build UI components
- [ ] Connect to API

#### Week 4: Polish & Submit
- [ ] Test on devices
- [ ] Generate assets
- [ ] Build archive
- [ ] Submit to App Store

---

## 🎨 Phase 3: App Store Assets (Week 5)

### iOS App Store

#### Required Assets:
- [ ] App Icon (1024x1024px, no alpha)
- [ ] Screenshots (6.5", 5.5" iPhone):
  1. Hero shot (job scoring UI)
  2. Prep pack viewer
  3. Pipeline/CRM board
  4. Analytics dashboard
  5. Before/After testimonial
- [ ] Preview video (30 sec max):
  - Problem (0-5s)
  - Solution demo (5-25s)
  - CTA (25-30s)

#### App Store Listing:
```
App Name: Career Operator: AI Job Tracker
Subtitle: Land Your Dream Tech Job Faster

Description: (First 3 lines critical!)
Stop applying to hundreds of jobs. Career Operator uses AI to
score every opportunity, generate interview prep packs, and
manage your pipeline like a pro.

✓ AI Job Scoring (0-100)
✓ Interview Prep Packs
✓ Application CRM
✓ Salary Intel
✓ Offline-First

Keywords: job search,career,interview prep,resume,tech jobs,ai
Category: Business > Productivity
Price: $4.99 USD
```

#### Privacy Policy & Terms:
- [ ] Create simple privacy policy (use template from app-privacy-policy-generator.com)
- [ ] Host on GitHub Pages or your website
- [ ] Add links to App Store Connect

### Google Play Store

#### Required Assets:
- [ ] App Icon (512x512px)
- [ ] Feature Graphic (1024x500px)
- [ ] Screenshots (Phone + Tablet):
  - Minimum 2, maximum 8
  - Same content as iOS
- [ ] Short description (80 chars)
- [ ] Full description (4000 chars max)

#### Play Store Listing:
```
Title: Career Operator - AI Job Search

Short: AI-powered job search. Score jobs, prep for interviews, land your dream role.

Full: (Copy from iOS, adjust for Android audience)

Category: Business
Content Rating: Everyone
Price: $4.99 USD
```

---

## 🚢 Phase 4: Submission (Week 6)

### iOS Submission

#### Day 1: Apple Developer Setup
- [ ] Join Apple Developer Program ($99/year)
- [ ] Create App ID in developer.apple.com
- [ ] Generate certificates & provisioning profiles
- [ ] Add to Xcode

#### Day 2: App Store Connect
- [ ] Create new app in App Store Connect
- [ ] Upload build via Xcode or Transporter
- [ ] Fill out all metadata
- [ ] Upload screenshots, preview video
- [ ] Add privacy policy URL
- [ ] Set pricing ($4.99 in all territories)

#### Day 3: Submit for Review
- [ ] Answer review questions honestly
- [ ] Add demo account (if needed)
- [ ] Submit for review
- [ ] Wait 1-3 days for approval

### Android Submission

#### Day 1: Google Play Console Setup
- [ ] Create Google Play Developer account ($25 one-time)
- [ ] Create new app
- [ ] Fill out store listing

#### Day 2: Upload Build
- [ ] Generate signed App Bundle
- [ ] Upload to Production track
- [ ] Fill out content rating questionnaire
- [ ] Set pricing ($4.99)

#### Day 3: Submit for Review
- [ ] Submit for review
- [ ] Wait 1-7 days for approval

---

## 📣 Phase 5: Launch Marketing (Week 7)

### Pre-Launch (3 days before)

#### Social Media Hype
- [ ] Post on Twitter:
  ```
  Launching Career Operator on iOS/Android in 3 days! 🚀

  Stop applying to 100 jobs. Let AI find the RIGHT ones.

  $4.99 one-time. No subscription BS.

  [Attach app preview video]
  ```
- [ ] Post on LinkedIn (professional tone)
- [ ] Email list (if you have one)

#### Influencer Outreach
- [ ] DM 10 tech YouTubers/Twitter accounts
- [ ] Offer promo codes (100 codes available)
- [ ] Ask for honest review

### Launch Day

#### 8 AM: Go Live
- [ ] App should be live on App Store
- [ ] Final checks (downloads work, IAP works)

#### 9 AM: Announcements
- [ ] Post on Product Hunt:
  ```
  Title: Career Operator - AI Job Search for $4.99
  Tagline: Stop job searching. Let AI run your $500K career.
  Description: [Explain problem, your journey, invite feedback]
  ```
- [ ] Tweet thread (10+ tweets):
  1. The problem (applying to 100 jobs)
  2. Why I built this
  3. How it works (AI scoring, prep packs)
  4. Demo video
  5. Testimonials (if any)
  6. Launch offer (40% off first week)
  7. Link to App Store
- [ ] LinkedIn post (cross-post from Twitter)

#### Throughout Day:
- [ ] Respond to EVERY comment/mention
- [ ] Share user reviews as they come in
- [ ] Post updates (50 downloads! 100 downloads!)

### Week 1: Push Hard

#### Daily Tasks:
- [ ] Post content on Twitter (tips, screenshots, user wins)
- [ ] Respond to all reviews (5-star: thank, <5-star: fix issue)
- [ ] Reddit posts (1 per day):
  - r/cscareerquestions
  - r/productmanagement
  - r/datascience
  - r/ExperiencedDevs
- [ ] Update App Store description based on feedback

#### Metrics to Track:
- [ ] Downloads (target: 1,000 in Week 1)
- [ ] Conversion rate (target: 30%+ free to paid)
- [ ] Reviews (target: 50+ with 4.5+ avg)
- [ ] Revenue (target: $1,000+)

---

## 💰 Phase 6: Monetization Optimization (Week 8+)

### A/B Test Pricing

#### Week 8: Test $2.99
- [ ] Change price to $2.99 for 1 week
- [ ] Track: downloads, conversion, revenue
- [ ] Compare to $4.99 baseline

#### Week 9: Test $6.99
- [ ] Change price to $6.99
- [ ] Track metrics
- [ ] Find optimal price point

### Add In-App Purchases

#### Prep Pack Credits
- [ ] Add IAP: "5 Extra Prep Packs" for $0.99
- [ ] Show when user hits limit
- [ ] Track purchase rate

#### AI Career Coach Subscription
- [ ] Add IAP: "AI Career Coach" for $2.99/month
- [ ] Paywall after 1 free message
- [ ] Track LTV (Lifetime Value)

### Optimize ASO (App Store Optimization)

#### Every 2 Weeks:
- [ ] Update screenshots (test new captions)
- [ ] A/B test app icon (if using paid tool)
- [ ] Try new keywords
- [ ] Monitor ranking for "job search"

---

## 📈 Success Metrics

### Month 1 Goals:
- ✅ 10,000 downloads
- ✅ 30% conversion (3,000 paid users)
- ✅ $10,000 revenue (after Apple's cut: $7,000)
- ✅ 4.5+ star rating
- ✅ 100+ reviews

### Month 3 Goals:
- ✅ 50,000 total downloads
- ✅ 40% conversion rate
- ✅ $70,000 cumulative revenue
- ✅ 4.7+ star rating
- ✅ #20 in Business category

### Month 6 Goals:
- ✅ 100,000 total downloads
- ✅ $140,000 cumulative revenue
- ✅ 4.8+ star rating
- ✅ #5 in Business category
- ✅ Featured by App Store (if lucky)

### Year 1 Goals:
- ✅ 250,000 downloads
- ✅ $350,000 revenue
- ✅ Quit day job territory 🎉

---

## 🐛 Common Issues & Fixes

### App Rejected by Apple
**Reason**: "App is too simple"
**Fix**: Add more features (resume builder, salary comparison)

**Reason**: "In-App Purchase not working"
**Fix**: Test StoreKit in sandbox mode first

**Reason**: "Privacy policy missing"
**Fix**: Add clear privacy policy URL

### Low Conversion Rate (<20%)
**Fix**:
- Improve onboarding (show value in 30 seconds)
- Add video tutorial
- Reduce friction (don't require resume upload)
- Offer 3-day free trial

### Users Complaining About Price
**Response**:
"Career Operator costs less than a coffee but can help you land a $50K raise.
That's a 10,000x ROI. Compare to career coaches ($200+/hour) or
competitors like Huntr ($40/month). We think $4.99 is fair."

### High Churn (Users Delete App)
**Fix**:
- Send push notification: "You have 3 jobs expiring soon!"
- Weekly digest email
- Add more value (content, tips, insights)

---

## 🎯 Post-Launch Roadmap

### Version 1.1 (Month 2)
- [ ] Safari extension (auto-capture jobs)
- [ ] Resume builder
- [ ] Salary comparison tool

### Version 1.2 (Month 3)
- [ ] AI Career Coach (IAP)
- [ ] Network mapping
- [ ] Interview scheduling

### Version 2.0 (Month 6)
- [ ] Company reviews integration
- [ ] Referral program
- [ ] Team accounts (for bootcamps)

---

## ✅ Final Pre-Launch Checklist

**One day before launch:**
- [ ] Backend API is live and tested
- [ ] Mobile app builds successfully
- [ ] All features work on real devices
- [ ] Screenshots look professional
- [ ] App Store listing is complete
- [ ] Privacy policy is live
- [ ] Payment/IAP works in sandbox
- [ ] You have promo codes ready
- [ ] Social media posts are drafted
- [ ] You're EXCITED! 🚀

**You're ready to ship!**

Remember:
- Version 1.0 doesn't need to be perfect
- Ship fast, iterate based on reviews
- Focus on ASO (keywords, screenshots, reviews)
- Engage with EVERY user
- Your first 100 users are gold - treat them well

**Let's get you to $350K in Year 1! 💰**
