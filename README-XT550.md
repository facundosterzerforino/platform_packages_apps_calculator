# Calculadora (AOSP Calculator 2.3.6, branch `xt550-libre`)

This is the stock Android 2.3.6 Calculator (`android-2.3.6_r1`, commit
`5c85e48`, Apache 2.0), built outside AOSP for an Android 2.3 phone (Motorola
XT550) that runs only software built from source.

## Changes

- Removed the prebuilt `arity-2.1.2.jar`. The arity math engine is compiled
  from its author's source: [preda/arithmetic](https://github.com/preda/arithmetic)
  at commit `7327763` (version 2.1.6, Apache 2.0). `UnitTest.java` is left out.
- `build.py`: offline build with aapt, javac, D8, zipalign and apksigner, plus:
  - `uses-sdk` min 9 / target 10, so the app doesn't run in compatibility mode;
  - package renamed to `org.librecalculadora`, so it installs as a normal app;
  - fixed zip timestamp, so the APK hash is reproducible.
- App code is unchanged.

## Review

- No permissions, no network, no file or command access.
- arity only parses and evaluates math expressions. Its only `Runtime` use is in
  `UnitTest`, which is not built.

## Build

    git clone https://github.com/preda/arithmetic arity-src   # commit 7327763
    python build.py --jdk JDK --build-tools BUILD_TOOLS --android-jar android-17/android.jar \
      --arity-src arity-src --keystore /outside/key.jks --storepass-file /outside/pass

`android.jar` comes from Google's `android-17_r03.zip` (SHA-1
`dbe14101c06e6cdb34e300393e64e64f8c92168a`) and is used at compile time only.

## Tested on the XT550 (Android 2.3.6)

- `12 × 3 + 4 = 40` and `7 ÷ 2 = 3.5`.
- Spanish labels ("Calculadora", "BORRAR").
- RAM: 2.7 MB PSS while open (median of 3 cold starts).
