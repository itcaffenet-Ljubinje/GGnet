using System.Text;
using System.Text.Json;
using GgnetScan;

namespace GgnetAgent.Tests;

public class ScanTests
{
    [Fact]
    public void Reads_the_config_the_server_writes()
    {
        var config = ScanConfig.Parse("""
            {"server": "http://192.168.0.40:8088", "mac": "4c:ed:fb:67:96:6b", "drivers": ["net1ic64.inf"]}
            """);
        Assert.Equal("4c:ed:fb:67:96:6b", config.Mac);
        Assert.Equal(["net1ic64.inf"], config.Drivers);
        Assert.Equal("http://192.168.0.40:8088/api/v1/boot/scan", config.ReportUrl.ToString());
    }

    [Theory]
    [InlineData("not json")]
    [InlineData("""{"server": "ftp://x", "mac": "aa"}""")]
    [InlineData("""{"server": "http://x:8088"}""")]
    [InlineData("""{"server": "http://x", "mac": "aa", "drivers": ["..\\evil.inf"]}""")]
    [InlineData("""{"server": "http://x", "mac": "aa", "drivers": ["setup.exe"]}""")]
    public void Refuses_a_bad_config(string json) => Assert.Throws<FormatException>(() => ScanConfig.Parse(json));

    [Fact]
    public void Splits_hardware_ids_as_setupapi_returns_them()
    {
        var bytes = Encoding.Unicode.GetBytes("PCI\\VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10\0PCI\\VEN_8086&DEV_15BC\0\0");
        Assert.Equal(["PCI\\VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10", "PCI\\VEN_8086&DEV_15BC"], PciDevices.SplitMultiSz(bytes));
    }

    [Fact]
    public void The_report_uses_the_servers_names()
    {
        var report = new ScanReport("aa:bb:cc:dd:ee:ff", "0.1.0",
            [new ScanDevice("PCI\\VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10\\3&11583659&0&FE",
                ["PCI\\VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10"], [], PciDevices.NetClass, "Intel", null)],
            [new ScanAdapter("4c:ed:fb:67:96:6b", "Intel", true)]);
        var json = JsonDocument.Parse(JsonSerializer.Serialize(report, ScanJson.Default.ScanReport)).RootElement;
        Assert.Equal("0.1.0", json.GetProperty("scanner_version").GetString());
        var device = json.GetProperty("devices")[0];
        Assert.StartsWith("PCI\\VEN_8086", device.GetProperty("instance_id").GetString());
        Assert.Equal(PciDevices.NetClass, device.GetProperty("class_guid").GetString());
        Assert.True(json.GetProperty("adapters")[0].GetProperty("has_address").GetBoolean());
    }
}

public class ScanNetworkTests
{
    [Fact]
    public void A_card_without_a_driver_is_found_by_its_class_code()
    {
        var bare = new ScanDevice("PCI\\VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10\\3&11583659&0&FE",
            ["PCI\\VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10"], ["PCI\\VEN_8086&CC_020000"], null, null, null);
        var gpu = bare with { CompatibleIds = ["PCI\\VEN_10DE&CC_030000"] };
        Assert.True(bare.IsNetwork);
        Assert.False(gpu.IsNetwork);
    }

    [Fact]
    public void Catalogs_must_be_plain_cat_names()
    {
        Assert.Equal(["x.cat"], ScanConfig.Parse("""{"server": "http://s", "mac": "aa", "catalogs": ["x.cat"]}""").Catalogs);
        Assert.Throws<FormatException>(() =>
            ScanConfig.Parse("""{"server": "http://s", "mac": "aa", "catalogs": ["..\\x.cat"]}"""));
    }
}

public class InfTests
{
    [Fact]
    public void An_inbox_inf_gets_its_catalog_named()
    {
        var text = "; Copyright\r\n[Version]\r\nSignature   = \"$Windows NT$\"\r\nDriverVer = 08/03/2015,12.19.1.32\r\n";
        var lines = Inf.AddCatalog(text, "ggnet1.cat").Split("\r\n");
        Assert.Equal("CatalogFile=ggnet1.cat", lines[2]);
        Assert.Single(Inf.AddCatalog(Inf.AddCatalog(text, "a.cat"), "b.cat").Split("\r\n"), l => l.StartsWith("CatalogFile"));
    }

    [Fact]
    public void The_copy_keeps_utf16()
    {
        var dir = Directory.CreateTempSubdirectory("ggnet-inf-").FullName;
        try
        {
            var path = Path.Combine(dir, "net1ic64.inf");
            File.WriteAllBytes(path, [0xFF, 0xFE, .. Encoding.Unicode.GetBytes("[Version]\r\nSignature=\"$Windows NT$\"\r\n")]);
            var copy = Inf.WithCatalog(path, "ggnet1.cat");
            Assert.Equal(Path.Combine(dir, "ggnet-net1ic64.inf"), copy);
            var bytes = File.ReadAllBytes(copy!);
            Assert.Equal([0xFF, 0xFE], bytes[..2]);
            Assert.Contains("CatalogFile=ggnet1.cat", Encoding.Unicode.GetString(bytes, 2, bytes.Length - 2));
        }
        finally
        {
            Directory.Delete(dir, true);
        }
    }
}
