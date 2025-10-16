import os
import shutil
from pathlib import Path

def create_innosetup_script():
    """创建 Inno Setup 安装脚本 - 修复版本"""
    script_content = """[Setup]
AppName=M3U8批量视频分割工具
AppVersion=2.0.0
AppPublisher=Your Company
AppPublisherURL=https://your-website.com
AppSupportURL=https://your-website.com/support
AppUpdatesURL=https://your-website.com/updates
DefaultDirName={autopf}\\M3U8批量视频分割工具
DefaultGroupName=M3U8批量视频分割工具
UninstallDisplayIcon={app}\\M3U8批量视频分割工具.exe
OutputDir=安装程序输出
OutputBaseFilename=M3U8批量视频分割工具_安装程序
Compression=lzma
SolidCompression=yes
SetupIconFile=resources\\icon.ico
LicenseFile=LICENSE.txt
; 安装程序语言
ShowLanguageDialog=no
; 权限要求
PrivilegesRequired=admin
; 安装程序界面
WizardStyle=modern
; 安装完成后选项
CloseApplications=no
RestartApplications=no
; 创建卸载信息
Uninstallable=yes
CreateUninstallRegKey=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.01

[Types]
Name: "full"; Description: "完全安装"
Name: "compact"; Description: "紧凑安装"
Name: "custom"; Description: "自定义安装"; Flags: iscustom

[Components]
Name: "main"; Description: "主程序文件"; Types: full compact custom; Flags: fixed
Name: "shortcuts"; Description: "创建快捷方式"; Types: full

[Files]
Source: "dist\\M3U8批量视频分割工具\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs; Components: main
; 确保ffmpeg.exe有执行权限
Source: "dist\\M3U8批量视频分割工具\\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: main

[Icons]
Name: "{group}\\M3U8批量视频分割工具"; Filename: "{app}\\M3U8批量视频分割工具.exe"; Comment: "将视频文件转换为M3U8格式"; Components: shortcuts
Name: "{group}\\{cm:UninstallProgram,M3U8批量视频分割工具}"; Filename: "{uninstallexe}"; Components: shortcuts
Name: "{autodesktop}\\M3U8批量视频分割工具"; Filename: "{app}\\M3U8批量视频分割工具.exe"; Tasks: desktopicon; Comment: "将视频文件转换为M3U8格式"; Components: shortcuts
Name: "{userappdata}\\Microsoft\\Internet Explorer\\Quick Launch\\M3U8批量视频分割工具"; Filename: "{app}\\M3U8批量视频分割工具.exe"; Tasks: quicklaunchicon; Comment: "将视频文件转换为M3U8格式"; Components: shortcuts

[Run]
Filename: "{app}\\M3U8批量视频分割工具.exe"; Description: "{cm:LaunchProgram,M3U8批量视频分割工具}"; Flags: nowait postinstall skipifsilent; Components: main

[InstallDelete]
Type: filesandordirs; Name: "{app}\\_internal\\*"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\\_internal\\*"
Type: files; Name: "{app}\\ffmpeg.exe"

[Code]
// 检查程序是否正在运行的函数
function IsAppRunning(const FileName: string): Boolean;
var
  FSWbemLocator: Variant;
  FWMIService: Variant;
  FWbemObjectSet: Variant;
begin
  Result := False;
  try
    FSWbemLocator := CreateOleObject('WBEMScripting.SWBEMLocator');
    FWMIService := FSWbemLocator.ConnectServer('', 'root\\CIMV2', '', '');
    FWbemObjectSet := FWMIService.ExecQuery(Format('SELECT Name FROM Win32_Process WHERE Name="%s"', [FileName]));
    Result := (FWbemObjectSet.Count > 0);
  except
    // 如果WMI查询失败，使用简单的进程检查
    Result := FileExists(ExpandConstant('{app}\\') + FileName);
  end;
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // 检查是否已安装
  if RegKeyExists(HKLM, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\M3U8批量视频分割工具_is1') then
  begin
    if MsgBox('检测到已安装的版本。建议先卸载旧版本再继续安装。' #13#13 '是否继续安装？', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
  
  // 检查程序是否正在运行
  if IsAppRunning('M3U8批量视频分割工具.exe') then
  begin
    if MsgBox('检测到 M3U8批量视频分割工具 正在运行。' #13#13 '建议关闭程序后再继续安装。是否继续？', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
  
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  // 检查程序是否正在运行
  if IsAppRunning('M3U8批量视频分割工具.exe') then
  begin
    MsgBox('请先关闭正在运行的 M3U8批量视频分割工具，然后再继续卸载。', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 安装完成后可以执行一些操作
    Log('安装完成，程序已就绪');
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // 卸载完成后清理
    Log('卸载完成');
  end;
end;
"""
    
    # 创建简单的许可文件
    license_content = """M3U8批量视频分割工具 最终用户许可协议

1. 许可授予
本程序授予您使用本软件的许可，但您必须遵守本协议中的条款。

2. 使用限制
您不得对本软件进行反向工程、反编译或反汇编。

3. 免责声明
本软件按"原样"提供，不提供任何明示或暗示的担保。

4. 技术支持
如需技术支持，请联系：support@your-company.com

点击"我同意"继续安装。
"""
    
    with open('LICENSE.txt', 'w', encoding='utf-8') as f:
        f.write(license_content)
    
    with open('setup_script.iss', 'w', encoding='utf-8') as f:
        f.write(script_content)
    print("✅ Inno Setup 脚本已创建: setup_script.iss")

