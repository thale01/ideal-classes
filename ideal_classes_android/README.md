# 📱 Ideal Classes Android App - Build Instructions

I have created the complete source code for your professional Android WebView app in the folder `ideal_classes_android`. 

### Key Features Implemented:
- **Auto-Login**: Configured Django sessions and WebView cookies to persist for 2 weeks.
- **Splash Screen**: Branded splash screen using your class logo.
- **Offline Handling**: "No Internet" screen with a retry button.
- **Performance**: Hardware acceleration and DOM storage enabled.
- **Navigation**: Support for back button history and external link handling.

---

### 🚀 How to Build the APK
Since a "Signed APK" requires the Android SDK and a private keystore (security best practice), you need to perform the final build step in Android Studio:

1.  **Open Project**:
    - Launch Android Studio.
    - Click **Open** and select the folder: `ideal_classes_android` (inside your project directory).

2.  **Generate Signed Bundle / APK**:
    - Go to **Build** > **Generate Signed Bundle / APK...**
    - Select **APK** and click **Next**.
    - Click **Create new...** for the Key store path (if you don't have one).
    - Fill in the password and alias info (remember these!).
    - Select **release** build variant.
    - Click **Finish**.

3.  **Install**:
    - The generated APK will be in `app/release/`.
    - Copy it to your phone and install it!

---

### ✅ Django Settings Updated
I have already updated your `ideal_class/settings.py` with:
- `SESSION_COOKIE_AGE = 1209600` (2 weeks)
- `SESSION_EXPIRE_AT_BROWSER_CLOSE = False`
- `SESSION_SAVE_EVERY_REQUEST = True`

This ensures that once a user logs in via the app, they stay logged in even if they close and restart the app.
