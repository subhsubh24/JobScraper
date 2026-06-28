# Permissions Audit — Career Operator (mobile)

> Verifies the app requests **only** permissions it actually uses (Apple 5.1.2 / Google
> "request only necessary permissions"). Source: `mobile/app.json` (plugins + iOS/Android
> config) + `mobile/app.config.ts`. Re-verify at the readiness gate and whenever a native
> capability is added.

## Result: the app requests ZERO sensitive runtime permissions.

Career Operator is a network-only client (auth + job/pipeline data + AI features over
HTTPS). It does **not** access the camera, microphone, photo library, location, contacts,
calendar, Bluetooth, motion, or any other privacy-sensitive capability — so there are no
`NS*UsageDescription` strings to justify on iOS and no dangerous `<uses-permission>` entries
to declare on Android.

## Declared plugins and their permission footprint

| Plugin (`app.json`) | Native permission? | Notes |
|---|---|---|
| `expo-router` | None | Navigation only |
| `expo-secure-store` | None (no runtime prompt) | Stores the auth token in the iOS Keychain / Android Keystore — no user-facing permission |
| `expo-splash-screen` | None | Launch splash only |

## iOS — `NS*UsageDescription` strings
**None required.** No `infoPlist` privacy-usage keys are set, because no API that requires
one is used. (If a future feature adds camera/photos/location/etc., add the matching
`NS*UsageDescription` with an honest, specific string at that time — never pre-declare a
permission the app doesn't use; an unused permission with a vague string is a rejection
risk.)

## Android — `<uses-permission>`
**No dangerous permissions declared.** Expo includes `INTERNET` (normal, auto-granted, no
prompt) which the app legitimately needs for all API calls. No `ACCESS_FINE_LOCATION`,
`CAMERA`, `READ_CONTACTS`, `READ_MEDIA_*`, `RECORD_AUDIO`, etc.

## Standing rule
Adding a native capability ⇒ (1) add the minimal permission, (2) add an honest usage string,
(3) update this file + `APP_PRIVACY_LABELS.md` + the Data Safety form, (4) confirm it clears
review. Requesting a permission the app doesn't exercise is a defect, not a convenience.