def create_simplified_script():
    """创建简化版本的安装脚本（无复杂代码）"""
    simple_script = """[Setup]
AppName=M3U8批量视频分割工具
AppVersion=2.0.0
AppPublisher=Your Company
DefaultDirName={autopf}\\M3U8批量视频分割工具
DefaultGroupName=M3U8批量视频分割工具
UninstallDisplayIcon={app}\\M3U8批量视频分割工具.exe
OutputDir=安装程序输出
OutputBaseFilename=M3U8批量视频分割工具_安装程序_简化版
Compression=lzma
SolidCompression=yes
SetupIconFile=resources\\icon.ico
PrivilegesRequired=admin
WizardStyle=modern

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式:"

[Files]
Source: "dist\\M3U8批量视频分割工具\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\\M3U8批量视频分割工具"; Filename: "{app}\\M3U8批量视频分割工具.exe"
Name: "{group}\\卸载M3U8批量视频分割工具"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\M3U8批量视频分割工具"; Filename: "{app}\\M3U8批量视频分割工具.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\\M3U8批量视频分割工具.exe"; Description: "启动M3U8批量视频分割工具"; Flags: nowait postinstall skipifsilent
"""
    
    with open('setup_simple.iss', 'w', encoding='utf-8') as f:
        f.write(simple_script)
    print("✅ 简化版安装脚本已创建: setup_simple.iss")

def create_basic_script():
    """创建基础版本安装脚本（最简）"""
    basic_script = """[Setup]
AppName=M3U8批量视频分割工具
AppVersion=2.0.0
AppPublisher=Your Company
DefaultDirName={autopf}\\M3U8批量视频分割工具
DefaultGroupName=M3U8批量视频分割工具
OutputDir=安装程序输出
OutputBaseFilename=M3U8批量视频分割工具_安装程序_基础版
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Files]
Source: "dist\\M3U8批量视频分割工具\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\\M3U8批量视频分割工具"; Filename: "{app}\\M3U8批量视频分割工具.exe"
Name: "{autodesktop}\\M3U8批量视频分割工具"; Filename: "{app}\\M3U8批量视频分割工具.exe"

[Run]
Filename: "{app}\\M3U8批量视频分割工具.exe"; Description: "启动程序"; Flags: nowait postinstall skipifsilent
"""
    
    with open('setup_basic.iss', 'w', encoding='utf-8') as f:
        f.write(basic_script)
    print("✅ 基础版安装脚本已创建: setup_basic.iss")

def main():
    print("🔧 创建修复版安装程序...")
    
    # 检查PyInstaller输出是否存在
    if not Path('dist/M3U8批量视频分割工具/M3U8批量视频分割工具.exe').exists():
        print("❌ 请先运行 build_script.py 打包程序")
        return
    
    # 创建输出目录
    os.makedirs('安装程序输出', exist_ok=True)
    
    # 创建多个版本的安装脚本
    create_innosetup_script()      # 完整版（修复了CheckForMutex问题）
    create_simplified_script()     # 简化版
    create_basic_script()          # 基础版
    
    print("\n📋 安装程序脚本创建完成！")
    print("🎯 推荐使用以下脚本：")
    print("   1. setup_simple.iss - 简化版（推荐，功能完整）")
    print("   2. setup_basic.iss - 基础版（最简，无错误）")
    print("   3. setup_script.iss - 完整版（包含高级功能）")
    print("\n💡 使用步骤：")
    print("   1. 安装 Inno Setup: https://jrsoftware.org/isdl.php")
    print("   2. 用 Inno Setup 打开 setup_simple.iss（推荐）")
    print("   3. 点击 Build → Compile")
    print("   4. 安装程序将输出到: 安装程序输出/")
    print("\n🔧 默认安装路径: C:\\Program Files\\M3U8批量视频分割工具")

if __name__ == "__main__":
    main()