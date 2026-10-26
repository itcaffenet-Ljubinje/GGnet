using System.Runtime.InteropServices;

namespace GgnetScan;

/// <summary>Adds a signing catalog to this Windows, as a driver install does (CryptCATAdminAddCatalog).</summary>
public static class Catalogs
{
    private const string CatRootGuid = "{F750E6C3-38EE-11D1-85E5-00C04FC295EE}";

    /// <summary>Puts the catalog in X:\Windows\System32\CatRoot\{F750...}; null when done, else why not.</summary>
    public static string? CopyToCatRoot(string path)
    {
        try
        {
            var dir = Path.Combine(Environment.SystemDirectory, "CatRoot", CatRootGuid);
            Directory.CreateDirectory(dir);
            File.Copy(path, Path.Combine(dir, Path.GetFileName(path)), true);
            return null;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            return $"copy to CatRoot failed: {e.Message}";
        }
    }

    /// <summary>Null when added, else why not.</summary>
    public static string? Add(string path)
    {
        if (!File.Exists(path))
            return "not found";
        if (!CryptCATAdminAcquireContext(out var admin, IntPtr.Zero, 0))
            return $"error {Marshal.GetLastWin32Error()}";
        try
        {
            var info = CryptCATAdminAddCatalog(admin, path, Path.GetFileName(path), 0);
            if (info == IntPtr.Zero)
                return $"error {Marshal.GetLastWin32Error()}";
            CryptCATAdminReleaseCatalogContext(admin, info, 0);
            return null;
        }
        finally
        {
            CryptCATAdminReleaseContext(admin, 0);
        }
    }

    [DllImport("wintrust.dll", SetLastError = true)]
    private static extern bool CryptCATAdminAcquireContext(out IntPtr admin, IntPtr subsystem, int flags);

    [DllImport("wintrust.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr CryptCATAdminAddCatalog(IntPtr admin, string catalogFile, string? selectBaseName,
        int flags);

    [DllImport("wintrust.dll", SetLastError = true)]
    private static extern bool CryptCATAdminReleaseCatalogContext(IntPtr admin, IntPtr info, int flags);

    [DllImport("wintrust.dll", SetLastError = true)]
    private static extern bool CryptCATAdminReleaseContext(IntPtr admin, int flags);
}
