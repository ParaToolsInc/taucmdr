#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

/* Makes a known number of POSIX I/O calls: 10 open, 5 write, 5 read, 10 close. */
int main(int argc, char *argv[])
{
    char buf[16] = "hello io\n";
    for (int i = 0; i < 5; ++i) {
        int fd = open("io-test.txt", O_CREAT | O_WRONLY | O_TRUNC, 0644);
        if (fd < 0 || write(fd, buf, 9) != 9 || close(fd) != 0) {
            perror("write io-test.txt");
            return 1;
        }
        fd = open("io-test.txt", O_RDONLY);
        if (fd < 0 || read(fd, buf, sizeof buf) != 9 || close(fd) != 0) {
            perror("read io-test.txt");
            return 1;
        }
    }
    printf("Done\n");
    return 0;
}
