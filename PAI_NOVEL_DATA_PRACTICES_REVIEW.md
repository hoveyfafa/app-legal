# PaiNovel legal and data-handling audit

Audit date: 2026-10-22. Legal documents are effective 2026-10-13. This describes repository behavior, not unverified production configuration.

## Findings and code evidence

- **App identity:** `PaiNovel` is the Android label, iOS display/name, and Flutter title (`apps/mobile/android/app/src/main/AndroidManifest.xml`, `apps/mobile/ios/Runner/Info.plist`, `apps/mobile/lib/main.dart`). Android application ID is `com.paiguo.novelread` (`apps/mobile/android/app/build.gradle.kts`).
- **Accounts:** no auth dependency, sign-in route, credential model, token storage, or account endpoint exists. “Paiguo Reader” is fixed display text in `apps/mobile/lib/main.dart`; the API uses a singleton `/readers/me` convention with no authentication in `apps/api/src/app.controller.ts`.
- **Server/network:** mobile uses deterministic mocks unless compile-time `API_BASE_URL` is non-empty (`apps/mobile/lib/core/config/app_environment.dart`, `apps/mobile/lib/main.dart`). When enabled, only the discovery catalog performs an HTTP GET to `/catalog/home` (`apps/mobile/lib/features/discover/data/http_discover_repository.dart`). The Nest API listens locally by default, enables permissive CORS, and stores all state in memory (`apps/api/src/main.ts`, `apps/api/src/app.service.ts`). Production host, TLS, proxy/access logs, hosting region, and subprocessors are not present in code.
- **Permissions:** the Android main manifest has no `uses-permission`; debug/profile manifests add `INTERNET` for Flutter development tooling. iOS has no sensitive-data usage description in `Info.plist`. The main manifest contains only a package-visibility query for activities that process text; this is not permission to read user text.
- **File upload:** the mobile app has no picker/upload implementation. The Vue operations console accepts cover images, `.txt`/`.md`, and a ZIP containing `metadata.json`, `novel.md`, and `cover.png` in `apps/web/src/App.vue`. It uses browser file APIs and can place a cover Data URL (up to 5,000,000 characters per API DTO) and chapters into novel create/update payloads (`apps/api/src/novels/dto/*.ts`). The API has no object-storage SDK and only retains records in process memory.
- **Ads:** the reader text mentions “keep reading with an ad,” but `pubspec.yaml`, native manifests, and application code include no ad SDK or ad request. This is planned/interface copy, not an available advertising capability.
- **Analytics and crash reporting:** no Firebase, Google Analytics, Sentry, Crashlytics, or equivalent dependency/configuration is present in mobile, web, or API manifests.
- **Payment:** `RechargePage` displays RMB packs but calls `MockProfileRepository.addCoins`; its success text explicitly says “Mock purchase” (`apps/mobile/lib/main.dart`, `apps/mobile/lib/features/profile/data/mock_profile_repository.dart`). No billing SDK or server verification exists. Unlocks and tips only mutate local/in-memory coin balances. These are not live paid capabilities.
- **Notifications:** notification settings mutate in-memory preferences only; no push SDK, device token, or Android notification permission exists. Do not disclose push delivery as live.
- **Community data:** review and tip endpoints exist only in the in-memory API. Reviews use a fixed author and are lost on restart (`apps/api/src/app.service.ts`). The mobile app does not currently call these endpoints.
- **Retention/deletion:** the mobile profile repository and API are in-memory; no database, durable client storage, account creation, account deletion endpoint, backup policy, retention job, or production log setting exists. Bundled assets remain until app uninstall/update. Production infrastructure retention cannot be inferred.

## Official publication requirements reviewed

- Google Play requires a comprehensive privacy policy in Play Console and in the app, with developer/contact information, data access/collection/use/sharing, secure handling, retention, and deletion practices. Data safety answers must remain accurate and include SDK behavior: <https://support.google.com/googleplay/android-developer/answer/18258653>
- All published apps must complete the Data safety form, even when the accurate declaration is that no user data is collected or shared: <https://support.google.com/googleplay/android-developer/answer/10787469>
- If account creation is later enabled, Google Play requires both an in-app deletion route and an external web deletion resource, with associated data deleted except disclosed legitimate retention: <https://support.google.com/googleplay/android-developer/answer/13327111>
- Virtual currency, subscriptions, and paid digital content in a Play-distributed app generally require Google Play Billing; pricing and terms must be clear, and purchased virtual currency is restricted to the app title: <https://support.google.com/googleplay/android-developer/answer/9858738>
- Google recommends server-side verification and purchase acknowledgement/consumption for Billing integration: <https://developer.android.com/google/play/billing/integrate>

No third-party data SDK is currently integrated, so there is no SDK-specific privacy requirement to attribute beyond the platform requirements above. Re-run this audit whenever dependencies or native manifests change.

## Items requiring publisher confirmation

1. Production API host, hosting country/region, access-log provider and retention, subprocessors, TLS policy, and whether the API will actually be enabled.
2. Launch markets, governing law/dispute venue, target age group, and whether users can submit content in production.
3. Whether real coins/subscriptions, ads, analytics, crash reporting, push notifications, accounts, or file uploads will ship. Each needs a fresh code/config audit and policy/Data safety update before release.
