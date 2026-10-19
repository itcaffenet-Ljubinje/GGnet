using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;

namespace GgnetAgent;

/// <summary>UEFI variables of this PC (NVRAM), read and written from Windows.</summary>
public interface IUefiVariables
{
    /// <summary>False on a BIOS (legacy) boot: there are no UEFI variables.</summary>
    bool IsUefi { get; }

    /// <summary>The variable's data, or null when it does not exist.</summary>
    byte[]? Read(string name, Guid vendor);

    /// <summary>Writes a non-volatile variable (boot and runtime access).</summary>
    void Write(string name, Guid vendor, byte[] data);
}

/// <summary>
/// Secure Boot key enrollment without a USB stick, as `mokutil --import` does
/// on Linux: shim (the Microsoft-signed first stage the PCs boot) trusts the
/// ggNet key once it is in the PC's MOK list. The agent asks for it by writing
/// MokNew (the key) and MokAuth (a hash of the key and a password); at the
/// next boot shim opens MokManager, where someone at the PC confirms
/// "Enroll MOK" and types the password. Only that confirmation can add a key:
/// it is what keeps Secure Boot secure.
/// </summary>
public static class Mok
{
    /// <summary>shim's vendor GUID for its variables (MokNew, MokAuth, MokListRT).</summary>
    public static readonly Guid ShimLock = new("605dab50-e046-4300-abb6-3dd810dd8b23");

    /// <summary>EFI_CERT_X509_GUID: a signature list entry holding a DER certificate.</summary>
    public static readonly Guid CertX509 = new("a5c059a1-94e4-4aa7-87b5-ab155c2bf072");

    private const int ListHeader = 28;   // SignatureType (16), ListSize, HeaderSize, SignatureSize
    private const int OwnerSize = 16;

    /// <summary>One EFI_SIGNATURE_LIST with the certificate, owned by shim, as mokutil writes MokNew.</summary>
    public static byte[] SignatureList(byte[] certificate)
    {
        var list = new byte[ListHeader + OwnerSize + certificate.Length];
        CertX509.ToByteArray().CopyTo(list, 0);            // GUIDs are stored as EFI lays them out
        BitConverter.TryWriteBytes(list.AsSpan(16), (uint)list.Length);
        BitConverter.TryWriteBytes(list.AsSpan(20), 0u);   // no signature header
        BitConverter.TryWriteBytes(list.AsSpan(24), (uint)(OwnerSize + certificate.Length));
        ShimLock.ToByteArray().CopyTo(list, ListHeader);
        certificate.CopyTo(list, ListHeader + OwnerSize);
        return list;
    }

    /// <summary>MokAuth: SHA-256 of MokNew and the password in UCS-2, what MokManager checks.</summary>
    public static byte[] Auth(byte[] mokNew, string password)
    {
        using var sha = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        sha.AppendData(mokNew);
        sha.AppendData(Encoding.Unicode.GetBytes(password));
        return sha.GetHashAndReset();
    }

    /// <summary>Whether a set of signature lists (e.g. MokListRT) holds this X.509 certificate.</summary>
    public static bool Contains(byte[]? lists, byte[] certificate)
    {
        if (lists is null) return false;
        var x509 = CertX509.ToByteArray();
        int at = 0;
        while (at + ListHeader <= lists.Length)
        {
            var type = lists.AsSpan(at, 16);
            uint listSize = BitConverter.ToUInt32(lists, at + 16);
            uint headerSize = BitConverter.ToUInt32(lists, at + 20);
            uint sigSize = BitConverter.ToUInt32(lists, at + 24);
            if (listSize < ListHeader || at + listSize > lists.Length || sigSize < OwnerSize) return false;
            if (type.SequenceEqual(x509))
            {
                long first = at + ListHeader + headerSize;
                for (long sig = first; sig + sigSize <= at + listSize; sig += sigSize)
                {
                    var data = lists.AsSpan((int)sig + OwnerSize, (int)sigSize - OwnerSize);
                    if (data.SequenceEqual(certificate)) return true;
                }
            }
            at += (int)listSize;
        }
        return false;
    }
}

/// <summary>What the agent did about the ggNet Secure Boot key; sent to the server.</summary>
public static class MokState
{
    public const string Enrolled = "enrolled";    // the PC trusts the key (shim's MokListRT has it)
    public const string Requested = "requested";  // MokNew is set: confirm in MokManager at the next boot
    public const string Failed = "failed";
}

