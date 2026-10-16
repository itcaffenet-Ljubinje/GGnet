namespace GgnetAgent;

/// <summary>
/// Boot Mode: the PC runs Windows from the server, so its own disks must not
/// be used. Left online, a game library (Steam, Warzone) lands on the local
/// NVMe instead of the game disk, only on that PC and out of the server's
/// reach. ggRock tells centers to pull the drives; the agent takes them offline.
/// </summary>
public interface ILocalDisks
{
    /// <summary>Takes the PC's local disks offline; returns a line per disk it took offline.</summary>
    Task<IReadOnlyList<string>> HideAsync(CancellationToken ct);
}

/// <summary>ILocalDisks with Get-Disk / Set-Disk (Storage module, in Windows 11).</summary>
public sealed class WindowsLocalDisks(IScriptRunner runner) : ILocalDisks
{
    /// <summary>
    /// Internal buses only: iSCSI (the server's disks), USB (a player's stick)
    /// and virtual disks stay as they are, and so does whatever Windows boots
    /// from or keeps its boot files on, whatever its bus. Offline is stored in
    /// this Windows (the writeback), not on the disk, so the PC's own Windows
    /// still sees its disk when it boots locally.
    /// </summary>
    internal const string Script = """
        $local = @('NVMe', 'SATA', 'ATA', 'SAS', 'RAID', 'SCSI', 'SD', 'MMC')
        Get-Disk | Where-Object {
            -not $_.IsOffline -and -not $_.IsBoot -and -not $_.IsSystem -and $local -contains [string]$_.BusType
        } | ForEach-Object {
            Set-Disk -Number $_.Number -IsOffline $true
            "$($_.Number): $($_.FriendlyName) ($($_.BusType))"
        }
        """;

    public async Task<IReadOnlyList<string>> HideAsync(CancellationToken ct) =>
        (await runner.RunAsync(Script, ct))
            .Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
}
