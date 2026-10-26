using System.Text;

namespace GgnetScan;

/// <summary>INF files (UTF-16 with BOM, or ANSI).</summary>
public static class Inf
{
    /// <summary>
    /// A copy of the INF next to it (ggnet-&lt;name&gt;) with `CatalogFile=` set in
    /// [Version]; null when it cannot be written.
    /// </summary>
    public static string? WithCatalog(string path, string catalog)
    {
        try
        {
            var bytes = File.ReadAllBytes(path);
            var unicode = bytes.Length >= 2 && bytes[0] == 0xFF && bytes[1] == 0xFE;
            var text = unicode ? Encoding.Unicode.GetString(bytes, 2, bytes.Length - 2) : Encoding.Latin1.GetString(bytes);
            var copy = Path.Combine(Path.GetDirectoryName(path)!, "ggnet-" + Path.GetFileName(path));
            var body = AddCatalog(text, catalog);
            File.WriteAllBytes(copy, unicode ? [0xFF, 0xFE, .. Encoding.Unicode.GetBytes(body)] : Encoding.Latin1.GetBytes(body));
            return copy;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            return null;
        }
    }

    /// <summary>The INF text with CatalogFile=`catalog` as the first line of [Version] (an old one dropped).</summary>
    public static string AddCatalog(string text, string catalog)
    {
        var lines = text.Replace("\r\n", "\n").Split('\n').ToList();
        lines.RemoveAll(l => l.TrimStart().StartsWith("CatalogFile", StringComparison.OrdinalIgnoreCase));
        var version = lines.FindIndex(l => l.Trim().Equals("[Version]", StringComparison.OrdinalIgnoreCase));
        if (version < 0)
        {
            lines.Insert(0, "[Version]");
            version = 0;
        }
        lines.Insert(version + 1, $"CatalogFile={catalog}");
        return string.Join("\r\n", lines);
    }
}
