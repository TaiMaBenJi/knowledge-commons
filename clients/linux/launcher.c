/* CloudStudy Linux 启动器（便携文件夹版）
 * 职责：打开与本可执行文件同目录的 study.html —— 内容完整版随包分发
 * （study.html + study-data/ + learn/ 与启动器放在同一目录）。
 * 构建：zig cc -target x86_64-linux-musl -O2 -s -o CloudStudy launcher.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <limits.h>

int main(void) {
    char exe[PATH_MAX];
    ssize_t n = readlink("/proc/self/exe", exe, sizeof(exe) - 1);
    if (n <= 0) {
        fprintf(stderr, "无法定位自身路径\n");
        return 1;
    }
    exe[n] = 0;
    char *slash = strrchr(exe, '/');
    if (!slash) return 1;
    *(slash + 1) = 0;

    char page[PATH_MAX + 16];
    snprintf(page, sizeof(page), "%sstudy.html", exe);

    if (access(page, R_OK) != 0) {
        fprintf(stderr,
            "未找到 %s\n请解压完整压缩包后再运行——启动器需与 study.html、study-data、learn 在同一目录。\n",
            page);
        return 2;
    }

    pid_t pid = fork();
    if (pid == 0) {
        execlp("xdg-open", "xdg-open", page, (char *)NULL);
        _exit(127); /* 没有 xdg-open */
    }
    if (pid < 0) {
        fprintf(stderr, "无法调用浏览器，请手动打开上述文件。\n");
        return 4;
    }
    return 0;
}
