package com.axioma.lexis

import android.annotation.SuppressLint
import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

/**
 * Android Main Activity for Axioma Lexis G2.
 *
 * Implements a standalone fullscreen client with offline HTML5 caching,
 * native touch drag physics, hardware vibration haptics via AndroidBridge,
 * system push/local notification scheduling with deep linking, and
 * automatic fallback to bundled assets if the remote server is unreachable.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val localAssetUrl = "file:///android_asset/index.html"
    private val CHANNEL_ID = "axioma_lexis_srs"
    private val NOTIFICATION_PERMISSION_CODE = 101

    /**
     * Native Javascript Interface exposing hardware capabilities to WebView.
     */
    inner class AndroidBridge(private val context: Context) {

        @JavascriptInterface
        fun vibrate(milliseconds: Long) {
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                    vibratorManager?.defaultVibrator?.vibrate(
                        VibrationEffect.createOneShot(milliseconds, VibrationEffect.DEFAULT_AMPLITUDE)
                    )
                } else {
                    @Suppress("DEPRECATION")
                    val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        vibrator?.vibrate(
                            VibrationEffect.createOneShot(milliseconds, VibrationEffect.DEFAULT_AMPLITUDE)
                        )
                    } else {
                        @Suppress("DEPRECATION")
                        vibrator?.vibrate(milliseconds)
                    }
                }
            } catch (e: Exception) {
                // Silently ignore if permission or hardware unavailable
            }
        }

        @JavascriptInterface
        fun showToast(message: String) {
            runOnUiThread {
                Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
            }
        }

        @JavascriptInterface
        fun postNotification(title: String, message: String, delaySeconds: Int) {
            runOnUiThread {
                scheduleNativeNotification(title, message, delaySeconds, NotificationReceiver.DEFAULT_NOTIFICATION_ID)
            }
        }

        @JavascriptInterface
        fun postTestNotification(title: String, message: String, delaySeconds: Int) {
            runOnUiThread {
                scheduleNativeNotification(title, message, delaySeconds, NotificationReceiver.TEST_NOTIFICATION_ID)
            }
        }

        @JavascriptInterface
        fun requestNotificationPermission() {
            runOnUiThread {
                checkAndRequestNotificationPermission()
            }
        }

        @JavascriptInterface
        fun hasNotificationPermission(): Boolean {
            return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
            } else {
                NotificationManagerCompat.from(context).areNotificationsEnabled()
            }
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "Axioma Lexis Reminders"
            val descriptionText = "Spaced repetition due alerts and curiosity hooks"
            val importance = NotificationManager.IMPORTANCE_HIGH
            val channel = NotificationChannel(CHANNEL_ID, name, importance).apply {
                description = descriptionText
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 250, 100, 250)
                lockscreenVisibility = NotificationCompat.VISIBILITY_PUBLIC
            }
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun checkAndRequestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), NOTIFICATION_PERMISSION_CODE)
            }
        }
    }

    fun scheduleNativeNotification(
        title: String,
        message: String,
        delaySeconds: Int = 0,
        notifId: Int = NotificationReceiver.DEFAULT_NOTIFICATION_ID
    ) {
        checkAndRequestNotificationPermission()

        val alarmIntent = Intent(this, NotificationReceiver::class.java).apply {
            putExtra(NotificationReceiver.EXTRA_TITLE, title)
            putExtra(NotificationReceiver.EXTRA_MESSAGE, message)
            putExtra(NotificationReceiver.EXTRA_ID, notifId)
            putExtra(NotificationReceiver.EXTRA_ROUTE, "review")
        }

        if (delaySeconds <= 0) {
            NotificationReceiver().onReceive(this, alarmIntent)
            return
        }

        val pendingFlags = PendingIntent.FLAG_UPDATE_CURRENT or (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
        val pendingIntent = PendingIntent.getBroadcast(this, notifId, alarmIntent, pendingFlags)

        val alarmManager = getSystemService(Context.ALARM_SERVICE) as? AlarmManager
        val triggerAtMillis = System.currentTimeMillis() + (delaySeconds.toLong() * 1000L)

        val showActivityIntent = Intent(this, MainActivity::class.java).apply {
            setFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            action = Intent.ACTION_VIEW
            data = Uri.parse("lexis://review")
        }
        val showIntent = PendingIntent.getActivity(this, notifId, showActivityIntent, pendingFlags)

        try {
            if (alarmManager != null) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    val clockInfo = AlarmManager.AlarmClockInfo(triggerAtMillis, showIntent)
                    alarmManager.setAlarmClock(clockInfo, pendingIntent)
                } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent)
                } else {
                    alarmManager.setExact(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent)
                }
            }
        } catch (e: Exception) {
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    alarmManager?.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent)
                } else {
                    alarmManager?.set(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent)
                }
            } catch (e2: Exception) {
                NotificationReceiver().onReceive(this, alarmIntent)
            }
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == NOTIFICATION_PERMISSION_CODE) {
            val granted = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
            if (granted) {
                webView.evaluateJavascript("if (typeof scheduleSpacedReviewReminder === 'function') { scheduleSpacedReviewReminder(); }", null)
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        createNotificationChannel()
        checkAndRequestNotificationPermission()

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.databaseEnabled = true
            settings.cacheMode = WebSettings.LOAD_DEFAULT
            settings.useWideViewPort = true
            settings.loadWithOverviewMode = true
            settings.setSupportZoom(false)
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            settings.allowFileAccessFromFileURLs = true
            settings.allowUniversalAccessFromFileURLs = true
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            scrollBarStyle = View.SCROLLBARS_INSIDE_OVERLAY

            addJavascriptInterface(AndroidBridge(this@MainActivity), "AndroidBridge")

            webViewClient = WebViewClient()
            webChromeClient = WebChromeClient()
        }
        setContentView(webView)

        val targetUrl = resolveTargetUrl(intent)
        webView.loadUrl(targetUrl)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        val targetUrl = resolveTargetUrl(intent)
        webView.loadUrl(targetUrl)
    }

    private fun resolveTargetUrl(intent: Intent?): String {
        val data: Uri? = intent?.data
        val fragment = when (data?.host) {
            "capture" -> "#capture"
            "review" -> "#review"
            else -> ""
        }
        return "$localAssetUrl$fragment"
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
