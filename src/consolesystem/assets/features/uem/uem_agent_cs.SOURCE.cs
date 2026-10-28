// Console System agent __VER__
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Security;
using System.Net.Sockets;
using System.Net.WebSockets;
using System.Runtime.InteropServices;
using System.Drawing;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Security.Principal;
using Microsoft.Win32;
using System.ServiceProcess;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

public class CsAgent : ServiceBase
{
    const string VER = "__VER__";
    static string Data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "ConsoleSystem");
    static string PsExe = Path.Combine(Environment.SystemDirectory, "WindowsPowerShell\\v1.0\\powershell.exe");
    static JavaScriptSerializer Js = new JavaScriptSerializer { MaxJsonLength = int.MaxValue, RecursionLimit = 64 };
    static volatile bool Halt;
    static string Url = "";
    static X509Certificate2 Client, Ca;
    static readonly object LogLock = new object();
    static readonly Dictionary<string, string> Running = new Dictionary<string, string>();
    static readonly object PfLock = new object();
    static DateTime Started = DateTime.UtcNow;
    static long NdSent = 0;
    static readonly Semaphore PsSlots = new Semaphore(4, 4);
    const string ProductCode = "{6B1F2C9E-4D7A-4E58-9C31-0A5D8E7F4B21}";
    static readonly List<string> Ring = new List<string>();
    static volatile bool PubDirty = true;
    static volatile bool SyncReq;
    static volatile HttpWebRequest CurReq;
    static bool Connected; static long LastOk; static string LastErr = "";
    static List<string> Urls = new List<string>(); static int UrlIdx; static long UrlSwitched;
    static volatile bool DiagRunning;

    public CsAgent() { ServiceName = "ConsoleSystemAgent"; CanStop = true; AutoLog = false; }

    public static void Main(string[] a)
    {
        if (a.Length > 0 && a[0] == "--console") { Init(); Loop(); }
        else if (a.Length > 0 && a[0] == "--tray") RunTray();
        else if (a.Length > 0 && a[0] == "--uninstall") Environment.Exit(DoUninstall(a.Length > 1 ? a[1] : ""));
        else if (a.Length > 0 && a[0] == "--teardown") { Teardown(); Environment.Exit(0); }
        else if (a.Length > 3 && a[0] == "--check-passkey") Environment.Exit(CheckPasskey(a[1], a[2], a[3]));
        else if (a.Length > 2 && a[0] == "--check-local") Environment.Exit(CheckPasskey("", a[1], a[2]));
        else ServiceBase.Run(new CsAgent());
    }

    protected override void OnStart(string[] args)
    {
        Halt = false;
        Thread t = new Thread(delegate() { try { Init(); Loop(); } catch (Exception e) { Log("fatal: " + e); } });
        t.IsBackground = true; t.Start();
    }

    protected override void OnStop() { Halt = true; Thread.Sleep(300); }

    // ------------------------------------------------------------ tien ich
    static void Log(string s)
    {
        try
        {
            lock (LogLock)
            {
                string d = Path.Combine(Data, "log"); Directory.CreateDirectory(d);
                string f = Path.Combine(d, "agent.log");
                if (File.Exists(f) && new FileInfo(f).Length > 1048576) { try { File.Delete(f + ".1"); File.Move(f, f + ".1"); } catch { } }
                string line = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " " + s;
                File.AppendAllText(f, line + "\r\n", Encoding.UTF8);
                lock (Ring) { Ring.Add(line); if (Ring.Count > 400) Ring.RemoveAt(0); }
                PubDirty = true;
            }
        }
        catch { }
    }

    static string S(IDictionary d, string k) { object o = d != null && d.Contains(k) ? d[k] : null; return o == null ? "" : Convert.ToString(o); }
    static int I(IDictionary d, string k, int mac) { int v; return int.TryParse(S(d, k), out v) ? v : mac; }
    static List<object> L(object o) { List<object> r = new List<object>(); IEnumerable e = o as IEnumerable; if (e != null && !(o is string)) foreach (object x in e) r.Add(x); return r; }
    static long Now() { return (long)(DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds; }

    static void Init()
    {
        ServicePointManager.SecurityProtocol = (SecurityProtocolType)(3072 | 12288);
        ServicePointManager.DefaultConnectionLimit = 32;
        ServicePointManager.Expect100Continue = false;
        ServicePointManager.ServerCertificateValidationCallback = ValidateServer;
        Dictionary<string, object> cfg = (Dictionary<string, object>)Js.DeserializeObject(File.ReadAllText(Path.Combine(Data, "config.json"), Encoding.UTF8));
        Url = S(cfg, "url").TrimEnd('/');
        Urls.Add(Url);
        foreach (object o in L(cfg.ContainsKey("urls") ? cfg["urls"] : null)) { string u = Convert.ToString(o).TrimEnd('/'); if (u != "" && !Urls.Contains(u)) Urls.Add(u); }
        Ca = new X509Certificate2(File.ReadAllBytes(Path.Combine(Data, "ca.pem")));
        try { Client = new X509Certificate2(File.ReadAllBytes(Path.Combine(Data, "client.pfx")), S(cfg, "pfx_pass"), X509KeyStorageFlags.MachineKeySet); }
        catch (Exception ex)
        {   // chung chi moi hong -> dung ban sao luu truoc khi doi
            Log("khong nap duoc client.pfx (" + ex.Message + "), thu ban sao luu");
            Dictionary<string, object> bak = (Dictionary<string, object>)Js.DeserializeObject(File.ReadAllText(Path.Combine(Data, "config.json.bak"), Encoding.UTF8));
            Client = new X509Certificate2(File.ReadAllBytes(Path.Combine(Data, "client.pfx.bak")), S(bak, "pfx_pass"), X509KeyStorageFlags.MachineKeySet);
        }
        Directory.CreateDirectory(Path.Combine(Data, "tmp")); Directory.CreateDirectory(Path.Combine(Data, "profiles")); Directory.CreateDirectory(Path.Combine(Data, "nd"));
        foreach (string f in Directory.GetFiles(Path.Combine(Data, "tmp"))) { try { File.Delete(f); } catch { } }
        Directory.CreateDirectory(PubDir);
        Bg("pub", PubLoop);
        Log("khoi dong v" + VER + " -> " + Url);
    }

    // May chu phai la chung chi do CA da GHIM ky (khong kiem ten host: IP Console System co the doi, CA moi la goc tin cay)
    static bool ValidateServer(object s, X509Certificate cert, X509Chain chain, SslPolicyErrors err)
    {
        try
        {
            if (Ca == null || cert == null) return false;
            X509Certificate2 c2 = new X509Certificate2(cert);
            X509Chain ch = new X509Chain();
            ch.ChainPolicy.RevocationMode = X509RevocationMode.NoCheck;
            ch.ChainPolicy.VerificationFlags = X509VerificationFlags.AllowUnknownCertificateAuthority;
            ch.ChainPolicy.ExtraStore.Add(Ca);
            ch.Build(c2);
            bool co = false;
            foreach (X509ChainElement e in ch.ChainElements) if (e.Certificate.Thumbprint == Ca.Thumbprint) co = true;
            if (!co) return false;
            foreach (X509ChainStatus st in ch.ChainStatus)
                if (st.Status != X509ChainStatusFlags.NoError && st.Status != X509ChainStatusFlags.UntrustedRoot && st.Status != X509ChainStatusFlags.PartialChain
                    && st.Status != X509ChainStatusFlags.RevocationStatusUnknown && st.Status != X509ChainStatusFlags.OfflineRevocation) return false;
            return true;
        }
        catch { return false; }
    }

    static HttpWebRequest Req(string path, string method, int timeoutMs)
    {
        HttpWebRequest r = (HttpWebRequest)WebRequest.Create(Url + path);
        r.Method = method; r.Timeout = timeoutMs; r.ReadWriteTimeout = timeoutMs; r.Proxy = null; r.UserAgent = "ConsoleSystemAgent/" + VER;
        r.ClientCertificates.Add(Client);
        return r;
    }

    static string PostJson(string path, object body, int timeoutMs)
    {
        byte[] data = Encoding.UTF8.GetBytes(Js.Serialize(body));
        HttpWebRequest r = Req(path, "POST", timeoutMs);
        r.ContentType = "application/json; charset=utf-8"; r.ContentLength = data.Length;
        bool nhip = path == "/uem/agent/nhip";
        if (nhip) CurReq = r;
        try
        {
            using (Stream s = r.GetRequestStream()) s.Write(data, 0, data.Length);
            using (HttpWebResponse resp = (HttpWebResponse)r.GetResponse())
            using (StreamReader sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8)) return sr.ReadToEnd();
        }
        finally { if (nhip) CurReq = null; }
    }

    // ------------------------------------------------------------ vong chinh
    static void Loop()
    {
        Thread pf = new Thread(ProfileLoop); pf.IsBackground = true; pf.Start();
        int fail = 0;
        if (Urls.Count > 1 && !Probe(Url, 4000)) RotateUrl();            // dia chi dau khong toi duoc ngay luc khoi dong -> sang dia chi du phong ngay
        while (!Halt)
        {
            try
            {
                Dictionary<string, object> body = new Dictionary<string, object>();
                body["ver"] = VER; body["host"] = Environment.MachineName; body["dang"] = RunningIds(); body["pf"] = PfVersions(); body["kq_profile"] = PfPending();
                object nd = ReadNd(); if (nd != null) body["nd"] = nd;
                SyncReq = false;
                Dictionary<string, object> r = (Dictionary<string, object>)Js.DeserializeObject(PostJson("/uem/agent/nhip", body, 75000));
                if (fail > 0) Log("da noi lai Console System");
                fail = 0; Connected = true; LastOk = Now(); LastErr = ""; PubDirty = true;
                if (UrlIdx != 0 && Now() - UrlSwitched > 600)
                {   // dang o dia chi du phong: moi 10 phut thu quay lai dia chi chinh
                    UrlSwitched = Now();
                    if (Probe(Urls[0], 3000)) { UrlIdx = 0; Url = Urls[0]; Log("quay lai dia chi chinh " + Url); }
                }
                if (r.ContainsKey("ack_pf")) PfAck(L(r["ack_pf"]));
                if (r.ContainsKey("capnhat")) { SelfUpdate(r["capnhat"] as Dictionary<string, object>); continue; }
                if (r.ContainsKey("viec")) Handle(r["viec"] as Dictionary<string, object>);
            }
            catch (Exception e)
            {
                if (SyncReq) { SyncReq = false; Log("dong bo ngay theo yeu cau nguoi dung"); continue; }
                fail++; Connected = false; LastErr = e.Message; PubDirty = true;
                if (fail == 1 || fail % 20 == 0) Log("nhip loi (" + fail + "): " + e.Message);
                string cu = Url; RotateUrl();
                if (Url == cu) for (int i = 0; i < Math.Min(60, 5 * fail) && !Halt && !SyncReq; i++) Thread.Sleep(1000);
                if (SyncReq) { SyncReq = false; Log("dong bo ngay theo yeu cau nguoi dung"); }
            }
        }
    }

    static List<object> RunningIds() { lock (Running) { return new List<object>(Running.Keys); } }

    static void Result(string id, string o, string e, int code)
    {
        Dictionary<string, object> b = new Dictionary<string, object>();
        b["id"] = id; b["out"] = o ?? ""; b["err"] = e ?? ""; b["code"] = code;
        for (int i = 0; i < 4; i++)
        {
            try { PostJson("/uem/agent/ketqua", b, 60000); return; }
            catch (Exception ex) { Log("ketqua loi: " + ex.Message); Thread.Sleep(3000); }
        }
    }

    static void Bg(string ten, ThreadStart f) { Thread t = new Thread(f); t.IsBackground = true; t.Name = ten; t.Start(); }

    static void Handle(Dictionary<string, object> job)
    {
        string id = S(job, "id"), kieu = S(job, "kieu");
        Log("viec " + kieu + " " + id);
        try
        {
            switch (kieu)
            {
                case "ps": lock (Running) Running[id] = kieu; Bg("ps", delegate() { JobPs(id, S(job, "script"), I(job, "timeout", 3600)); }); break;
                case "tep_len": lock (Running) Running[id] = kieu; Bg("tep", delegate() { JobTepLen(id, S(job, "duong")); }); break;
                case "tep_xuong": lock (Running) Running[id] = kieu; Bg("tep", delegate() { JobTepXuong(id, S(job, "duong")); }); break;
                case "tunnel": JobTunnel(id, S(job, "tok"), I(job, "cong", 5900)); break;
                case "shell": JobShell(id, S(job, "tok"), S(job, "loai")); break;
                case "hoi_phep": lock (Running) Running[id] = kieu; Bg("phep", delegate() { JobPhep(id, S(job, "thong_bao"), I(job, "giay", 40)); }); break;
                case "doi_chung_chi": DoiChungChi(id, job); break;
                case "profile": SaveBundle(job); Result(id, "OK", "", 0); break;
                case "profile_go": try { File.Delete(Path.Combine(Data, "profiles", Safe(S(job, "pid")) + ".json")); } catch { } Result(id, "OK", "", 0); break;
                case "profile_chay": ForceRun(S(job, "pid")); Result(id, "OK", "", 0); break;
                default: Result(id, "", "kieu viec khong ho tro: " + kieu, 2); break;
            }
        }
        catch (Exception e) { Result(id, "", "Loi agent: " + e.Message, 3); lock (Running) Running.Remove(id); }
    }

    static string Safe(string s) { return Regex.Replace(s ?? "", "[^A-Za-z0-9_-]", ""); }

    // ------------------------------------------------------------ chay PowerShell
    static void RunPs(string script, int timeoutSec, out string o, out string e, out int code)
    {
        PsSlots.WaitOne();
        string f = Path.Combine(Data, "tmp", Guid.NewGuid().ToString("N") + ".ps1");
        o = ""; e = ""; code = 0;
        try
        {
            File.WriteAllText(f, "[Console]::OutputEncoding=[Text.Encoding]::UTF8; $OutputEncoding=[Text.Encoding]::UTF8\r\n" + script, new UTF8Encoding(true));
            ProcessStartInfo psi = new ProcessStartInfo(PsExe, "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File \"" + f + "\"");
            psi.UseShellExecute = false; psi.CreateNoWindow = true; psi.RedirectStandardOutput = true; psi.RedirectStandardError = true; psi.RedirectStandardInput = true;
            psi.StandardOutputEncoding = Encoding.UTF8; psi.StandardErrorEncoding = Encoding.UTF8;
            StringBuilder so = new StringBuilder(), se = new StringBuilder();
            using (Process p = Process.Start(psi))
            {
                p.StandardInput.Close();
                p.OutputDataReceived += delegate(object s, DataReceivedEventArgs a) { if (a.Data != null && so.Length < 4000000) lock (so) so.AppendLine(a.Data); };
                p.ErrorDataReceived += delegate(object s, DataReceivedEventArgs a) { if (a.Data != null && se.Length < 200000) lock (se) se.AppendLine(a.Data); };
                p.BeginOutputReadLine(); p.BeginErrorReadLine();
                if (!p.WaitForExit(Math.Max(5, timeoutSec) * 1000))
                {
                    try { Process.Start(new ProcessStartInfo("taskkill", "/T /F /PID " + p.Id) { CreateNoWindow = true, UseShellExecute = false }).WaitForExit(10000); } catch { }
                    code = -1; lock (se) se.AppendLine("Het thoi gian cho phep (" + timeoutSec + " giay)");
                }
                else { p.WaitForExit(); code = p.ExitCode; }
            }
            lock (so) o = so.ToString(); lock (se) e = se.ToString().Trim();
        }
        catch (Exception ex) { e = "Khong chay duoc PowerShell: " + ex.Message; code = -2; }
        finally { try { File.Delete(f); } catch { } PsSlots.Release(); }
    }

    static void JobPs(string id, string script, int timeout)
    {
        string o, e; int c;
        try { RunPs(script, timeout, out o, out e, out c); Result(id, o, e, c); }
        finally { lock (Running) Running.Remove(id); }
    }

    // ------------------------------------------------------------ chuyen file dang luong
    static void JobTepLen(string id, string duong)
    {
        try
        {
            HttpWebRequest r = Req("/uem/agent/tep/" + Safe(id), "PUT", 3600000);
            r.SendChunked = true; r.AllowWriteStreamBuffering = false; r.ContentType = "application/octet-stream";
            long n;
            using (FileStream fs = File.OpenRead(duong)) { n = fs.Length; using (Stream s = r.GetRequestStream()) fs.CopyTo(s, 262144); }
            using (HttpWebResponse resp = (HttpWebResponse)r.GetResponse()) { }
            Result(id, "OK " + n, "", 0);
        }
        catch (Exception e) { Result(id, "", "Khong tai len duoc: " + e.Message, 1); }
        finally { lock (Running) Running.Remove(id); }
    }

    static void JobTepXuong(string id, string duong)
    {
        string tam = duong + ".cs-tmp";
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(duong));
            HttpWebRequest r = Req("/uem/agent/tep/" + Safe(id), "GET", 3600000);
            long n = 0;
            using (HttpWebResponse resp = (HttpWebResponse)r.GetResponse())
            using (Stream rs = resp.GetResponseStream())
            using (FileStream fs = File.Create(tam)) { rs.CopyTo(fs, 262144); n = fs.Length; }
            if (File.Exists(duong)) File.Delete(duong);
            File.Move(tam, duong);
            Result(id, "OK " + n, "", 0);
        }
        catch (Exception e) { try { File.Delete(tam); } catch { } Result(id, "", "Khong tai xuong duoc: " + e.Message, 1); }
        finally { lock (Running) Running.Remove(id); }
    }

    // ------------------------------------------------------------ tunnel VNC di nguoc qua TLS
    static void JobTunnel(string id, string tok, int cong)
    {
        string ws = Url.Replace("https://", "wss://") + "/uem-agent-ws/" + Safe(tok);
        Bg("tunnel", delegate()
        {
            try
            {
                using (ClientWebSocket w = new ClientWebSocket())
                using (TcpClient tcp = new TcpClient())
                {
                    w.Options.ClientCertificates.Add(Client);
                    w.Options.AddSubProtocol("binary");
                    w.Options.KeepAliveInterval = TimeSpan.FromSeconds(30);
                    CancellationTokenSource cts = new CancellationTokenSource();
                    tcp.Connect("127.0.0.1", cong); Log("tunnel: da noi VNC 127.0.0.1:" + cong);
                    w.ConnectAsync(new Uri(ws), cts.Token).Wait(20000);
                    if (w.State != WebSocketState.Open) throw new Exception("khong mo duoc WebSocket (" + w.State + ")");
                    Log("tunnel: da noi " + ws);
                    NetworkStream ns = tcp.GetStream();
                    Thread t1 = new Thread(delegate()
                    {
                        try { byte[] b = new byte[65536]; int n; while ((n = ns.Read(b, 0, b.Length)) > 0) w.SendAsync(new ArraySegment<byte>(b, 0, n), WebSocketMessageType.Binary, true, cts.Token).Wait(); }
                        catch { }
                        try { cts.Cancel(); } catch { }
                    });
                    t1.IsBackground = true; t1.Start();
                    byte[] rb = new byte[65536];
                    while (w.State == WebSocketState.Open && !cts.IsCancellationRequested)
                    {
                        WebSocketReceiveResult rr = w.ReceiveAsync(new ArraySegment<byte>(rb), cts.Token).Result;
                        if (rr.MessageType == WebSocketMessageType.Close) break;
                        if (rr.Count > 0) ns.Write(rb, 0, rr.Count);
                    }
                    try { tcp.Close(); } catch { }
                }
            }
            catch (Exception e) { Log("tunnel dong: " + e.GetBaseException().GetType().Name + ": " + e.GetBaseException().Message); }
        });
        Result(id, "OK", "", 0);
    }

    // ------------------------------------------------------------ cua so dong lenh truc tiep (cmd / PowerShell)
    // Mo 1 tien trinh cmd.exe hoac powershell.exe (quyen SYSTEM), noi stdin/stdout qua WebSocket nguoc (mTLS) ve Console System:
    // trinh duyet go dong nao thi gui vao stdin, ket qua chay ra tung khuc ngay (khong doi lenh xong). Dong WebSocket -> diet tien trinh.
    static void JobShell(string id, string tok, string loai)
    {
        string ws = Url.Replace("https://", "wss://") + "/uem-agent-ws/" + Safe(tok);
        bool ps = loai == "powershell";
        Bg("shell", delegate()
        {
            Process p = null;
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                // Ca hai chay trong cmd da "chcp 65001": PowerShell ke thua bang ma UTF-8 cua console an -> tieng Viet vao/ra dung.
                psi.FileName = Path.Combine(Environment.SystemDirectory, "cmd.exe");
                psi.Arguments = ps ? "/Q /C chcp 65001>nul & \"" + Path.Combine(Environment.SystemDirectory, @"WindowsPowerShell\v1.0\powershell.exe") + "\" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command -"
                                   : "/Q /K chcp 65001>nul";
                psi.UseShellExecute = false; psi.CreateNoWindow = true;
                psi.RedirectStandardInput = true; psi.RedirectStandardOutput = true; psi.RedirectStandardError = true;
                psi.WorkingDirectory = Environment.GetEnvironmentVariable("SystemDrive") + "\\";
                using (ClientWebSocket w = new ClientWebSocket())
                {
                    w.Options.ClientCertificates.Add(Client);
                    w.Options.AddSubProtocol("binary");
                    w.Options.KeepAliveInterval = TimeSpan.FromSeconds(30);
                    CancellationTokenSource cts = new CancellationTokenSource();
                    w.ConnectAsync(new Uri(ws), cts.Token).Wait(20000);
                    if (w.State != WebSocketState.Open) throw new Exception("khong mo duoc WebSocket (" + w.State + ")");
                    p = Process.Start(psi);
                    Log("shell: " + (ps ? "powershell" : "cmd") + " pid " + p.Id);
                    object khoaGui = new object();
                    Action<byte[], int> gui = delegate(byte[] b, int n)
                    {
                        lock (khoaGui) { try { w.SendAsync(new ArraySegment<byte>(b, 0, n), WebSocketMessageType.Binary, true, cts.Token).Wait(); } catch { cts.Cancel(); } }
                    };
                    Stream[] ra = new Stream[] { p.StandardOutput.BaseStream, p.StandardError.BaseStream };
                    foreach (Stream st in ra)
                    {
                        Stream s1 = st;
                        Thread t = new Thread(delegate()
                        {
                            try { byte[] b = new byte[8192]; int n; while ((n = s1.Read(b, 0, b.Length)) > 0) gui(b, n); } catch { }
                        });
                        t.IsBackground = true; t.Start();
                    }
                    Process pp = p;
                    Thread cho = new Thread(delegate() { try { pp.WaitForExit(); Thread.Sleep(300); } catch { } try { cts.Cancel(); } catch { } });
                    cho.IsBackground = true; cho.Start();
                    Stream vao = p.StandardInput.BaseStream;
                    if (ps)
                    {
                        byte[] dau = Encoding.UTF8.GetBytes("$OutputEncoding=[Text.Encoding]::UTF8; Write-Host -NoNewline ('PS ' + (Get-Location).Path + '> ')\n");
                        vao.Write(dau, 0, dau.Length); vao.Flush();
                    }
                    byte[] rb = new byte[65536];
                    while (w.State == WebSocketState.Open && !cts.IsCancellationRequested)
                    {
                        WebSocketReceiveResult rr = w.ReceiveAsync(new ArraySegment<byte>(rb), cts.Token).Result;
                        if (rr.MessageType == WebSocketMessageType.Close) break;
                        if (rr.Count <= 0) continue;
                        vao.Write(rb, 0, rr.Count);
                        if (ps && rb[rr.Count - 1] == 10)          // PowerShell khong tu in dau nhac khi doc stdin -> tu in sau moi dong
                        {
                            byte[] nh = Encoding.UTF8.GetBytes("Write-Host -NoNewline ('PS ' + (Get-Location).Path + '> ')\n");
                            vao.Write(nh, 0, nh.Length);
                        }
                        vao.Flush();
                    }
                }
            }
            catch (Exception e) { Log("shell dong: " + e.GetBaseException().GetType().Name + ": " + e.GetBaseException().Message); }
            finally
            {
                if (p != null)
                {
                    try { if (!p.HasExited) Process.Start(new ProcessStartInfo("taskkill.exe", "/T /F /PID " + p.Id) { UseShellExecute = false, CreateNoWindow = true }).WaitForExit(5000); } catch { }
                }
            }
        });
        Result(id, "OK", "", 0);
    }

    // ------------------------------------------------------------ xin phep nguoi dang dung may
    [DllImport("wtsapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool WTSSendMessage(IntPtr hServer, int sessionId, string title, int titleLen, string msg, int msgLen, int style, int timeout, out int response, bool wait);
    [DllImport("kernel32.dll")] static extern uint WTSGetActiveConsoleSessionId();

    static void JobPhep(string id, string tb, int giay)
    {
        try
        {
            uint sid = WTSGetActiveConsoleSessionId();
            if (sid == 0xFFFFFFFF) { Result(id, "KHONG_CO_PHIEN", "", 0); return; }
            int resp;
            string tieu = "Console System";
            bool ok = WTSSendMessage(IntPtr.Zero, (int)sid, tieu, tieu.Length * 2, tb, tb.Length * 2, 0x4 | 0x20 | 0x40000, giay, out resp, true);   // do dai tinh bang BYTE (Unicode)
            Result(id, !ok ? "KHONG_CO_PHIEN" : (resp == 6 ? "CHO_PHEP" : (resp == 7 ? "TU_CHOI" : "HET_GIO")), "", 0);
        }
        catch (Exception e) { Result(id, "", e.Message, 1); }
        finally { lock (Running) Running.Remove(id); }
    }

    // ------------------------------------------------------------ du lieu tro ly phien nguoi dung
    static object ReadNd()
    {
        try
        {
            string d = Path.Combine(Data, "nd"); FileInfo best = null;
            foreach (string f in Directory.GetFiles(d, "*.json")) { FileInfo fi = new FileInfo(f); if (fi.Length < 400000 && (best == null || fi.LastWriteTimeUtc > best.LastWriteTimeUtc)) best = fi; }
            if (best == null || best.LastWriteTimeUtc.Ticks <= NdSent || (DateTime.UtcNow - best.LastWriteTimeUtc).TotalHours > 8) return null;
            object o = Js.DeserializeObject(File.ReadAllText(best.FullName, Encoding.UTF8));
            NdSent = best.LastWriteTimeUtc.Ticks; return o;
        }
        catch { return null; }
    }

    // ------------------------------------------------------------ PROFILE TU TRI
    static Dictionary<string, object> LoadJson(string f) { try { return (Dictionary<string, object>)Js.DeserializeObject(File.ReadAllText(f, Encoding.UTF8)); } catch { return null; } }
    static void SaveJson(string f, object o) { string t = f + ".tmp"; File.WriteAllText(t, Js.Serialize(o), new UTF8Encoding(false)); if (File.Exists(f)) File.Delete(f); File.Move(t, f); }
    static string PfDir { get { return Path.Combine(Data, "profiles"); } }
    static string StateFile { get { return Path.Combine(PfDir, "state.dat"); } }
    static string PendFile { get { return Path.Combine(PfDir, "pending.dat"); } }
    static HashSet<string> Force = new HashSet<string>();

    static Dictionary<string, object> PfVersions()
    {
        Dictionary<string, object> r = new Dictionary<string, object>();
        try { foreach (string f in Directory.GetFiles(PfDir, "*.json")) { Dictionary<string, object> b = LoadJson(f); if (b != null) r[S(b, "pid")] = S(b, "ver"); } } catch { }
        return r;
    }

    static void SaveBundle(Dictionary<string, object> job)
    {
        string pid = Safe(S(job, "pid"));
        lock (PfLock)
        {
            SaveJson(Path.Combine(PfDir, pid + ".json"), job);
            Force.Add(pid);
        }
    }

    static void ForceRun(string pid) { lock (PfLock) Force.Add(Safe(pid)); }

    static List<object> PfPending() { lock (PfLock) { Dictionary<string, object> d = LoadJson(PendFile); return d == null ? new List<object>() : L(d["ds"]); } }

    static void PfAck(List<object> acks)
    {
        lock (PfLock)
        {
            Dictionary<string, object> d = LoadJson(PendFile); if (d == null) return;
            List<object> giu = new List<object>();
            foreach (object o in L(d["ds"])) { Dictionary<string, object> k = (Dictionary<string, object>)o; bool xong = false; foreach (object a in acks) if (Convert.ToString(a) == S(k, "pid") + "|" + S(k, "luc")) xong = true; if (!xong) giu.Add(o); }
            Dictionary<string, object> nd = new Dictionary<string, object>(); nd["ds"] = giu; SaveJson(PendFile, nd);
        }
    }

    static void ProfileLoop()
    {
        Thread.Sleep(45000);
        while (!Halt)
        {
            try
            {
                foreach (string f in Directory.GetFiles(PfDir, "*.json"))
                {
                    if (Halt) break;
                    string ten = Path.GetFileName(f); if (ten == "state.dat" || ten == "pending.dat") continue;
                    Dictionary<string, object> b = LoadJson(f); if (b == null) continue;
                    string pid = S(b, "pid"); long chuky = Math.Max(5, I(b, "chu_ky", 30)) * 60;
                    Dictionary<string, object> st; lock (PfLock) { st = LoadJson(StateFile) ?? new Dictionary<string, object>(); }
                    Dictionary<string, object> mine = st.ContainsKey(pid) ? (Dictionary<string, object>)st[pid] : null;
                    bool ep; lock (PfLock) { ep = Force.Remove(pid); }
                    long last = mine == null ? 0 : (long)Convert.ToDouble(S(mine, "last_run"));
                    if (ep || mine == null || Now() - last >= chuky) RunBundle(b, st);
                }
            }
            catch (Exception e) { Log("profile loi: " + e.Message); }
            for (int i = 0; i < 20 && !Halt; i++) Thread.Sleep(1000);
        }
    }

    static void RunBundle(Dictionary<string, object> b, Dictionary<string, object> st)
    {
        string pid = S(b, "pid"), ver = S(b, "ver");
        Dictionary<string, object> mine = st.ContainsKey(pid) ? (Dictionary<string, object>)st[pid] : new Dictionary<string, object>();
        Dictionary<string, object> old = mine.ContainsKey("tasks") ? (Dictionary<string, object>)mine["tasks"] : new Dictionary<string, object>();
        Dictionary<string, object> res = new Dictionary<string, object>();
        long t0 = Now(); bool dung = false; int loi = 0, lam = 0;
        Log("ap profile " + pid);
        foreach (object o in L(b["tasks"]))
        {
            Dictionary<string, object> t = (Dictionary<string, object>)o; string tid = S(t, "id");
            Dictionary<string, object> cu = old.ContainsKey(tid) ? (Dictionary<string, object>)old[tid] : null;
            Dictionary<string, object> r = new Dictionary<string, object>();
            if (dung) { r["tt"] = "bo_qua"; r["tb"] = "Bo qua vi tac vu truoc bi loi."; r["luc"] = Now(); res[tid] = r; continue; }
            string tv = S(t, "ver");
            if (S(t, "loai") == "powershell" && S(t, "mot_lan") == "True" && cu != null && S(cu, "ok_ver") == tv && tv != "")
            { r["tt"] = "da_chay_truoc"; r["tb"] = "Da chay thanh cong truoc do (che do mot lan)."; r["luc"] = S(cu, "luc"); r["ok_ver"] = tv; res[tid] = r; continue; }
            string o2, e2; int c2;
            RunPs(S(t, "script"), I(t, "timeout", 3600), out o2, out e2, out c2);
            string tt, tb;
            if (S(t, "loai") == "powershell") { if (e2 != "" || c2 != 0) { tt = "loi"; tb = "Script bao loi: " + (e2 != "" ? e2 : "ma " + c2); } else { tt = "da_lam"; tb = ("Chay xong. " + o2.Trim()); } }
            else
            {
                Match m = Regex.Match(o2, "ST=(DA_DAT|DA_LAM|LOI)[ \\t]*([^\\r\\n]*)");
                if (!m.Success) { tt = "loi"; tb = "Khong nhan duoc ket qua. " + (e2 != "" ? e2 : o2.Trim()); }
                else { tt = m.Groups[1].Value == "DA_DAT" ? "da_dat" : (m.Groups[1].Value == "DA_LAM" ? "da_lam" : "loi"); tb = m.Groups[2].Value.Trim(); }
            }
            if (tb.Length > 400) tb = tb.Substring(0, 400);
            r["tt"] = tt; r["tb"] = tb; r["luc"] = Now(); r["ok_ver"] = tt != "loi" ? tv : (cu != null && S(cu, "ok_ver") == tv ? tv : "");
            res[tid] = r;
            if (tt == "da_lam") lam++;
            if (tt == "loi") { loi++; if (S(t, "bo_qua_loi") != "True") dung = true; }
        }
        Dictionary<string, object> ns = new Dictionary<string, object>();
        ns["last_run"] = t0; ns["tasks"] = res; ns["ver"] = ver;
        lock (PfLock)
        {
            Dictionary<string, object> st2 = LoadJson(StateFile) ?? new Dictionary<string, object>(); st2[pid] = ns; SaveJson(StateFile, st2);
            Dictionary<string, object> pd = LoadJson(PendFile) ?? new Dictionary<string, object>(); List<object> ds = pd.ContainsKey("ds") ? L(pd["ds"]) : new List<object>();
            List<object> nds = new List<object>(); foreach (object x in ds) if (S((Dictionary<string, object>)x, "pid") != pid) nds.Add(x);
            Dictionary<string, object> k = new Dictionary<string, object>();
            k["pid"] = pid; k["ver"] = ver; k["luc"] = Now(); k["trang_thai"] = loi > 0 ? "loi" : "ok"; k["lam"] = lam; k["loi"] = loi; k["tasks"] = res;
            nds.Add(k); if (nds.Count > 40) nds.RemoveAt(0);
            Dictionary<string, object> np = new Dictionary<string, object>(); np["ds"] = nds; SaveJson(PendFile, np);
        }
    }

    // ------------------------------------------------------------ doi chung chi khach (gia han, hoac cap lai do nguoi quan tri)
    static void DoiChungChi(string id, Dictionary<string, object> job)
    {
        try
        {
            byte[] pfx = Convert.FromBase64String(S(job, "pfx")); string mk = S(job, "pfx_pass");
            new X509Certificate2(pfx, mk, X509KeyStorageFlags.MachineKeySet);          // thu nap duoc roi moi thay (hong thi bao loi, giu chung chi cu)
            string pf = Path.Combine(Data, "client.pfx"), cf = Path.Combine(Data, "config.json");
            File.Copy(pf, pf + ".bak", true); File.Copy(cf, cf + ".bak", true);
            Dictionary<string, object> cfg = (Dictionary<string, object>)Js.DeserializeObject(File.ReadAllText(cf, Encoding.UTF8));
            cfg["pfx_pass"] = mk;
            File.WriteAllBytes(pf, pfx); File.WriteAllText(cf, Js.Serialize(cfg), new UTF8Encoding(true));
            Result(id, "OK", "", 0);
            Log("da doi chung chi khach, khoi dong lai dich vu");
            Process.Start(new ProcessStartInfo(PsExe, "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command \"Start-Sleep 3; Restart-Service ConsoleSystemAgent -Force\"") { UseShellExecute = false, CreateNoWindow = true });
        }
        catch (Exception e) { Result(id, "", "Khong doi duoc chung chi: " + e.Message, 1); }
    }



    // ------------------------------------------------------------ nhieu dia chi server (du phong) + chan doan
    static bool Probe(string url, int ms)
    {
        try
        {
            Uri u = new Uri(url);
            using (TcpClient c = new TcpClient())
            {
                IAsyncResult ar = c.BeginConnect(u.Host, u.Port, null, null);
                if (!ar.AsyncWaitHandle.WaitOne(ms, false)) return false;
                c.EndConnect(ar); return true;
            }
        }
        catch { return false; }
    }

    static void RotateUrl()
    {
        if (Urls.Count < 2) return;
        for (int i = 1; i < Urls.Count; i++)
        {
            int k = (UrlIdx + i) % Urls.Count;
            if (Probe(Urls[k], 4000)) { UrlIdx = k; Url = Urls[k]; UrlSwitched = Now(); Log("chuyen sang dia chi " + (k == 0 ? "chinh " : "du phong ") + Url); return; }
        }
    }

    static void DiagAdd(List<object> it, string ten, string tt, string gc)
    {
        Dictionary<string, object> d = new Dictionary<string, object>(); d["ten"] = ten; d["tt"] = tt; d["gc"] = gc; it.Add(d);
    }

    static void WriteDiag(List<object> it, bool dang, long bd)
    {
        Dictionary<string, object> d = new Dictionary<string, object>(); d["dang"] = dang; d["luc_bd"] = bd; d["luc"] = Now(); d["muc"] = it;
        SaveJson(Path.Combine(PubDir, "diag.json"), d);
    }

    // Kiem tra tung buoc va ghi pub\diag.json (khay doc). Chay trong dich vu (SYSTEM) vi nguoi dung khong doc duoc chung chi/cau hinh.
    static void RunDiag()
    {
        if (DiagRunning) return;
        DiagRunning = true; long bd = Now();
        List<object> it = new List<object>();
        try
        {
            WriteDiag(it, true, bd);
            TimeSpan up = DateTime.UtcNow - Started;
            DiagAdd(it, "Dịch vụ agent", "ok", "Phiên bản " + VER + ", chạy được " + (int)up.TotalMinutes + " phút, tài khoản " + WindowsIdentity.GetCurrent().Name);
            if (Client == null) DiagAdd(it, "Chứng chỉ của máy", "loi", "Chưa nạp được chứng chỉ máy (client.pfx).");
            else
            {
                double days = (Client.NotAfter - DateTime.Now).TotalDays;
                string gc = "Hết hạn " + Client.NotAfter.ToString("dd/MM/yyyy") + " (còn " + (int)days + " ngày), " + (Client.HasPrivateKey ? "có khóa riêng" : "THIẾU khóa riêng");
                DiagAdd(it, "Chứng chỉ của máy", days < 0 || !Client.HasPrivateKey ? "loi" : (days < 20 ? "canhbao" : "ok"), gc + (days < 60 && days >= 0 ? ". Agent sẽ tự xin chứng chỉ mới khi còn dưới 60 ngày và kết nối được server." : ""));
            }
            DiagAdd(it, "CA của Console System", Ca == null ? "loi" : "ok", Ca == null ? "Thiếu ca.pem." : "Đã ghim CA, dấu vân tay " + Ca.Thumbprint.Substring(0, 16) + "...");
            long skew = long.MinValue; int stt = 0;
            foreach (string u in Urls)
            {
                stt++; string nhan = "Server " + u.Replace("https://", "") + (stt == 1 ? " (chính)" : " (dự phòng)") + (u == Url ? " *" : "");
                Uri uri; try { uri = new Uri(u); } catch { DiagAdd(it, nhan, "loi", "Địa chỉ không hợp lệ."); WriteDiag(it, true, bd); continue; }
                string host = uri.Host; System.Net.IPAddress ip0;
                if (!System.Net.IPAddress.TryParse(host, out ip0))
                {
                    try { System.Net.IPAddress[] ips = Dns.GetHostAddresses(host); List<string> ls = new List<string>(); foreach (System.Net.IPAddress a in ips) ls.Add(a.ToString()); DiagAdd(it, nhan + ": phân giải tên", "ok", host + " = " + string.Join(", ", ls.ToArray())); }
                    catch (Exception e) { DiagAdd(it, nhan + ": phân giải tên", "loi", "Không phân giải được " + host + ": " + e.Message + ". Kiểm tra DNS hoặc mạng."); WriteDiag(it, true, bd); continue; }
                }
                DateTime t0 = DateTime.UtcNow;
                if (!Probe(u, 5000)) { DiagAdd(it, nhan + ": cổng " + uri.Port, "loi", "Không mở được kết nối TCP tới cổng " + uri.Port + " (tường lửa, chuyển cổng chưa đúng, hoặc server tắt)."); WriteDiag(it, true, bd); continue; }
                DiagAdd(it, nhan + ": cổng " + uri.Port, "ok", "Mở được kết nối TCP (" + (int)(DateTime.UtcNow - t0).TotalMilliseconds + " ms)." + (u == Url ? " Đây là địa chỉ agent đang dùng." : ""));
                try
                {
                    t0 = DateTime.UtcNow;
                    HttpWebRequest r = (HttpWebRequest)WebRequest.Create(u + "/uem/agent/ping");
                    r.Method = "GET"; r.Timeout = 10000; r.ReadWriteTimeout = 10000; r.Proxy = null; r.ClientCertificates.Add(Client); r.UserAgent = "ConsoleSystemAgent/" + VER;
                    string body; using (HttpWebResponse resp = (HttpWebResponse)r.GetResponse()) using (StreamReader sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8)) body = sr.ReadToEnd();
                    Dictionary<string, object> pj = (Dictionary<string, object>)Js.DeserializeObject(body);
                    long gio; long.TryParse(S(pj, "gio"), out gio); if (skew == long.MinValue && gio > 0) skew = Now() - gio;
                    DiagAdd(it, nhan + ": xác thực hai chiều (mTLS)", "ok", "Server tin chứng chỉ của máy, agent tin server (" + (int)(DateTime.UtcNow - t0).TotalMilliseconds + " ms). Server bản " + S(pj, "ban") + ".");
                }
                catch (WebException we)
                {
                    HttpWebResponse hr = we.Response as HttpWebResponse; string gc;
                    if (hr != null && (int)hr.StatusCode == 403) gc = "Server từ chối chứng chỉ của máy (đã bị thu hồi hoặc chưa ghi danh). Cần cài lại agent bằng file mới.";
                    else if (we.Status == WebExceptionStatus.TrustFailure || we.Status == WebExceptionStatus.SecureChannelFailure) gc = "Không thiết lập được TLS: chứng chỉ server không do CA đã ghim ký, hoặc đồng hồ máy sai nhiều. " + we.Message;
                    else gc = we.Message;
                    DiagAdd(it, nhan + ": xác thực hai chiều (mTLS)", "loi", gc);
                }
                catch (Exception e) { DiagAdd(it, nhan + ": xác thực hai chiều (mTLS)", "loi", e.Message); }
                WriteDiag(it, true, bd);
            }
            if (skew != long.MinValue) DiagAdd(it, "Đồng hồ của máy", Math.Abs(skew) > 300 ? "canhbao" : "ok", Math.Abs(skew) > 300 ? "Lệch " + skew + " giây so với server. Giờ sai nhiều có thể làm TLS thất bại." : "Lệch " + skew + " giây so với server.");
            long ago = Now() - LastOk;
            DiagAdd(it, "Nhịp báo cáo gần nhất", Connected ? "ok" : "loi", Connected ? "Nối được server, nhịp gần nhất " + ago + " giây trước, đang dùng " + Url + "." : "Đang mất kết nối" + (LastErr != "" ? ": " + LastErr : "") + (LastOk > 0 ? ". Lần nối được gần nhất cách đây " + (ago / 60) + " phút." : ""));
            int np = 0; try { np = Directory.GetFiles(PfDir, "*.json").Length; } catch { }
            DiagAdd(it, "Profile (policy) lưu trên máy", "ok", np + " profile; tự áp dụng theo chu kỳ kể cả khi mất kết nối server.");
            try
            {
                DriveInfo di = new DriveInfo(Path.GetPathRoot(Data)); double gb = di.AvailableFreeSpace / 1073741824.0;
                DiagAdd(it, "Dung lượng ổ " + di.Name, gb < 0.2 ? "loi" : (gb < 1 ? "canhbao" : "ok"), "Còn trống " + gb.ToString("0.0") + " GB.");
            }
            catch { }
            DiagAdd(it, "Passkey gỡ cài đặt", "ok", File.Exists(Path.Combine(Data, "passkey.json")) ? "Đã đặt: gỡ agent cần nhập passkey." : "Không đặt: gỡ agent không cần passkey.");
        }
        catch (Exception e) { DiagAdd(it, "Chẩn đoán", "loi", "Lỗi khi chẩn đoán: " + e.Message); }
        finally { WriteDiag(it, false, bd); DiagRunning = false; }
    }

    // ------------------------------------------------------------ thu muc cong khai cho bieu tuong khay (nguoi dung doc duoc)
    static string PubDir { get { return Path.Combine(Data, "pub"); } }
    static string NdDir { get { return Path.Combine(Data, "nd"); } }

    static void PubLoop()
    {
        long lastStatus = 0;
        while (!Halt)
        {
            try
            {
                string flag = Path.Combine(NdDir, "sync.flag");
                if (File.Exists(flag))
                {
                    try { File.Delete(flag); } catch { }
                    SyncReq = true; HttpWebRequest r = CurReq; if (r != null) { try { r.Abort(); } catch { } }
                }
                string dflag = Path.Combine(NdDir, "diag.flag");
                if (File.Exists(dflag)) { try { File.Delete(dflag); } catch { } if (!DiagRunning) Bg("diag", RunDiag); }
                if (PubDirty || Now() - lastStatus >= 5)
                {
                    PubDirty = false; lastStatus = Now();
                    string txt; lock (Ring) txt = string.Join("\r\n", Ring.ToArray());
                    File.WriteAllText(Path.Combine(PubDir, "log.txt"), txt, new UTF8Encoding(true));
                    Dictionary<string, object> st = new Dictionary<string, object>();
                    st["ver"] = VER; st["ket_noi"] = Connected; st["luc_ok"] = LastOk; st["loi"] = LastErr; st["server"] = Url; st["luc"] = Now(); st["so_dia_chi"] = Urls.Count;
                    st["passkey"] = File.Exists(Path.Combine(Data, "passkey.json"));
                    SaveJson(Path.Combine(PubDir, "status.json"), st);
                }
            }
            catch { }
            Thread.Sleep(1000);
        }
    }

    // ------------------------------------------------------------ passkey (PBKDF2-SHA1, dinh dang p1:so-vong:muoi-hex:bam-hex)
    static byte[] HexB(string h) { byte[] b = new byte[h.Length / 2]; for (int i = 0; i < b.Length; i++) b[i] = Convert.ToByte(h.Substring(i * 2, 2), 16); return b; }
    static string HexS(byte[] b) { StringBuilder sb = new StringBuilder(); foreach (byte x in b) sb.Append(x.ToString("x2")); return sb.ToString(); }

    static bool PkOk(string pk, string pw)
    {
        try
        {
            string[] p = pk.Split(':');
            if (p.Length != 4 || p[0] != "p1") return false;
            using (Rfc2898DeriveBytes d = new Rfc2898DeriveBytes(pw, HexB(p[2]), int.Parse(p[1])))
            {
                string h = HexS(d.GetBytes(32)); int diff = h.Length ^ p[3].Length;
                for (int i = 0; i < h.Length && i < p[3].Length; i++) diff |= h[i] ^ p[3][i];
                return diff == 0;
            }
        }
        catch { return false; }
    }

    static string LocalPk()
    {
        try
        {
            Dictionary<string, object> d = LoadJson(Path.Combine(Data, "passkey.json"));
            return d == null ? "" : S(d, "pk");
        }
        catch { return ""; }
    }

    static void MsiLog(string s)
    {
        try { File.AppendAllText(Path.Combine(Environment.GetEnvironmentVariable("windir"), "Temp\\cs-agent-msi.log"), DateTime.Now.ToString("s") + " " + s + "\r\n"); } catch { }
    }

    // Hop thoai nhap passkey (che ky tu). Tra ve null neu bam Huy.
    static string Prompt(string title, string text)
    {
        using (Form f = new Form())
        {
            f.Text = title; f.FormBorderStyle = FormBorderStyle.FixedDialog; f.StartPosition = FormStartPosition.CenterScreen; f.MaximizeBox = false; f.MinimizeBox = false;
            f.ClientSize = new Size(420, 130); f.TopMost = true; f.ShowInTaskbar = true;
            Label l = new Label(); l.Text = text; l.Left = 14; l.Top = 14; l.Width = 392; l.Height = 36;
            TextBox t = new TextBox(); t.Left = 14; t.Top = 56; t.Width = 392; t.UseSystemPasswordChar = true;
            Button ok = new Button(); ok.Text = "OK"; ok.Left = 232; ok.Top = 90; ok.Width = 84; ok.DialogResult = DialogResult.OK;
            Button hu = new Button(); hu.Text = "Hủy"; hu.Left = 322; hu.Top = 90; hu.Width = 84; hu.DialogResult = DialogResult.Cancel;
            f.Controls.Add(l); f.Controls.Add(t); f.Controls.Add(ok); f.Controls.Add(hu); f.AcceptButton = ok; f.CancelButton = hu;
            return f.ShowDialog() == DialogResult.OK ? t.Text : null;
        }
    }

    // 0 = hop le (hoac khong dat passkey); 1 = sai / huy; 2 = thieu passkey o che do im lang. Dung boi MSI (cai va go).
    static int CheckPasskey(string fileHash, string pw, string ui)
    {
        if (fileHash == "-") fileHash = "";
        string need = LocalPk(); if (need == "") need = fileHash;
        if (need == "") { MsiLog("khong dat passkey"); return 0; }
        int uil = 0; int.TryParse(ui, out uil);
        if (pw == "" && uil >= 3 && Environment.UserInteractive)
        {
            for (int i = 0; i < 3; i++)
            {
                string v = Prompt("Console System Agent", i == 0 ? "Nhập passkey để tiếp tục:" : "Passkey sai. Nhập lại (" + (3 - i) + " lần còn lại):");
                if (v == null) { MsiLog("nguoi dung huy nhap passkey"); return 1; }
                if (PkOk(need, v)) { MsiLog("passkey dung"); return 0; }
            }
            MsiLog("passkey sai 3 lan"); return 1;
        }
        if (pw == "") { MsiLog("thieu PASSKEY (che do im lang): can them PASSKEY=... vao lenh msiexec"); return 2; }
        if (PkOk(need, pw)) { MsiLog("passkey dung"); return 0; }
        MsiLog("passkey sai"); return 1;
    }

    // ------------------------------------------------------------ go cai dat
    static void RunHidden(string exe, string args, int waitMs)
    {
        try
        {
            ProcessStartInfo psi = new ProcessStartInfo(exe, args); psi.UseShellExecute = false; psi.CreateNoWindow = true;
            using (Process p = Process.Start(psi)) p.WaitForExit(waitMs);
        }
        catch { }
    }

    // Go dich vu, tac vu, khoa rieng, du lieu. KHONG xoa thu muc chuong trinh (MSI hoac lenh goi tu xoa sau khi tien trinh nay thoat).
    static void Teardown()
    {
        string sys = Environment.SystemDirectory;
        RunHidden(Path.Combine(sys, "schtasks.exe"), "/Delete /TN ConsoleSystemUserHelper /F", 15000);
        RunHidden(Path.Combine(sys, "schtasks.exe"), "/Delete /TN ConsoleSystemTray /F", 15000);
        try { using (ServiceController sc = new ServiceController("ConsoleSystemAgent")) { if (sc.Status != ServiceControllerStatus.Stopped) { sc.Stop(); sc.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(25)); } } } catch { }
        int me = Process.GetCurrentProcess().Id;
        foreach (Process p in Process.GetProcessesByName("cs-agent")) { try { if (p.Id != me) { p.Kill(); p.WaitForExit(5000); } } catch { } }
        RunHidden(Path.Combine(sys, "sc.exe"), "delete ConsoleSystemAgent", 15000);
        try
        {
            string pfx = Path.Combine(Data, "client.pfx"); Dictionary<string, object> cf = LoadJson(Path.Combine(Data, "config.json"));
            if (File.Exists(pfx) && cf != null)
            {
                X509Certificate2 c = new X509Certificate2(File.ReadAllBytes(pfx), S(cf, "pfx_pass"), X509KeyStorageFlags.MachineKeySet);
                RSACryptoServiceProvider k = c.PrivateKey as RSACryptoServiceProvider;
                if (k != null) { k.PersistKeyInCsp = false; k.Clear(); }
            }
        }
        catch { }
        for (int i = 0; i < 5; i++) { try { if (Directory.Exists(Data)) Directory.Delete(Data, true); break; } catch { Thread.Sleep(1000); } }
        MsiLog("da go agent (teardown)");
    }

    static bool MsiInstalled()
    {
        foreach (string k in new string[] { "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\", "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\" })
        { using (RegistryKey r = Registry.LocalMachine.OpenSubKey(k + ProductCode)) { if (r != null) return true; } }
        return false;
    }

    // uninstall.bat -> cs-agent.exe --uninstall: yeu cau Administrator + passkey, roi go.
    static int DoUninstall(string progDir)
    {
        Application.EnableVisualStyles();
        if (!new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator))
        { MessageBox.Show("Cần chạy bằng quyền Administrator (chuột phải uninstall.bat, Run as administrator).", "Console System Agent", MessageBoxButtons.OK, MessageBoxIcon.Warning); return 1; }
        string me = Process.GetCurrentProcess().MainModule.FileName;
        if (Path.GetFileName(me).Equals("cs-agent.exe", StringComparison.OrdinalIgnoreCase))
        {   // chay ban sao trong Temp: de MSI/lenh go xoa duoc cs-agent.exe va hop thoai ket qua van con sau khi go
            string tmp = Path.Combine(Path.GetTempPath(), "cs-uninstall-" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".exe");
            File.Copy(me, tmp, true);
            ProcessStartInfo ps = new ProcessStartInfo(tmp, "--uninstall \"" + Path.GetDirectoryName(me) + "\""); ps.UseShellExecute = false;
            Process.Start(ps);
            return 0;
        }
        string pk = LocalPk(), pw = "";
        if (pk != "")
        {
            bool ok = false;
            for (int i = 0; i < 3 && !ok; i++)
            {
                string v = Prompt("Gỡ Console System Agent", i == 0 ? "Nhập passkey để gỡ agent:" : "Passkey sai. Nhập lại (" + (3 - i) + " lần còn lại):");
                if (v == null) return 1;
                if (PkOk(pk, v)) { ok = true; pw = v; }
            }
            if (!ok) { MessageBox.Show("Passkey sai. Không gỡ.", "Console System Agent", MessageBoxButtons.OK, MessageBoxIcon.Error); return 1; }
        }
        else if (MessageBox.Show("Gỡ Console System Agent khỏi máy này?", "Console System Agent", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return 1;
        string prog = progDir;
        if (MsiInstalled())
        {
            ProcessStartInfo psi = new ProcessStartInfo(Path.Combine(Environment.SystemDirectory, "msiexec.exe"), "/x " + ProductCode + " /qn /norestart PASSKEY=\"" + pw.Replace("\"", "") + "\"");
            psi.UseShellExecute = false; psi.CreateNoWindow = true;
            int code = 1; using (Process p = Process.Start(psi)) { p.WaitForExit(180000); code = p.ExitCode; }
            if (code != 0 && code != 3010) { MessageBox.Show("Không gỡ được (msiexec mã " + code + "). Xem C:\\Windows\\Temp\\cs-agent-msi.log", "Console System Agent", MessageBoxButtons.OK, MessageBoxIcon.Error); return 1; }
        }
        else
        {
            Teardown();
            Process.Start(new ProcessStartInfo(Path.Combine(Environment.SystemDirectory, "cmd.exe"), "/c ping -n 4 127.0.0.1 >nul & rmdir /s /q \"" + prog + "\"") { UseShellExecute = false, CreateNoWindow = true });
        }
        try { Process.Start(new ProcessStartInfo(Path.Combine(Environment.SystemDirectory, "cmd.exe"), "/c ping -n 6 127.0.0.1 >nul & del /f /q \"" + me + "\"") { UseShellExecute = false, CreateNoWindow = true }); } catch { }
        MessageBox.Show("Đã gỡ Console System Agent.", "Console System Agent", MessageBoxButtons.OK, MessageBoxIcon.Information);
        return 0;
    }

    // ------------------------------------------------------------ bieu tuong khay he thong (chay trong phien nguoi dung: cs-agent.exe --tray)
    static Icon MakeIcon(Color c)
    {
        using (Bitmap b = new Bitmap(32, 32))
        {
            using (Graphics g = Graphics.FromImage(b))
            {
                g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias; g.Clear(Color.Transparent);
                using (Brush br = new SolidBrush(c)) g.FillEllipse(br, 1, 1, 30, 30);
                using (Font f = new Font("Segoe UI", 18, FontStyle.Bold, GraphicsUnit.Pixel))
                { StringFormat sf = new StringFormat(); sf.Alignment = StringAlignment.Center; sf.LineAlignment = StringAlignment.Center; g.DrawString("C", f, Brushes.White, new RectangleF(0, 1, 32, 32), sf); }
            }
            return (Icon)Icon.FromHandle(b.GetHicon()).Clone();
        }
    }

    static Dictionary<string, object> ReadStatus()
    {
        try
        {
            string f = Path.Combine(PubDir, "status.json");
            if (!File.Exists(f) || (DateTime.UtcNow - File.GetLastWriteTimeUtc(f)).TotalSeconds > 45) return null;
            return (Dictionary<string, object>)Js.DeserializeObject(File.ReadAllText(f, Encoding.UTF8));
        }
        catch { return null; }
    }

    static string StatusText(Dictionary<string, object> st)
    {
        if (st == null) return "Dịch vụ agent không chạy";
        if (S(st, "ket_noi") == "True")
        {
            long t; long.TryParse(S(st, "luc_ok"), out t);
            return "Đã kết nối server (nhịp " + new DateTime(1970, 1, 1).AddSeconds(t).ToLocalTime().ToString("HH:mm:ss") + ")";
        }
        return "Mất kết nối server" + (S(st, "loi") != "" ? ": " + S(st, "loi") : "");
    }

    static Form DiagForm;
    static void ShowDiag()
    {
        if (DiagForm != null && !DiagForm.IsDisposed) { DiagForm.Activate(); return; }
        Form f = new Form(); DiagForm = f;
        f.Text = "Console System Agent - chẩn đoán kết nối"; f.Width = 1040; f.Height = 560; f.StartPosition = FormStartPosition.CenterScreen;
        Label tt = new Label(); tt.Dock = DockStyle.Top; tt.Height = 34; tt.Padding = new Padding(8, 8, 0, 0); tt.Font = new Font("Segoe UI", 10, FontStyle.Bold); tt.Text = "Đang kiểm tra...";
        ListView lv = new ListView(); lv.Dock = DockStyle.Fill; lv.View = View.Details; lv.FullRowSelect = true; lv.GridLines = true; lv.Font = new Font("Segoe UI", 9);
        lv.Columns.Add("Kết quả", 80); lv.Columns.Add("Mục kiểm tra", 440); lv.Columns.Add("Chi tiết", 500); lv.ShowItemToolTips = true;
        Panel pn = new Panel(); pn.Dock = DockStyle.Bottom; pn.Height = 44;
        Button qb = new Button(); qb.Text = "Quét lại"; qb.Left = 8; qb.Top = 8; qb.Width = 110;
        Button cb = new Button(); cb.Text = "Chép kết quả"; cb.Left = 128; cb.Top = 8; cb.Width = 120;
        pn.Controls.Add(qb); pn.Controls.Add(cb);
        f.Controls.Add(lv); f.Controls.Add(pn); f.Controls.Add(tt);
        long[] req = new long[] { 0 };
        System.Windows.Forms.Timer t = new System.Windows.Forms.Timer(); t.Interval = 800;
        Action chay = delegate()
        {
            try { req[0] = Now() - 1; File.WriteAllText(Path.Combine(NdDir, "diag.flag"), "1"); tt.Text = "Đang kiểm tra..."; tt.ForeColor = SystemColors.ControlText; qb.Enabled = false; lv.Items.Clear(); t.Start(); }
            catch (Exception ex) { tt.Text = "Không gửi được yêu cầu: " + ex.Message; }
        };
        t.Tick += delegate
        {
            try
            {
                string fp = Path.Combine(PubDir, "diag.json"); if (!File.Exists(fp)) return;
                Dictionary<string, object> d = (Dictionary<string, object>)Js.DeserializeObject(File.ReadAllText(fp, Encoding.UTF8));
                long bd; long.TryParse(S(d, "luc_bd"), out bd); if (bd < req[0]) return;
                lv.BeginUpdate(); lv.Items.Clear(); int loi = 0, cbao = 0;
                foreach (object o in L(d["muc"]))
                {
                    Dictionary<string, object> m = (Dictionary<string, object>)o; string k = S(m, "tt");
                    ListViewItem li = new ListViewItem(k == "ok" ? "Đạt" : (k == "canhbao" ? "Cảnh báo" : "Lỗi")); li.SubItems.Add(S(m, "ten")); li.SubItems.Add(S(m, "gc"));
                    li.ForeColor = k == "ok" ? Color.FromArgb(20, 130, 60) : (k == "canhbao" ? Color.FromArgb(190, 110, 0) : Color.FromArgb(200, 30, 30));
                    if (k == "loi") loi++; else if (k == "canhbao") cbao++;
                    lv.Items.Add(li);
                }
                lv.EndUpdate();
                if (S(d, "dang") == "False") { t.Stop(); qb.Enabled = true; tt.Text = loi > 0 ? "Có " + loi + " lỗi cần xử lý" : (cbao > 0 ? "Hoạt động, có " + cbao + " cảnh báo" : "Mọi mục đều đạt"); tt.ForeColor = loi > 0 ? Color.FromArgb(200, 30, 30) : Color.FromArgb(20, 130, 60); }
                else tt.Text = "Đang kiểm tra... (" + lv.Items.Count + " mục xong)";
            }
            catch { }
        };
        qb.Click += delegate { chay(); };
        cb.Click += delegate
        {
            StringBuilder sb = new StringBuilder(); sb.AppendLine("Console System Agent " + VER + " - " + Environment.MachineName + " - " + DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss"));
            foreach (ListViewItem li in lv.Items) sb.AppendLine("[" + li.Text + "] " + li.SubItems[1].Text + ": " + li.SubItems[2].Text);
            try { Clipboard.SetText(sb.ToString()); tt.Text = "Đã chép kết quả vào clipboard."; } catch { }
        };
        f.FormClosed += delegate { t.Stop(); t.Dispose(); };
        f.Show(); f.Activate(); chay();
    }

    static Form LogForm;
    static void ShowLog()
    {
        if (LogForm != null && !LogForm.IsDisposed) { LogForm.Activate(); return; }
        Form f = new Form(); LogForm = f;
        f.Text = "Console System Agent - nhật ký"; f.Width = 920; f.Height = 560; f.StartPosition = FormStartPosition.CenterScreen;
        TextBox tb = new TextBox(); tb.Multiline = true; tb.ReadOnly = true; tb.Dock = DockStyle.Fill; tb.ScrollBars = ScrollBars.Both; tb.WordWrap = false;
        tb.Font = new Font("Consolas", 9); tb.BackColor = Color.White;
        f.Controls.Add(tb);
        string[] last = new string[] { null };
        System.Windows.Forms.Timer t = new System.Windows.Forms.Timer(); t.Interval = 1500;
        t.Tick += delegate(object o, EventArgs e)
        {
            try
            {
                string x = File.ReadAllText(Path.Combine(PubDir, "log.txt"), Encoding.UTF8);
                if (x != last[0]) { last[0] = x; tb.Text = x; tb.SelectionStart = tb.TextLength; tb.ScrollToCaret(); }
            }
            catch { }
        };
        t.Start(); f.FormClosed += delegate { t.Stop(); t.Dispose(); };
        f.Show(); f.Activate();
    }

    // Windows 11 mac dinh dua bieu tuong moi vao muc an (mui ten ^): dat IsPromoted de hien thang tren thanh tac vu (khong co thi bo qua).
    static void PromoteIcon()
    {
        try
        {
            using (RegistryKey k = Registry.CurrentUser.OpenSubKey("Control Panel\\NotifyIconSettings", true))
            {
                if (k == null) return;
                foreach (string n in k.GetSubKeyNames())
                    using (RegistryKey s = k.OpenSubKey(n, true))
                    {
                        string p = s.GetValue("ExecutablePath") as string;
                        if (p != null && p.EndsWith("cs-agent.exe", StringComparison.OrdinalIgnoreCase) && !object.Equals(s.GetValue("IsPromoted"), 1)) s.SetValue("IsPromoted", 1, RegistryValueKind.DWord);
                    }
            }
        }
        catch { }
    }

    static void RunTray()
    {
        bool moi; Mutex mx = new Mutex(true, "Local\\ConsoleSystemTray", out moi);
        if (!moi) return;
        Application.EnableVisualStyles();
        NotifyIcon ni = new NotifyIcon(); ni.Text = "Console System Agent"; ni.Visible = true;
        Icon xanh = MakeIcon(Color.FromArgb(34, 160, 90)), cam = MakeIcon(Color.FromArgb(230, 140, 30));
        ni.Icon = cam;
        ContextMenuStrip m = new ContextMenuStrip();
        ToolStripMenuItem h = new ToolStripMenuItem("Console System Agent " + VER); h.Enabled = false;
        ToolStripMenuItem st = new ToolStripMenuItem("Đang kiểm tra..."); st.Enabled = false;
        ToolStripMenuItem lg = new ToolStripMenuItem("Xem log");
        ToolStripMenuItem sy = new ToolStripMenuItem("Đồng bộ ngay (lấy policy và phần mềm từ server)");
        ToolStripMenuItem cd = new ToolStripMenuItem("Chẩn đoán kết nối...");
        m.Items.Add(h); m.Items.Add(st); m.Items.Add(new ToolStripSeparator()); m.Items.Add(lg); m.Items.Add(cd); m.Items.Add(sy);
        ni.ContextMenuStrip = m;
        lg.Click += delegate { ShowLog(); };
        cd.Click += delegate { ShowDiag(); };
        System.Windows.Forms.Timer kq = new System.Windows.Forms.Timer(); kq.Interval = 6000;
        kq.Tick += delegate
        {
            kq.Stop(); Dictionary<string, object> s2 = ReadStatus();
            ni.ShowBalloonTip(4000, "Console System Agent", s2 != null && S(s2, "ket_noi") == "True" ? "Đồng bộ xong. " + StatusText(s2) : StatusText(s2), s2 != null && S(s2, "ket_noi") == "True" ? ToolTipIcon.Info : ToolTipIcon.Warning);
        };
        sy.Click += delegate
        {
            try
            {
                File.WriteAllText(Path.Combine(NdDir, "sync.flag"), "1");
                ni.ShowBalloonTip(2500, "Console System Agent", "Đã gửi yêu cầu đồng bộ tới server...", ToolTipIcon.Info);
                kq.Stop(); kq.Start();
            }
            catch (Exception ex) { ni.ShowBalloonTip(4000, "Console System Agent", "Không gửi được yêu cầu: " + ex.Message, ToolTipIcon.Error); }
        };
        System.Windows.Forms.Timer tm = new System.Windows.Forms.Timer(); tm.Interval = 3000;
        int dem = 0;
        tm.Tick += delegate
        {
            if (dem++ < 3) PromoteIcon();
            Dictionary<string, object> s2 = ReadStatus(); string tx = StatusText(s2);
            st.Text = tx; string tip = "Console System Agent - " + tx; ni.Text = tip.Length > 63 ? tip.Substring(0, 63) : tip;
            ni.Icon = s2 != null && S(s2, "ket_noi") == "True" ? xanh : cam;
        };
        tm.Start(); tm.Interval = 3000;
        Application.Run();
        ni.Visible = false; GC.KeepAlive(mx);
    }

    // ------------------------------------------------------------ tu cap nhat
    static void SelfUpdate(Dictionary<string, object> up)
    {
        try
        {
            string cs = S(up, "cs"), ban = S(up, "ban");
            string dir = Path.Combine(Data, "tmp"); string src = Path.Combine(dir, "agent.new.cs"); string exe = Path.Combine(dir, "cs-agent.new.exe");
            File.WriteAllText(src, cs, new UTF8Encoding(true));
            string csc = Path.Combine(Environment.GetEnvironmentVariable("windir"), (Environment.Is64BitOperatingSystem ? "Microsoft.NET\\Framework64" : "Microsoft.NET\\Framework") + "\\v4.0.30319\\csc.exe");
            ProcessStartInfo psi = new ProcessStartInfo(csc, "/nologo /target:winexe /codepage:65001 /optimize+ /out:\"" + exe + "\" /r:System.ServiceProcess.dll /r:System.Web.Extensions.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll \"" + src + "\"");
            psi.UseShellExecute = false; psi.CreateNoWindow = true; psi.RedirectStandardOutput = true;
            string kq; using (Process p = Process.Start(psi)) { kq = p.StandardOutput.ReadToEnd(); p.WaitForExit(120000); if (p.ExitCode != 0) { Log("bien dich ban moi that bai: " + kq); Thread.Sleep(60000); return; } }
            string cur = Process.GetCurrentProcess().MainModule.FileName;
            string ps1 = Path.Combine(dir, "update.ps1");
            File.WriteAllText(ps1, "Start-Sleep 2; Stop-Service ConsoleSystemAgent -Force; Get-Process cs-agent -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep 2; Copy-Item -LiteralPath '" + exe + "' -Destination '" + cur + "' -Force; Remove-Item -LiteralPath '" + exe + "','" + src + "' -Force -ErrorAction SilentlyContinue; Start-Service ConsoleSystemAgent; Start-ScheduledTask -TaskName ConsoleSystemTray -ErrorAction SilentlyContinue\r\n", new UTF8Encoding(true));
            Log("cap nhat len " + ban);
            Process.Start(new ProcessStartInfo(PsExe, "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"" + ps1 + "\"") { UseShellExecute = false, CreateNoWindow = true });
            Thread.Sleep(120000);
        }
        catch (Exception e) { Log("cap nhat loi: " + e.Message); Thread.Sleep(60000); }
    }
}