public sealed class MokEnrollment(IUefiVariables variables)
{
    /// <summary>
    /// Asks for the certificate unless the PC already trusts it or the same
    /// request is pending. Null on a BIOS boot (no shim, no Secure Boot).
    /// </summary>
    public string? Ensure(byte[] certificate, string password)
    {
        if (!variables.IsUefi) return null;
        // shim mirrors the MOK list into MokListRT at every boot it runs.
        if (Mok.Contains(variables.Read("MokListRT", Mok.ShimLock), certificate)) return MokState.Enrolled;
        var request = Mok.SignatureList(certificate);
        var pending = variables.Read("MokNew", Mok.ShimLock);
        var auth = Mok.Auth(request, password);
        if (pending is not null && pending.AsSpan().SequenceEqual(request)
            && variables.Read("MokAuth", Mok.ShimLock) is { } oldAuth && oldAuth.AsSpan().SequenceEqual(auth))
        {
            return MokState.Requested;
        }
        variables.Write("MokNew", Mok.ShimLock, request);
        variables.Write("MokAuth", Mok.ShimLock, auth);
        return MokState.Requested;
    }
}

/// <summary>IUefiVariables through the Win32 firmware environment API (needs SeSystemEnvironmentPrivilege).</summary>
public sealed partial class WindowsUefiVariables : IUefiVariables
{
    private const uint NonVolatile = 0x1, BootServiceAccess = 0x2, RuntimeAccess = 0x4;
    private const int ErrorEnvvarNotFound = 203;
    private const int FirmwareTypeUefi = 2;
    private bool _privileged;

    public bool IsUefi => GetFirmwareType(out int type) && type == FirmwareTypeUefi;

    public byte[]? Read(string name, Guid vendor)
    {
        EnablePrivilege();
        var buffer = new byte[64 * 1024];
        uint size = GetFirmwareEnvironmentVariableExW(name, vendor.ToString("B"), buffer, (uint)buffer.Length, out _);
        if (size == 0)
        {
            int error = Marshal.GetLastPInvokeError();
            if (error == ErrorEnvvarNotFound) return null;
            throw new Win32Exception(error, $"Reading UEFI variable {name}");
        }
        return buffer[..(int)size];
    }

    public void Write(string name, Guid vendor, byte[] data)
    {
        EnablePrivilege();
        if (!SetFirmwareEnvironmentVariableExW(name, vendor.ToString("B"), data, (uint)data.Length,
                NonVolatile | BootServiceAccess | RuntimeAccess))
        {
            throw new Win32Exception(Marshal.GetLastPInvokeError(), $"Writing UEFI variable {name}");
        }
    }

    /// <summary>The service runs as LocalSystem, which holds the privilege but has it disabled.</summary>
    private void EnablePrivilege()
    {
        if (_privileged) return;
        if (!OpenProcessToken(GetCurrentProcess(), 0x0020 | 0x0008, out var token))   // ADJUST_PRIVILEGES | QUERY
            throw new Win32Exception(Marshal.GetLastPInvokeError(), "OpenProcessToken");
        try
        {
            if (!LookupPrivilegeValueW(null, "SeSystemEnvironmentPrivilege", out long luid))
                throw new Win32Exception(Marshal.GetLastPInvokeError(), "LookupPrivilegeValue");
            var state = new TokenPrivileges { Count = 1, Luid = luid, Attributes = 0x2 };   // SE_PRIVILEGE_ENABLED
            if (!AdjustTokenPrivileges(token, false, ref state, 0, IntPtr.Zero, IntPtr.Zero)
                || Marshal.GetLastPInvokeError() != 0)
                throw new Win32Exception(Marshal.GetLastPInvokeError(), "AdjustTokenPrivileges");
            _privileged = true;
        }
        finally
        {
            CloseHandle(token);
        }
    }

    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    private struct TokenPrivileges
    {
        public uint Count;
        public long Luid;
        public uint Attributes;
    }

    [LibraryImport("kernel32.dll", SetLastError = true, StringMarshalling = StringMarshalling.Utf16)]
    private static partial uint GetFirmwareEnvironmentVariableExW(string name, string guid, byte[] buffer,
        uint size, out uint attributes);

    [LibraryImport("kernel32.dll", SetLastError = true, StringMarshalling = StringMarshalling.Utf16)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool SetFirmwareEnvironmentVariableExW(string name, string guid, byte[] value,
        uint size, uint attributes);

    [LibraryImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool GetFirmwareType(out int type);

    [LibraryImport("kernel32.dll")]
    private static partial IntPtr GetCurrentProcess();

    [LibraryImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool CloseHandle(IntPtr handle);

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);

    [LibraryImport("advapi32.dll", SetLastError = true, StringMarshalling = StringMarshalling.Utf16)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool LookupPrivilegeValueW(string? system, string name, out long luid);

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool AdjustTokenPrivileges(IntPtr token, [MarshalAs(UnmanagedType.Bool)] bool disableAll,
        ref TokenPrivileges newState, uint length, IntPtr previous, IntPtr returnLength);
}
