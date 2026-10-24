# Console Pi - go app kem san (pha specialize, SYSTEM). Tu sinh, khong sua tay.
$ds = @('Microsoft.BingNews','Microsoft.BingWeather','Microsoft.GetHelp')
$log = 'C:\Windows\Setup\Scripts\go-app.log'
foreach ($p in (Get-AppxProvisionedPackage -Online)) {
    if ($ds -contains $p.DisplayName) {
        try {
            Remove-AppxProvisionedPackage -Online -AllUsers -PackageName $p.PackageName -ErrorAction Stop | Out-Null
            Add-Content $log "da go: $($p.DisplayName)"
        } catch { Add-Content $log "LOI go $($p.DisplayName): $($_.Exception.Message)" }
    }
}
