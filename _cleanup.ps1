Set-Location "C:\Users\Lin\ViewCrop_New"

# 测试/调试脚本
$toDelete = @(
    "main_debug.py","main_fixed.py","check_env.py","debug_minimal.py",
    "diagnostic_test.py","fix_drop.py","minimal_test.py","quick_test.py",
    "test_app.py","test_console.py","test_core.py","test_drop.py",
    "test_gui.py","test_launch.py","test_packed_exe.py","test_params.py",
    "test_updated_ui.py","viewcrop_lite.py","run.py",
    "测试启动.py","诊断.py",
    # 临时输出
    "diag_result.txt","test_output.txt","诊断报告.txt","`$null",
    # 多余spec
    "ViewCrop_final.spec","ViewCrop_optimized.spec","ViewCrop_test.spec","ViewCrop.spec",
    # 多余bat
    "一键修复打包.bat","使用修复版本.bat","修复插件.bat","启动ViewCrop.bat",
    "启动程序.bat","完整诊断.bat","快速启动.bat","快速诊断.bat",
    "性能诊断.bat","手动测试.bat","打包 exe.bat","打包并测试极简版.bat",
    "执行分级测试.bat","诊断启动.bat","运行诊断.bat",
    # 临时md文档
    "BUGFIX_2024-03-16.md","BUILD_GUIDE.md","PYEXPAT_FIX.md","PROJECT_SUMMARY.md",
    "README 打包问题.md","TROUBLESHOOTING.md","UPDATE_SUMMARY.md",
    "完整测试方案.md","当前状态总结.md","快速开始.md","打包完成总结.md",
    "打包问题最终总结.md","突破性解决方案.md","问题解决路线图.md",
    # 备份UI
    "ui\main_window_backup.py","ui\main_window_v2.py"
)

$deleted = 0
foreach ($f in $toDelete) {
    if (Test-Path $f) {
        Remove-Item $f -Force
        Write-Host "DEL: $f"
        $deleted++
    }
}

# 删除build目录
if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
    Write-Host "DEL DIR: build/"
}

Write-Host "===== Cleanup done. Deleted $deleted files. ====="
