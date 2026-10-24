<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="6B1F2C9E-4D7A-4E58-9C31-0A5D8E7F4B21" Name="Console System Agent" Language="1033" Codepage="1252" Version="1.0.0" Manufacturer="Console System" UpgradeCode="C0D5E5A1-7B3F-4A6E-8D12-5F9A3C4E7B68">
    <Package Id="*" Description="Console System Agent" Manufacturer="Console System" InstallerVersion="200" Compressed="yes" InstallScope="perMachine" />
    <Media Id="1" Cabinet="cs.cab" EmbedCab="yes" />
    <Property Id="SERVER" Value="__SERVER__" />
    <Property Id="PIN" Value="__PIN__" />
    <Property Id="CODE" Value="__CODE__" />
    <Property Id="PKH" Value="__PKH__" />
    <Property Id="ARPSYSTEMCOMPONENT" Value="1" />
    <Property Id="MsiHiddenProperties" Value="PASSKEY" />
        <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="INSTALLDIR" Name="ConsoleSystem">
          <Component Id="CsAgentExe" Guid="2F7A1B90-3C4D-4E5F-8A6B-7C8D9E0F1A2B" Win64="yes">
            <File Id="CsAgentExeFile" Name="cs-agent.exe" Source="cs-agent.exe" KeyPath="yes" />
          </Component>
          <Component Id="CsUninstallBat" Guid="4B9C3D12-5E6F-4071-8C8D-9EAFB0213C4D" Win64="yes">
            <File Id="CsUninstallBatFile" Name="uninstall.bat" Source="uninstall.bat" KeyPath="yes" />
          </Component>
          <Component Id="CsInstallPs1" Guid="3A8B2C01-4D5E-4F60-9B7C-8D9EAF102B3C" Win64="yes">
            <File Id="CsInstallPs1File" Name="cs-install.ps1" Source="cs-install.ps1" KeyPath="yes" />
          </Component>
        </Directory>
      </Directory>
    </Directory>
    <Feature Id="Main" Title="Console System Agent" Level="1">
      <ComponentRef Id="CsAgentExe" />
      <ComponentRef Id="CsInstallPs1" />
      <ComponentRef Id="CsUninstallBat" />
    </Feature>
    <CustomAction Id="CsDatPs" Property="CSPSEXE" Value="[System64Folder]WindowsPowerShell\v1.0\powershell.exe" />
    <CustomAction Id="CsGhiDanh" Property="CSPSEXE" Execute="immediate" Return="check" ExeCommand="-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File &quot;[INSTALLDIR]cs-install.ps1&quot; -Server &quot;[SERVER]&quot; -Pin &quot;[PIN]&quot; -Code &quot;[CODE]&quot;" />
    <CustomAction Id="CsCheckPk" FileKey="CsAgentExeFile" Execute="deferred" Return="check" ExeCommand="--check-passkey &quot;[PKH]&quot; &quot;[PASSKEY]&quot; [UILevel]" />
    <CustomAction Id="CsCheckPkRm" FileKey="CsAgentExeFile" Execute="deferred" Return="check" ExeCommand="--check-local &quot;[PASSKEY]&quot; [UILevel]" />
    <CustomAction Id="CsGoAgent" FileKey="CsAgentExeFile" Execute="deferred" Return="ignore" ExeCommand="--teardown" />
    <InstallExecuteSequence>
      <Custom Action="CsDatPs" Sequence="1001">NOT REMOVE</Custom>
      <Custom Action="CsCheckPkRm" Sequence="3401">REMOVE="ALL"</Custom>
      <Custom Action="CsGoAgent" Sequence="3402">REMOVE="ALL"</Custom>
      <Custom Action="CsCheckPk" Sequence="4001">NOT Installed</Custom>
      <Custom Action="CsGhiDanh" Sequence="6601">NOT REMOVE AND CODE AND PIN AND SERVER</Custom>
    </InstallExecuteSequence>
  </Product>
</Wix>
