# Career Operator - Flutter Mobile App

This is the Flutter mobile app for Career Operator.

## Setup

### Prerequisites
- Flutter SDK 3.0+
- Dart SDK
- Xcode (for iOS)
- Android Studio (for Android)

### Installation

```bash
# Navigate to mobile directory
cd mobile

# Get dependencies
flutter pub get

# Run the app
flutter run
```

### Configuration

1. Update the API URL in `lib/services/api_client.dart`:
```dart
static const String baseUrl = 'https://your-railway-app.railway.app';
```

2. For production, configure:
- App icons
- Splash screen
- App signing keys

## Project Structure

```
lib/
├── main.dart              # App entry point
├── theme.dart             # App theming
├── models/                # Data models
│   ├── user.dart
│   ├── job.dart
│   └── chat_message.dart
├── services/              # API & services
│   └── api_client.dart
├── providers/             # State management
│   ├── auth_provider.dart
│   ├── jobs_provider.dart
│   └── coach_provider.dart
├── screens/               # UI screens
│   ├── auth/
│   ├── home/
│   ├── jobs/
│   ├── coach/
│   └── settings/
└── widgets/               # Reusable widgets
    ├── job_card.dart
    └── stat_card.dart
```

## Features

- **Authentication**: Login, register, JWT tokens
- **Job Tracking**: Add, view, update job applications
- **AI Scoring**: View match scores for jobs
- **Prep Packs**: Generate AI-powered interview prep
- **AI Coach**: Chat with career coach
- **Pipeline**: Track application status

## Building for Release

### iOS
```bash
flutter build ios --release
```

### Android
```bash
flutter build apk --release
# or
flutter build appbundle --release
```

## App Store Submission

See the main project's `SHIP_IT.md` for complete launch guide.
