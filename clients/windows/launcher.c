/* CloudStudy Windows 启动器（便携文件夹版）
 * 职责：打开与本 EXE 同目录的 study.html —— 内容完整版随包分发
 * （study.html + study-data/ + learn/ 与 EXE 放在同一目录）。
 * 构建：zig cc -target x86_64-windows-gnu -O2 -s -Wl,--subsystem,windows -o CloudStudy.exe launcher.c -lshell32 -luser32
 */
#include <windows.h>

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR lpCmd, int nShow) {
    (void)hInst; (void)hPrev; (void)lpCmd; (void)nShow;

    wchar_t exe[MAX_PATH];
    DWORD n = GetModuleFileNameW(NULL, exe, MAX_PATH);
    if (n == 0 || n >= MAX_PATH) return 1;
    wchar_t *slash = wcsrchr(exe, L'\\');
    if (!slash) return 1;
    *(slash + 1) = 0;                      /* exe 所在目录 */

    wchar_t page[MAX_PATH];
    if (lstrlenW(exe) + 11 >= MAX_PATH) return 1;
    lstrcpyW(page, exe);
    lstrcatW(page, L"study.html");

    if (GetFileAttributesW(page) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(NULL,
            L"未找到学习中心文件 study.html。\n"
            L"请解压完整压缩包后再运行——EXE 需与 study.html、study-data、learn 在同一目录。",
            L"云计算学习 CloudStudy", MB_ICONERROR);
        return 2;
    }

    HINSTANCE rc = ShellExecuteW(NULL, L"open", page, NULL, NULL, SW_SHOWNORMAL);
    if ((INT_PTR)rc <= 32) {
        MessageBoxW(NULL, page,
            L"未能自动打开浏览器，请手动打开上述路径的文件\nPlease open the file above manually.",
            MB_ICONINFORMATION);
        return 4;
    }
    return 0;
}
