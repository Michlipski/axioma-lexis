# Axioma Lexis Android ProGuard / R8 Rules
-keepattributes JavascriptInterface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

-keep class com.axioma.lexis.** { *; }
-dontwarn com.axioma.lexis.**
