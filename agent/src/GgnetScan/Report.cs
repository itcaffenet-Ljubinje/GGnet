using System.Text.Json;
using System.Text.Json.Serialization;

namespace GgnetScan;

/// <summary>
/// ggnet-scan.json, written by the server for this PC and injected next to
/// the scanner by wimboot: where to send the report, the PC's boot MAC (as
/// iPXE saw it) and the network card drivers to load first.
/// </summary>
public sealed record ScanConfig(string Server, string Mac, IReadOnlyList<string>? Drivers = null)
{
    public static ScanConfig Parse(string json)
    {
        ScanConfig? config;
        try
        {
            config = JsonSerializer.Deserialize(json, ScanJson.Default.ScanConfig);
        }
        catch (JsonException e)
        {
            throw new FormatException($"ggnet-scan.json is not valid JSON: {e.Message}", e);
        }
        if (config is null || !Uri.TryCreate(config.Server, UriKind.Absolute, out var uri)
            || (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps))
            throw new FormatException("ggnet-scan.json has no http(s) server URL");
        if (string.IsNullOrWhiteSpace(config.Mac))
            throw new FormatException("ggnet-scan.json has no MAC address");
        // Only plain file names: they are loaded from the scanner's own folder.
        if (config.Drivers?.Any(d => d.Contains('/') || d.Contains('\\') || d.Contains("..")
                                     || !d.EndsWith(".inf", StringComparison.OrdinalIgnoreCase)) == true)
            throw new FormatException("ggnet-scan.json names a driver that is not an .inf file name");
        return config;
    }

    public Uri ReportUrl => new(new Uri(Server.TrimEnd('/') + "/"), "api/v1/boot/scan");
}

/// <summary>One PCI device of the PC, as Windows (WinPE) enumerates it.</summary>
public sealed record ScanDevice(
    string InstanceId,
    IReadOnlyList<string> HardwareIds,
    IReadOnlyList<string> CompatibleIds,
    string? ClassGuid,
    string? Description,
    string? Service);

/// <summary>A network adapter WinPE brought up: its MAC and whether it got an address.</summary>
public sealed record ScanAdapter(string Mac, string Description, bool HasAddress);

/// <summary>What the scanner sends to POST /api/v1/boot/scan.</summary>
public sealed record ScanReport(
    string Mac, string ScannerVersion, IReadOnlyList<ScanDevice> Devices, IReadOnlyList<ScanAdapter> Adapters);

/// <summary>The server's answer: what it will do with this PC.</summary>
public sealed record ScanAnswer(string Message);

[JsonSourceGenerationOptions(PropertyNamingPolicy = JsonKnownNamingPolicy.SnakeCaseLower,
    PropertyNameCaseInsensitive = true)]
[JsonSerializable(typeof(ScanConfig))]
[JsonSerializable(typeof(ScanReport))]
[JsonSerializable(typeof(ScanAnswer))]
internal sealed partial class ScanJson : JsonSerializerContext;
