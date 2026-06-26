This package is prepared for GitHub upload and APK build with GitHub Actions.

Files:
- main.py: your app, with runtime pip-install removed for Android packaging.
- buildozer.spec: initial Buildozer config.
- .github/workflows/build-apk.yml: GitHub Actions workflow to build a debug APK.

Notes:
- Upload the project contents to a GitHub repository.
- If your default branch is not `main`, update `.github/workflows/build-apk.yml`.
- Storage paths in the app may still need Android-specific fixes after the first build/run test.
